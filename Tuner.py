import numpy as np
import matplotlib.pyplot as plt
import cv2
import copy
import os
import json
import tempfile
import sys
import functools
import inspect

# Change these if you have specific
# samples you like to work with
img_sample_color = "./tuner_sample_color.png"
img_sample_bw = "./tuner_sample_bw.jpg"

class tb_prop:

    def __init__(self, get_val_method):
        self.get_val_method = get_val_method
    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return self.get_val_method()
    def __set__(self, instance, value):
        return

class Tuner:
    # statics
    HIGHLIGHT_COLOR = (173,255,47)
    HIGHLIGHT_THICKNESS_LIGHT = 1
    HIGHLIGHT_THICKNESS_HEAVY = 2
    PUT_TEXT_FONT = cv2.FONT_HERSHEY_PLAIN
    PUT_TEXT_SMALL = 0.7
    PUT_TEXT_NORMAL = 1.0
    PUT_TEXT_HEAVY = 2.0


    class __tb:

        def __init__(self, tuner, name, *, max, min, default, cb_on_update=None) -> None:
            if max is None: raise ValueError("Must have 'max' to define a regular trackbar.")
            self.tuner = tuner
            self.on_update = cb_on_update
            self.name = name
            self.max = max
            self.min = 0 if min is None else (min if min >= 0 else 0)
            self.default = self.min if default is None else (self.min if default <= self.min or default > self.max else default)
            self._value = self.default
            self.trackbar = cv2.createTrackbar(name, tuner.window
                                                ,self.default
                                                ,self.max
                                                ,self.set_value)
            # create an attribute with the same name as the tracked property
            setattr(Tuner,name, tb_prop(self.get_value))
            # do not trigger the event - things are just getting set up
            # the "begin()" and other methods will reach out for the args anyway
            self._value = self.default
            # self.set_value(self.default)
        def spec(self):
            # these must be ints, not floats
            return int(self.max), int(self.default)

        def set_value(self,val):
            '''
            This callback for OpenCV cannot be modified. It's not particularly
            necessary to override this either. You must override get_value
            '''
            # Just put away whatever value you get.
            # We'll interpret (e.g. nulls) when get_value is accessed.
            self._value = val
            # python will delegate to the most derived class
            # the next line will kick off a refresh of the image
            if not self.on_update is None: self.on_update(self.name,self.get_value())
            # show the new parameter for 10 seconds
            self.tuner.status = self.name + ":" + str(self.get_display_value())
            return

        def get_value(self):
            '''
            Must be overridden by derivers.
            Provides a class specific interpretation of trackbar values

            '''
            # guard for None
            ret = self.min if self._value is None else self._value
            # guard for bad input by the user
            ret = self.min if ret < self.min else self._value
            return ret

        def get_display_value(self):
            '''
            Override this if you have a special formatting to apply
            '''
            return self.get_value()

        def ticks(self):
            # generator over the range of values
            for i in range(self.max):
                # tick over and set value to new
                # do this "headless" so that we
                # are not refreshing unnecessarily
                self._value = i
                yield i
            return
    class __tb_boolean(__tb):
        def __init__(self, tuner, name, *, default=False, cb_on_update=None) -> None:
            '''
            Represents True/False values.
            '''
            default=0 if default == False else 1
            super().__init__(tuner, name,min=0,max=1,default=default,cb_on_update=cb_on_update)

        def get_value(self):
            ret = super().get_value()
            ret = False if ret <= 0 else True
            return ret
    class __tb_list(__tb):
        def __init__(self, tuner, name, *, data_list, display_list=None, default_item=None, return_index=True, cb_on_update=None) -> None:
            '''
            Represents a list of values. The trackbar is used to pick the list index
            and the returned value is the corresponding item from the list.
            When display_list is provided, then the corresponding value from it
            is used in Tuner's displays - but not returned anywhere.
            '''
            if data_list is None: raise ValueError("Must have data_list to define a list trackbar.")
            self.__data_list = data_list
            self.__display_list = display_list
            max = min = default = 0
            if not data_list is None:
                max = len(data_list) - 1
                default = 0
                if not default_item is None:
                    if default_item in data_list:
                        # user specified a list item
                        default = data_list.index(default_item)
                    elif isinstance(default_item,int) and default_item < len(data_list):
                        # user specified a list index
                        default = default_item

            if not display_list is None:
                if len(data_list) != len(display_list):
                    raise ValueError("Display list must match data list in length.")

            self.__return_index = return_index
            super().__init__(tuner, name, max=max, min=0, default=default
                            , cb_on_update=cb_on_update)

        def get_value(self):
            ret = super().get_value()
            if not self.__return_index:
                ret = self.__data_list[ret]
            return ret

        def get_display_value(self):

            if self.__display_list is None:
                ret = self.get_value()
            else:
                ret = super().get_value()
                ret = self.__display_list[ret]
            return ret
    class __tb_dict(__tb_list):
        def __init__(self, tuner, name, dict_like, *, default_item_key, return_key=True, cb_on_update) -> None:
            '''
            Like a list tracker. Keys become data items, and associated data become display items.
            When return_key is True: you get the key back
            When return_key is False: you get the object relating to key

            '''
            self.__return_key = return_key
            self.data = dict_like
            try:
                # make a list of the keys
                display_list = list(dict_like.keys())
                # and a list of values
                data_list = [obj for obj in [dict_like[key] for key in dict_like]]
                assert data_list is not None and len(data_list) > 0
            except:
                raise ValueError("Dict like object must be populated and support key iteration.")

            try:
                if default_item_key is None: default_item_key = display_list[0]
                assert  default_item_key in dict_like
            except:
                raise ValueError("Default item not found in dict_like.")

            # given the setup in init, we want the list index back
            super().__init__(tuner, name
                                , data_list=data_list
                                , display_list=display_list
                                , default_item=default_item_key
                                , cb_on_update=cb_on_update
                                , return_index=True)

            return
        def get_value(self):
            key_index = super().get_value()
            key =  list(self.data.keys())[key_index]
            if self.__return_key:
                ret =key
            else:
                ret = self.data[key]
            return ret

    def __init__(self, *
                , cb_main
                , cb_downstream = None
                , output_dir = "."
                , def_window_title = ""
                ):
        '''
        Please see the readme fo more detail.
        name:           Required, Window name, default window title, and prefix for output files
        cb_main:        Required. The main target of tuning.
        cb_downstream:  Optional. Similar to cb_main, this is a downstream function to be called after cb_main.
        This is not tuned, but it can display an image in a second (downstream) window.
        output_dir      Optional. Where Tuner will dump temporary files, results etc.
        '''
        self.wip_dir = "." if (output_dir is None or output_dir == "") else os.path.realpath(output_dir)

        # provided later
        self.__carousel_files = None
        self.__unprocessed_image = None
        self.__args = {}
        self.__params = {}
        self.__invocation_errors = {}
        self.__results = {}

        # the safe default
        self.__calling_main = True

        # primary function to tune with its attendant image and other params
        self.__cb_main = cb_main
        if def_window_title is None or def_window_title == "":
            # base the main window name on the name of the function
            self.__window_name = self.get_func_name(cb_main)
        else:
            self.__window_name = def_window_title

        # result of tuning
        self.__image_main = None
        self.__thumbnail_main = None
        self.__img_title = None

        # cv2.WINDOW_NORMAL|
        # we need this window regardless of there the user wants a picture in it
        cv2.namedWindow(self.window,cv2.WINDOW_KEEPRATIO|cv2.WINDOW_GUI_EXPANDED)

        # optional secondary function which is passed
        # the tuned parameters and the image from primary tuning
        self.__cb_downstream = cb_downstream
        self.__downstream_window_name = self.get_func_name(cb_downstream)

        self.__image_downstream = None
        self.__thumbnail_downstream = None
        if not cb_downstream is None:
            # we have 2 pictures to show
            cv2.namedWindow(self.downstream_window,cv2.WINDOW_KEEPRATIO|cv2.WINDOW_GUI_EXPANDED)

        return

    def __del__(self):
        cv2.destroyWindow(self.window)
        if not self.__cb_downstream is None:
            cv2.destroyWindow(self.downstream_window)
        pass

    def track(self, name, max, min=None, default=None):
        '''
        Add an int parameter to be tuned.
        Please see the readme for details.
        '''
        tb = Tuner.__tb(self,name,min=min,max=max,default=default, cb_on_update=self.__update_arg)
        self.__params[name] = tb
        return
    def track_boolean(self, name, default=False):
        '''
        Add a boolean parameter to be tuned.
        Please see the readme for details.
        '''
        default = False if default is None else default
        tb = Tuner.__tb_boolean(self,name,default=default, cb_on_update=self.__update_arg)
        self.__params[name] = tb
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
            tb = Tuner.__tb_list(self,name
                                    ,data_list=data_list
                                    ,display_list = display_list
                                    ,default_item=default_item
                                    ,cb_on_update=self.__update_arg
                                    ,return_index=return_index
                                    )
            self.__params[name] = tb
        return
    def track_dict(self, name, dict_like, *, default_item_key=None, return_key=True):
        '''
        Add a list of values to be tuned. Dict keys are displayed as selected values.
        dict_like: Typically a dict or a json object.
        default_item: Initial pick.
        return_key: When True, the selected key is returned, otherwise, its object.
        '''

        if not dict_like is None:
            tb = Tuner.__tb_dict(self,name
                                    ,dict_like=dict_like
                                    ,default_item_key=default_item_key
                                    ,return_key=return_key
                                    ,cb_on_update=self.__update_arg
                                    )
            self.__params[name] = tb
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
            cv2.displayStatusBar(self.tuner.window,val,10_000)
        except:
            pass

    @property
    def overlay():

        return
    @status.setter
    def overlay(self, val):
        try:
            cv2.displayOverlay(self.window, val,delayms=1_000)
        except:
            # user does not have the Qt backend installed. Pity.
            pass

    def __refresh(self, headless=False):
        def safe_invoke(cb, name):
            try:
                if not cb is None:
                    # todo - check if the expected args all have safe defaults
                    # otherwise it will blow up quite easily (expected 4, got 1)
                    cb(tuner=self)
            except Exception as error:
                # do not let downstream errors kill us
                # eventually we'll have an appropriate gui
                # for this
                self.status = f"An error occurred executing {name}. Check results."
                self.errors = repr(error)
                print(error)

        def show_main():
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
        def show_downstream():
            #  call the user proc that does the secondary processing/application
            self.__calling_main = False
            safe_invoke(self.__cb_downstream, self.downstream_window)
            img = self.downstream_image
            if not (headless or img is None):
                # show it in the secondary window
                img = self.__insert_thumbnail(self.downstream_image, self.__thumbnail_downstream)
                cv2.imshow(self.downstream_window, img)
            return

        show_main()
        show_downstream()
        self.overlay = self.results

        return
    def __show(self, img, title,delay=0, headless=False, img_index = None, total_images=None):
        '''
        This is the original show - paths from the public show interface like begin() and review() come here.
        img:        the image to work with
        img_title:  window title, file name etc
        delay:      only set in review/grid_search mode; 0 means  - *indefinite*
        headless:   only set in review/grid_search mode - supress display
        '''
        cancel = False
        # this may be None and that is OK
        self.__unprocessed_image = img
        self.__image_title = (title,img_index,total_images)
        self.__invocation_errors = {}
        self.__results = {}

        # the first step in the message pump
        self.__refresh(headless=headless)

        while(not headless):
            # Wait forever (when delay == 0) for a keypress
            # This is skipped when in headless mode.
            k = cv2.waitKey(delay) #& 0xFF
            if k == 120:
                # F2 pressed = save image
                self.save_image()
                # don't exit just yet - clock starts over
                continue
            elif k == 99:
                # F3 - dump params
                self.save_results()
                # don't exit just yet - clock starts over
                continue
            else:
                # any other key - done with this image
                # cancel the stack if the Esc key was pressed
                cancel = (k==27)
                break
        return not cancel

    def grid_search(self, carousel, headless=False,delay=3_000, esc_cancels_carousel = False):
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
        steps = list(self.__params.keys())
        final_step = len(steps) - 1
        img = title = index = total = None
        gs_result = {}
        curr_res_list = None
        # Once this get set to false, the recursive descent unwinds
        # Whether we go on to the next file in the carousel depends
        # on the
        user_cancelled = False

        def creep_trackbar(step_no):
            nonlocal user_cancelled
            # which trackbar/param are we talking about?
            p = self.__params[steps[step_no]]

            for t in p.ticks():
                # get this param to tick over one.
                if user_cancelled:
                    # unwind this recursive descent
                    return
                elif step_no == final_step:
                    # If this is the last param in the set
                    # Call user code with a fresh set of params
                    # Doing this invokes the target, which gathers the args
                    user_cancelled = not self.__show(img, title, headless=headless, delay=delay,img_index=index,total_images=total)
                    # stash results
                    curr_res_list.append(self.results)
                else:
                    # For all non final params - there's just
                    # the ticking over,  no showing.
                    creep_trackbar(step_no=step_no+1)
            return

        self.__carousel = carousel
        for img, title, index, total in self.__carousel:
            # kick off the recursive descent
            curr_res_list = gs_result[title] = []
            creep_trackbar(0)
            if user_cancelled and esc_cancels_carousel: break

        # save consolidated results
        self.save_results(result=gs_result)
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
        self.__carousel = carousel
        img = title = None
        ret = True

        for img, title in self.__carousel:
            ret  = self.__show(img,title,delay)
            if not ret: break

        return ret

    def begin(self, carousel):
        '''
        Display the Tuner window.
        fnames: See readme. can be None, a single file name, or a list of file names.
                When a list, each image is processed until interruped via the keyboard.
                Hit Esc to cancel the whole stack.
        '''

        return self.review(carousel=carousel,delay=0)

    def save_image(self):
        '''
        Saves the current image to a temp file prefixed by {function_image_} in
        the working directory set during initialization.
        '''
        fname = self.get_temp_file(suffix=".main.png")
        cv2.imwrite(fname,self.__image_main)
        if not self.downstream_image is None:
            fname = fname.replace(".main.", ".downstream.")
            cv2.imwrite(fname,self.downstream_image)
        return

    def save_results(self, result=None):
        '''
        Saves the current set of results to a file following name conventions.
        Let result be None to grab the last set, or provide your own.
        '''
        ret = True
        j = self.results if result is None else result
        fname = self.get_temp_file(suffix=".json")
        try:
            with open(fname,"w") as f:
                try:
                    f.write(json.dumps(j))
                except:
                    # could not get a formatted output
                    f.write(str(j))
                f.write("\n")
        except:
            # dont let this screw anything else up
            self.status = "Failed to write results."
            ret = False

        return ret
    @property
    def __carousel(self):
        # generator
        title = None
        img = None
        total = len(self.__carousel_files)
        if self.__carousel_files is None:
            # we want one iteration when there's nothing
            # - so yield this once
            yield img, title, 0, 0
        else:
            for index, fname in enumerate(self.__carousel_files):
                img = cv2.imread(fname)
                if img is None: raise ValueError(f"Tuner could not find file {fname}. Check full path to file.")
                title = os.path.split(fname)[1]
                yield img, title, (index+1), total

        return

    @__carousel.setter
    def __carousel(self,val):

        if isinstance(val,str): val = [val]

        if val is None or isinstance(val,list):
            # this is cool
            pass
        else:
            # don't accept anything else
            # we probably got a single image
            raise ValueError("Carousel can only be set to a single file name, or a list of file names.")

        self.__carousel_files = val
        return

    @property
    def __image_title(self):
        return self.__img_title

    @__image_title.setter
    def __image_title(self,val):
        title = index = total = None
        if not (val is None or val == ""):
            if type(val) is str:
                title = val
            elif type(val) is tuple:
                title = val[0]
                if len(val) >= 2: index = val[1]
                if len(val) >= 3: total = val[2]
            # this will be in filenames and such - so don't add the x of y
            self.__img_title = title
            if not (index is None or total is None): title += f" [{index} of {total}]"
            cv2.setWindowTitle(self.window,title)
            if not self.__cb_downstream is None:
                cv2.setWindowTitle(self.downstream_window, "Downstream: " + title )
        return

    def __update_arg(self, key, val):
        self.__args[key] = val
        self.__refresh()
    @property
    def args(self):
        '''
        A dictionary containing all the tuned args, and their current settings.
        '''
        # this looks like a slower way of doing things,
        # especially given the __update_arg just up above;
        # but it actually avoids a whole lot of refresh
        # during trackbar init which can get really
        # expensive out in userland
        # Also, don't use a comprehension to replace - just update
        for key in self.__params:
            self.__args[key] =  self.__params[key].get_value()

        return self.__args

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
        Returns json which includes the image title, the current state of tuned args, the results set by main, and the results set by downstream.
        '''
        # return the combined results, and add args in there for good measure
        j = copy.deepcopy(self.__results)
        j["image_title"] = self.__img_title
        j["args"] = self.args
        j["errors"] = copy.deepcopy(self.errors)
        return j

    @results.setter
    def results(self, val):

        if self.__calling_main:
            self.__results["main"] = val
        else:
            # the object setting this is the downstream func
            self.__results["downstream"] = val

    @property
    def errors(self):
        '''
        Returns json containing errors in execution.
        '''
        return self.__invocation_errors

    @errors.setter
    def errors(self, val):

        if self.__calling_main:
            self.__invocation_errors["main"] = val
        else:
            # the object setting this is the downstream func
            self.__invocation_errors["downstream"] = val


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

    def get_temp_file(self, suffix=".png"):
        '''
        Creates a temporary file with the specified suffix.
        The temp file is prefixed with the name of the main target,
        and image currently being processed
        '''
        prefix = self.window
        it = self.__image_title
        prefix = prefix + "." + it if not (it is None or it == "") else prefix
        prefix += "."
        _, full_path_name = tempfile.mkstemp(
                                # makes it easy to find
                                prefix=prefix
                                ,suffix=suffix
                                ,dir=self.wip_dir
                                ,text=True
                                )
        # we're just going to leave this file lying around
        return full_path_name

    @staticmethod
    def get_sample_image_color():
        return cv2.imread(img_sample_color)

    @staticmethod
    def get_sample_image_bw():
        return cv2.imread(img_sample_bw)

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


