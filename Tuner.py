from PropertyBag import PropertyBag
import numpy as np
import cv2
import copy
import os
import sys


import inspect
import functools
import itertools as it
import matplotlib.pyplot as plt

from CarouselContext import CarouselContext
from tb import tb, tb_boolean, tb_dict, tb_list, tb_prop
from constants import *

class Tuner:
    # statics
    HIGHLIGHT_COLOR = (173,255,47)
    HIGHLIGHT_THICKNESS_LIGHT = 1
    HIGHLIGHT_THICKNESS_HEAVY = 2
    PUT_TEXT_FONT = cv2.FONT_HERSHEY_PLAIN
    PUT_TEXT_SMALL = 0.7
    PUT_TEXT_NORMAL = 1.0
    PUT_TEXT_HEAVY = 2.0

    # Change these if you have specific
    # samples you like to work with
    img_sample_color = "./tuner_sample_color.png"
    img_sample_bw = "./tuner_sample_bw.jpg"

    output_dir = "./wip"
    # why bother looking at uninteresting stuff, and let's preserve old runs
    save_style = SaveStyle.tagged | SaveStyle.newfile

    def __init__(self, func, *
                , downstream_func = None
                ):
        '''
        Please see the readme for detail.
        func:           Required. The main target of tuning.
        downstream_func:Optional. Similar to func, this is a downstream function to be called after func.
                        Downstream receives the same instance of Tuner, and displays the downstream
                        (second) image in a downstream window.
        '''
        # set up config
        # sort out where we will save results, defaulting to cwd
        self.wip_dir = "." if (Tuner.output_dir is None or Tuner.output_dir == "") else os.path.realpath(Tuner.output_dir)
        if not os.path.exists(self.wip_dir): self.wip_dir = "."
        self.wip_dir = os.path.realpath(self.wip_dir)

        self.save_all = False if (Tuner.save_style & SaveStyle.tagged == SaveStyle.tagged) else True
        self.overwrite_file = True if (Tuner.save_style & SaveStyle.overwrite == SaveStyle.overwrite) else False
        # used by the carousel context
        self.tag_codes = [i.value for i in Tags]
        self.tag_names = [i.name for i in Tags]
        # tag_names = [i.name for i in Tags]
        function_keys ={118:"F4", 96: "F5", 98:"F7", 100: "F8", 101:"F9", 109:"F10"}
        key_map = "F1: grid srch F2:save img F3:save args | Tag & Save ["
        for k in self.tag_codes:
            fk = function_keys[k]
            name = Tags(k).name
            key_map += fk + ":" + name + " "
        key_map += "]"

        # provided later
        self.__unprocessed_image = None
        self.__args = {}
        self.__params = {}
        self.__results = None
        # Holds path names to images needed by the client
        # who may want to open them in special ways with imread
        self.context_files = []
        # the safe default
        self.__calling_main = True

        # primary function to tune with its attendant image and other params
        self.__cb_main = func
        # base the main window name on the name of the function
        self.__window_name = self.get_func_name(func)

        # result of tuning
        self.__image_main = None
        self.__thumbnail_main = None
        self.__img_title = None

        # cv2.WINDOW_NORMAL|
        # we need this window regardless of there the user wants a picture in it
        cv2.namedWindow(self.window,cv2.WINDOW_KEEPRATIO|cv2.WINDOW_GUI_EXPANDED)
        # button = cv2.createButton(self.window,self.button_clicked, userData="grid_search", buttonType=cv2.QT_PUSH_BUTTON | cv2.QT_NEW_BUTTONBAR)

        self.overlay = key_map

        # optional secondary function which is passed
        # the tuned parameters and the image from primary tuning
        self.__cb_downstream = downstream_func
        self.__downstream_window_name = self.get_func_name(downstream_func)

        self.__image_downstream = None
        self.__thumbnail_downstream = None
        if not downstream_func is None:
            # we have 2 pictures to show
            cv2.namedWindow(self.downstream_window,cv2.WINDOW_KEEPRATIO|cv2.WINDOW_GUI_EXPANDED)

        # updated later when the user provides a carousel
        self.cc = None
        return

    def __del__(self):
        cv2.destroyWindow(self.window)
        if not self.__cb_downstream is None:
            cv2.destroyWindow(self.downstream_window)
        pass
    def button_clicked(self, state, other):
        return

    def __contains__(self, key):
        return key in self.args

    def __add_trackbar(self, name, t):
        self.__params[name] = t
        # create an attribute with the same name as the tracked property
        setattr(Tuner ,name, tb_prop(t.get_value))

        return
    def track(self, name, max, min=None, default=None):
        '''
        Add an int parameter to be tuned.
        Please see the readme for details.
        '''
        t = tb(self,name,min=min,max=max,default=default, cb_on_update=self.__update_arg)
        self.__add_trackbar(name,t)

        return
    def track_boolean(self, name, default=False):
        '''
        Add a boolean parameter to be tuned.
        Please see the readme for details.
        '''
        default = False if default is None else default
        t = tb_boolean(self,name,default=default, cb_on_update=self.__update_arg)
        self.__add_trackbar(name,t)
        return
    def track_list(self, name, data_list, *, default_item=None, display_list=None, return_index=True):
        '''
        Add a list of values to be tuned.Please see the readme for details.
        data_list: A list of values.
        default_item: Initial pick.
        display_list: An item corresponding to the selected index is used for display in Tuner.
        return_index: When True, the selection index is returned, otherwise the selected item in data_list is returned.
        '''

        if not data_list is None:
            t = tb_list(self,name
                            ,data_list=data_list
                            ,display_list = display_list
                            ,default_item=default_item
                            ,cb_on_update=self.__update_arg
                            ,return_index=return_index
                            )
        self.__add_trackbar(name,t)
        return
    def track_dict(self, name, dict_like, *, default_item_key=None, return_key=True):
        '''
        Add a list of values to be tuned. Dict keys are displayed as selected values.
        dict_like: Typically a dict or a json object.
        default_item: Initial pick.
        return_key: When True, the selected key is returned, otherwise, its object.
        '''

        if not dict_like is None:
            t = tb_dict(self,name
                            ,dict_like=dict_like
                            ,default_item_key=default_item_key
                            ,return_key=return_key
                            ,cb_on_update=self.__update_arg
                            )
            self.__add_trackbar(name,t)
        return

    def get_func_name(self, cb):
        # import TunedFunction
        ret = None
        if not cb is None:
            if type(cb) is functools.partial:
                ret = cb.func.__qualname__
                # if type(cb) is TunedFunction:
                #     ret = cb.func_name
                # else:
                #     ret = cb.func.__qualname__
            else:
                ret = cb.__qualname__
        return ret
    @property
    def status():

        return
    @status.setter
    def status(self, val):
        try:
            cv2.displayStatusBar(self.window,val,10_000)
        except:
            pass

    @property
    def overlay():

        return
    @status.setter
    def overlay(self, val):
        try:
            cv2.displayOverlay(self.window, val,delayms=0)
        except:
            # user does not have the Qt backend installed. Pity.
            pass

    def __refresh(self, headless=False):
        # invokes must ultimately come through this chokepoint
        def safe_invoke(cb, name):
            try:
                if not cb is None:
                    # todo - check if the expected args all have
                    # defaults, otherwise things will blow up
                    # quite easily (expected 4, got 1)
                    res = cb(tuner=self)
                    # At this point, the target is done.
                    # Use whatever returns we have captured.
                    self.__set_result(res,is_return=True)
            except Exception as error:
                # do not let downstream errors kill us
                # eventually we'll have an appropriate gui
                # for showing this error
                self.cc.capture_error()
            finally:
                # Let the CC know it should grab those results
                self.cc.capture_result(self.results)

        def invoke_main():
            self.__calling_main = True
            # call the user proc that does the calc/tuning
            safe_invoke(self.__cb_main, self.__window_name)
            # done calculating - show the results
            img = self.main_image
            # grid_searcehs are usually headless
            if not (headless or img is None):
                img = self.__insert_thumbnail(img, self.__thumbnail_main)
                # show the main image here
                cv2.imshow(self.window, img)
            return

        def invoke_downstream():
            #  call the user proc that does the secondary processing/application
            self.__calling_main = False
            safe_invoke(self.__cb_downstream, self.downstream_window)
            img = self.downstream_image
            if not (headless or img is None):
                # show it in the secondary window
                img = self.__insert_thumbnail(self.downstream_image, self.__thumbnail_downstream)
                cv2.imshow(self.downstream_window, img)
            return

        try:
            # set up a new results object
            self.__results = PropertyBag()
            # get an up to date copy of user args
            self.gather_args()

            # now let the context grab what it may
            self.cc.before_invoke()

            # make the invocations
            invoke_main()
            invoke_downstream()
            # show results if you can
            self.__show_results(self.results)

        except:
            pass
        finally:
            # last thing
            self.cc.after_invoke()

        return
    def __show_results(self, res):
        # TBD
        return
    def __show(self, img, delay=0, headless=False):
        '''
        This is the original show - paths from the public show interface like begin() and review() come here.
        img:        the image to work with
        img_title:  window title, file name etc
        delay:      only set in review/grid_search mode; 0 means  - *indefinite*
        headless:   only set in review/grid_search mode - supress display
        '''
        # can only "show" in the context of some carousel
        if self.cc is None: return True
        cancel = False
        # this may be None and that is OK
        self.__unprocessed_image = img
        self.__results = None

        # the first step in the message pump
        self.__refresh(headless=headless)

        while(not headless):
            # Wait forever (when delay == 0) for a keypress
            # This is skipped when in headless mode.
            k = cv2.waitKey(delay) #& 0xFF
            # need to figure out how to reset cc
            # before opening this back up
            # if k == 122:
            #     # F1 pressed
            #     self.grid_search(None)
            #     continue
            if k == 120:
                # F2 pressed = save image
                self.cc.save_image()
                # don't exit just yet - clock starts over
                continue
            elif k == 99:
                # F3 - record current results
                self.cc.capture_result(None, force=True)
                # self.save_results()
                # don't exit just yet - clock starts over
                continue
            elif k in self.tag_codes:
                # tag the current result - stays in here
                self.cc.tag(k)
                continue
            else:
                # any other key - done with this image
                # cancel the stack if the Esc key was pressed
                cancel = (k==27)
                break
        return not cancel

    def get_ranges(self):
        '''
        Returns a list containing the range of each of the trackbars in this tuner.
        And another of the keys with which this list was butilt.
        There is a positional correspondence between the two lists.
        '''
        # Eventually will get to filtering the set of params we actually take
        keys = list(self.__params.keys())
        ranges = [r for r in [self.__params[key].range() for key in keys]]
        return ranges, keys

    def set_values_headless(self, t, keys):
        '''
        t:      tuple or values
        keys:   list of keys to update
        '''
        # Each tuple t is a combination of trackbar values
        # and will have the same length as keys
        for i in range(len(keys)):
            # skip the UI refresh on every property set
            self.__params[keys[i]].set_value(t[i],headless_op=True)

        return

    def grid_search(self, carousel, headless=False,delay=500, esc_cancels_carousel = False):
        '''
        Conducts a grid search across the trackbar configuration, and saves
        aggregated results to file. When not in headless mode, you can
        save images and results for individual files as they are displayed.
        carousel:   Like review(), a list of image file names
        headless:   When doing large searches, set this to True to suppress the display.
        delay   :   When not in headless mode, acts like review()
        esc_cancels_carousel: When you submit a carousel, does the 'Esc' key get you:
                            -- out of tuning the current image only (False), or
                            -- out of the entire carousel as well (True)
        '''
        if carousel is None:
            # use the current context
            cc = self.cc
        else:
            # create a new one
            cc = CarouselContext(self, carousel, headless)
        with cc:
            # the ranges that our trackbars have
            ranges, keys = self.get_ranges()
            # ready to iterate
            for img in cc:
                # Bang on this image.
                user_cancelled = False
                # cart(esian) iterates over the complete set of values
                # that this constellation of trackbars could have.
                # It needs to be rebuilt for each file, as
                # an iteration will exhaust it.
                cart = it.product(*ranges)
                for t in cart:
                    # Update the trackbar values.
                    self.set_values_headless(t, keys)
                    # Invoke target
                    user_cancelled = not self.__show(img,headless=headless,delay=delay)
                    if user_cancelled : break #out of this image
                # done with the last image
                if user_cancelled and esc_cancels_carousel: break

        return

    def review(self, carousel, delay=2_000):
        '''
        Usage: Identical to begin() except in that each image is shown for 'delay' ms unless interrupted.
        Sit back and enjoy the slideshow, saving image/result files
        as you go. Typically used in your regression test.
        1. create a tuner and set defaults to the best of your knowledge
        2. call this to flip through the images from your project
        carousel: one of
                -- None (if you are reading images in the tuning target)
                -- Single single fully qualified file name
                -- A list of fully qualified file names, each of which will be processed
        delay   : miliseconds to hold the display
        '''
        with CarouselContext(self, carousel, False) as cc:
            for img in cc:
                ret  = self.__show(img,delay=delay)
                if not ret: break


        return ret

    def begin(self, carousel):
        '''
        Display the Tuner window.
        fnames: See readme. can be None, a single file name, or a list of file names.
                When a list, each image is processed until interruped via the keyboard.
                Hit Esc to cancel the whole stack.
        '''
        with CarouselContext(self, carousel, False) as cc:
            for img in cc:
                ret  = self.__show(img,delay=0)
                if not ret: break

        return ret

    def stitch_images(self, img_list):
        if len(img_list) == 0: return

        ret = None
        padding = 5
        ret = img_list.pop(0)
        h = ret.shape[0]

        num_colors = 1 if ret.ndim == 2 else 3
        border = np.ones((h, padding, num_colors))

        while len(img_list) > 0:
            this_img = img_list.pop(0)
            sh = this_img.shape
            t = np.zeros(shape=(h,sh[1]))
            t[0:sh[0],0:sh[1]] = this_img
            # add border
            ret = np.hstack((
                            # the last image
                            ret
                            # plus a border
                            , border
                            # plus the current image
                            , t
                            )
                            )

        return ret

    @property
    def image_title(self):
        return self.__img_title

    @image_title.setter
    def image_title(self,val):
        title = index = total = None
        if val is None:
            # go with func name
            val = (self.__window_name,None,None)
        elif type(val) is str:
            val = (val, None, None)

        title = self.__window_name if val[0] is None else val[0]
        if len(val) >= 2: index = val[1]
        if len(val) >= 3: total = val[2]
        # this will be in filenames and such - so don't add the x of y
        self.__img_title = title
        if not (index is None or total is None): title += f" [{index} of {total}]"
        cv2.setWindowTitle(self.window,title)
        if not self.__cb_downstream is None:
            cv2.setWindowTitle(self.downstream_window, "Downstream: " + title )

        return

    def gather_args(self):
        # this looks like a slower way of doing things,
        # especially given the __update_arg just up above;
        # but it actually avoids a whole lot of refresh
        # during trackbar init which can get really
        # expensive out in userland
        # Also, don't use a comprehension to replace - just update
        for key in self.__params:
            self.__args[key] =  self.__params[key].get_value()
        return

    def __update_arg(self, key, val):
        self.__args[key] = val
        self.__refresh()

    @property
    def args(self):
        '''
        A dictionary containing all the tuned args, and their current settings.
        '''
        return copy.deepcopy(self.__args)

    @property
    def main_image(self):
        '''
        The image as updated by the main function - the target of tuning.
        '''
        return self.__image_main

    @property
    def downstream_image(self):
        '''
        The image as updated by the downstream function.
        '''

        return self.__image_downstream

    @property
    def results(self):
        '''
        Returns results json which includes the results set by main, as well as by downstream.
        '''

        return self.__results

    @results.setter
    def results(self, val):
        '''
        Called from userland code to save various results
        '''
        self.__set_result(val,is_return=False)

    def __set_result(self, res, *, is_return:bool=False):
        '''
        Calls from userland to the 'results' property
        are forwarded here. This is also called directly
        by Tuner to save return values with overwrite set to False.
        '''
        def format_result():
            ret = None
            if type(res) is tuple:
                # Results are tupled together
                # convert to array - weed out types
                # incompatible with json.dumps
                ret = []
                for obj in res:
                    if type(obj) is np.ndarray:
                        # not using that
                        pass
                    else:
                        ret.append(obj)
                # ret = {"list":ret}
            elif type(res) is np.ndarray:
                ret = None
            # elif type(res) is dict:
            #     ret = res
            else:
                ret = res
            return ret

        # get a result that we can safely stash
        res = format_result()



        if self.__calling_main:
            if (not "main" in self.__results) or not is_return :
                # either forwarded call from userland, or
                # default result capture and no results saved yet
                # Prevents user results from being overwrittwen
                self.__results.main = res
                if is_return: self.__results.return_capture = True
        else:
            # the object setting this is the downstream func
            if (not "downstream" in self.__results) or not is_return:
                self.__results.downstream = res
                if is_return: self.__results.return_capture = True
    @property
    def image(self):
        '''
        Always return a fresh copy of the user supplied image.
        '''
        return np.copy(self.__unprocessed_image)

    @image.setter
    def image(self, val):
        if self.__calling_main:
            self.__image_main = val
        else:
            # the object setting this is the downstream func
            self.__image_downstream = val

    @property
    def window(self):
        '''
        Window title.
        '''
        return self.__window_name

    @property
    def downstream_window(self):
        '''
        Downstream window title.
        '''
        return self.__downstream_window_name
    @property
    def thumbnail(self):
        '''
        This image is inserted into the upper left hand corner of the main image. Keep it very small.
        '''
        if self.__calling_main:
            return self.__thumbnail_main
        else:
            return self.__thumbnail_downstream

    @thumbnail.setter
    def thumbnail(self,val):
        # this is the current thumbnail
        if self.__calling_main:
            self.__thumbnail_main = val
        else:
            self.__thumbnail_downstream = val
        return

    def __insert_thumbnail(self, mn, tn):
        '''
        mn: main image to insert the thing into
        '''
        # do not use the property - use what has been set
        if not tn is None:
            # Draw a bounding box 1 pixel wide in the top left corner.
            # The box should have enough pixels for all of the image
            bt = 1
            tl = (3,3)
            br = (tl[0] + tn.shape[1] + (2*bt), tl[1] + tn.shape[0] + (2*bt))
            cv2.rectangle(mn,tl,br,Tuner.HIGHLIGHT_COLOR,thickness=bt)
            # adjust for offset border
            tl = (tl[0] + bt, tl[1] + bt)
            x,x1,y,y1 = Tuner.image_to_array_indices(tl,img_shape=tn.shape)

            tn_dim = np.ndim(tn)
            if np.ndim(mn) == 3:
                mn[x:x1,y:y1, 0] = tn if tn_dim == 2 else tn[:,:,0]
                mn[x:x1,y:y1, 1] = tn if tn_dim == 2 else tn[:,:,1]
                mn[x:x1,y:y1, 2] = tn if tn_dim == 2 else tn[:,:,2]
            else:
                mn[x:x1,y:y1] = tn if tn_dim == 2 else cv2.cvtColor(tn,cv2.COLOR_BGR2GRAY)
        return mn

    @staticmethod
    def get_sample_image_color():
        return cv2.imread(Tuner.img_sample_color)

    @staticmethod
    def get_sample_image_bw():
        return cv2.imread(Tuner.img_sample_bw)

    @staticmethod
    def tuner_from_json(name, cb_main, cb_downstream, json_def:dict):
        '''
        Returns an instance of Tuner configured to the json you pass in.
        '''
        tuner = Tuner(name,cb_main=cb_main,cb_downstream=cb_downstream)
        keys = list(json_def.keys())
        for key in keys:
            # each is a new trackbar
            this = json_def[key]
            # what type
            this_type = this["type"] if "type" in this else None
            # starting value
            default = this["default"] if "default" in this else None

            if this_type is None:
                min = this["min"] if "min" in this else None
                max = this["max"] if "max" in this else None
                tuner.track(key, max, min, default)
            elif this_type in ["bool", "boolean"]:
                tuner.track_boolean(key,default)
            elif this_type == "list":
                data_list = display_list = None
                if "data_list" in this: data_list = this["data_list"]
                if "display_list" in this: display_list = this["display_list"]
                tuner.track_list(key,data_list,default,display_list=display_list)
            # elif this_type == "json":
            #     TOO RECURSIVE

        return tuner

    @staticmethod
    def minimal_preprocessor( window_title="Minimal Preprocessor", *, cb_downstream = None, thumbnail=None):
        '''
        Tuning the pre-processing is a common task in CV. Use this method to
        get a minimal (you will need more for your projects) preprocessing
        tuner that meets some goals like blurring, canny edge detection, etc.
        Pass it the downstream function that consumes the tuned parameters
        to meet your project goals; e.g., finding lines, or matching templates.
        Call the begin() method on the returned object, passing it your image.

        You can use this to develop pre-processing presets. Get to a point
        with the trackbars that you like, and then save the results to file
        to review/copy into your code.

        This function could just as easily have made calls to the track_ set of
        trackbar creation functions. It takes the json def approach as an
        illustration. Use this tuner to get your image to a good stage of
        pre-processing, and save the results. Use the results json in your code.
        '''

        def tune(tuner:Tuner):
            res = {}
            img = tuner.image
            # we got nothing to say about preprocessing
            res["preprocessing"] = copy.deepcopy(tuner.args)
            tuner.results = res

            # get the processed image
            tuner.image = Tuner.preprocess_to_spec(img,tuner.args)
            # process the thumbnail if one exists
            if not thumbnail is None:
                tuner.thumbnail = Tuner.preprocess_to_spec(thumbnail,tuner.args)
            return

        json_def={
        "img_mode":{
            "type":"list"
            ,"data_list":["grayscale","blue","green","red"]
            ,"default":"grayscale"
            }
        ,"blur":{
            "type":"boolean"
            ,"default":True
            }
        ,"blur_ksize":{
            "type":"list"
            ,"data_list":[(3,3), (5,5), (7,7)]
            ,"default":0
            }
        ,"blur_sigmaX":{
            "max":20
            ,"min":0
            ,"default":4
            }
        ,"contrast":{
            "type":"boolean"
            ,"default":False
            }
        ,"contrast_kept_val":{
            "max":255
            ,"default":0
            }
        ,"contrast_flip":{
            "type":"boolean"
            ,"default":False
            }
        ,"detect_edge":{
            "type":"boolean"
            ,"default":False
            }
        ,"edge_threshold1":{
            "max":200
            ,"default":150
            }
        ,"edge_threshold2":{
            "max":200
            ,"default":50
            }
        ,"edge_apertureSize":{
            "type":"list"
            ,"data_list":[3,5,7]
            }
        }

        tuner = Tuner.tuner_from_json(name=window_title
                                        ,cb_main= tune
                                        ,cb_downstream=cb_downstream
                                        ,json_def= json_def)


        return tuner

    @staticmethod
    def bin_these(iterable_1d,wt="Bin These"):
        plt.hist(iterable_1d,bins='auto',)
        plt.title(wt +  ":auto binned")
        plt.show()
        hist = bins = mid = None
        try:
            hist, bins = np.histogram(a=iterable_1d)
            # print(hist,bins)
            mid = bins[np.argmax(hist)]
        except:
            # not all data is amenable to this
            pass
        return hist,bins,mid

    @staticmethod
    def image_to_array_indices(img_pt_from, *
                                , img_pt_to = None
                                , img_shape = None):

        # since array x and y are flipped in the image
        y, x = img_pt_from

        if not img_pt_to is None:
            # go point to point
            y1, x1 = img_pt_to
        elif not img_shape is None:
            # this is the shape of the subset image
            y1, x1 = img_shape[0], img_shape[1]
            y1 += y
            x1 += x
        return x, x1, y, y1


