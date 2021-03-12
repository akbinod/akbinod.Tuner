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
import itertools as it
import time

from enum import Enum, auto, Flag

class Tag(Enum):
    '''
    These are keycodes (on macOS at any rate)
    '''
    interesting = 109 # F10
    debug = 101 # F9

class SaveStyle(Flag):
    '''
    Change the Tuner.save_style static if the current scheme does not work for you.
    '''
    all = auto()
    tagged = auto()
    newfile = auto()
    overwrite = auto()

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

    # Change these if you have specific
    # samples you like to work with
    img_sample_color = "./tuner_sample_color.png"
    img_sample_bw = "./tuner_sample_bw.jpg"

    output_dir = "."
    # why bother looking at uninteresting stuff, and let's preserve old runs
    save_style = SaveStyle.tagged or SaveStyle.newfile

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
        def range(self):
            # if the user wants to see a certain min, why default to 0
            # range will not return the 'max' value
            ret = range(self.min, self.max + 1)
            return ret

        def set_value(self,val, headless_op=False):
            '''
            This callback for OpenCV cannot be modified. It's not particularly
            necessary to override this either. You must override get_value
            '''
            # Just put away whatever value you get.
            # We'll interpret (e.g. nulls) when get_value is accessed.
            self._value = val
            if not headless_op:
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
    class CarouselContext:
        def __init__(self, tuner, files, headless):
            '''
            tuner: set to self
            files: what the cat dragged in
            headless: what the cat says

            Usage:
            Context Manager and Generator: manages the current carousel.
            generator of image files, result tracker, updater of the tuner GUI's
            WindowCaption.
            '''
            if isinstance(files,str): val = [files]
            if not (files is None or isinstance(files,list)):
                # don't accept anything else
                # we probably got a single image
                raise ValueError("Carousel can only be set to a single file name, or a list of file names.")

            self.tuner = tuner
            self.files = files
            self.headless = headless
            self.file_count = 0 if files is None else len(files)

            self.results = {}
            # placeholders
            self.results["headless"] = headless
            self.results["duration"] = ""
            # probably only makes sense in the context of a grid search
            self.results["iterations"] = 0

            self.t1 = time.time()
            self.proc_time1 = time.process_time()


        def __enter__(self):
            # weird way of doing it, but OK
            return self
        def __exit__(self, *args):

            # figure duration
            proc_time2 = time.process_time()
            t2 = time.gmtime(time.time() - self.t1)
            outp = f"{time.strftime('%H:%M:%S', t2 )}"
            if t2.tm_sec <= 1 or (proc_time2 - self.proc_time1) < 1:
                outp += f"\t[process_time: {round(proc_time2 - self.proc_time1,5)}]"
            self.results["duration"] = outp

            try:
                self.tuner.save_results(self.results)
            except:
                pass

            return

        @property
        def iterations(self):
            return self.results["iterations"]

        @iterations.setter
        def iterations(self,val):
            self.results["iterations"] = val
            return

        def capture_result(self, force=False):
            stash = True

            this_result = self.tuner.results
            if not force and self.tuner.save_tagged_only:
                if (not "tags" in this_result or len(this_result["tags"]) == 0):
                    # must have the tags object and one that is not empty
                    stash = False


            # make a hive for this result
            if stash:
                if not self.title in self.results:
                    res = self.results[self.title] = []
                else:
                    res = self.results[self.title]

                # we're getting a copy from tuner
                # - no need to make another
                res.append(this_result)

            return

        def __iter__(self):
            '''
            Generator. Iterate over the user supplied carousel.
            '''
            self.title = None
            img = None

            if self.files is None:
                # We want one iteration when there's nothing
                # - so yield this once. This is prob coming
                # from the decorator impl
                # No image title - let the tuner default
                # to what it will
                self.tuner.image_title = None
                self.title = "no_image"
                yield img
            else:
                for index, fname in enumerate(self.files):
                    img = cv2.imread(fname)
                    if img is None: raise ValueError(f"Tuner could not find file {fname}. Check full path to file.")
                    self.title = os.path.split(fname)[1]
                    # Stash the last result before we change the image,
                    if index > 0: self.capture_result()
                    self.tuner.image_title = (self.title,index+1,self.file_count)
                    yield img

            # done iterating the images, capture the last result
            self.capture_result()
            return

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
        self.wip_dir = "." if (Tuner.output_dir is None or Tuner.output_dir == "") else os.path.realpath(Tuner.output_dir)
        self.save_tagged_only = True if (Tuner.save_style and SaveStyle.tagged) else False
        self.overwrite_file = True if (Tuner.save_style and SaveStyle.overwrite) else False

        # provided later
        # self.__carousel_files = None
        self.__unprocessed_image = None
        self.__args = {}
        self.__params = {}
        self.__invocation_errors = {}
        self.__results = {}

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

        # optional secondary function which is passed
        # the tuned parameters and the image from primary tuning
        self.__cb_downstream = downstream_func
        self.__downstream_window_name = self.get_func_name(downstream_func)

        self.__image_downstream = None
        self.__thumbnail_downstream = None
        if not downstream_func is None:
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
                    res = cb(tuner=self)
                    self.__set_result(res,overwrite=False)
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
    def __show(self, img, cc:CarouselContext, delay=0, headless=False):
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
                cc.capture_result(True)
                # self.save_results()
                # don't exit just yet - clock starts over
                continue
            elif k in [101, 109]:
                self.tag_result(k)
                continue
            else:
                # any other key - done with this image
                # cancel the stack if the Esc key was pressed
                cancel = (k==27)
                break
        return not cancel
    def tag_result(self, obs:Tag):
        key = Tag(obs).name
        if not self.__results is None:
            if not "tags" in self.__results: self.__results["tags"] = {}
            self.__results["tags"][key] = True
        return
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
    def grid_search(self, carousel, headless=False,delay=2_000, esc_cancels_carousel = False):
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
        with Tuner.CarouselContext(self, carousel, headless) as car:
            iterations = 0
            # the ranges that our trackbars have
            ranges, keys = self.get_ranges()
            # ready to iterate
            for img in car:
                # Bang on this image.
                user_cancelled = False
                # Prod iterates over the complete set of values
                #  that this constellation of trackbars could have.
                # It needs to be rebuilt for each file, as
                # an iteration will exhaust it.
                prod = it.product(*ranges)
                for t in prod:
                    # Update the trackbar values.
                    self.set_values_headless(t, keys)
                    # Invoke target
                    iterations += 1
                    user_cancelled = not self.__show(img,headless=headless,delay=delay,cc=car)
                    # stash results if headless, otherwise the user will do that with F3
                    if headless: car.capture_result()
                    if user_cancelled : break #out of this image
                # done with the last image
                if user_cancelled and esc_cancels_carousel: break
            # record how many iterations before you exit the context
            car.iterations = iterations

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
        with Tuner.CarouselContext(self, carousel, False) as car:
            for img in car:
                ret  = self.__show(img,delay=delay,cc=car)
                if not ret: break

        return ret

    def begin(self, carousel):
        '''
        Display the Tuner window.
        fnames: See readme. can be None, a single file name, or a list of file names.
                When a list, each image is processed until interruped via the keyboard.
                Hit Esc to cancel the whole stack.
        '''
        with Tuner.CarouselContext(self, carousel, False) as car:
            for img in car:
                ret  = self.__show(img,delay=0,cc=car)
                if not ret:
                    break

        return ret

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
    # @property
    # def __carousel(self):
    #     # generator
    #     title = None
    #     img = None
    #     index = total = 0
    #     if self.__carousel_files is None:
    #         # we want one iteration when there's nothing
    #         # - so yield this once
    #         yield img, title, 0, 0
    #     else:
    #         total = len(self.__carousel_files)
    #         for index, fname in enumerate(self.__carousel_files):
    #             img = cv2.imread(fname)
    #             if img is None: raise ValueError(f"Tuner could not find file {fname}. Check full path to file.")
    #             title = os.path.split(fname)[1]
    #             yield img, title, (index+1), total

    #     return

    # @__carousel.setter
    # def __carousel(self,val):

    #     if isinstance(val,str): val = [val]

    #     if val is None or isinstance(val,list):
    #         # this is cool
    #         pass
    #     else:
    #         # don't accept anything else
    #         # we probably got a single image
    #         raise ValueError("Carousel can only be set to a single file name, or a list of file names.")

    #     self.__carousel_files = val
    #     return

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
        # j["image_title"] = self.__img_title
        j["errors"] = copy.deepcopy(self.errors)
        return j

    @results.setter
    def results(self, val):
        self.__set_result(val)

    def __set_result(self, res, overwrite=True):

        if self.__calling_main:
            if overwrite or (not "main" in self.__results):
                # let's track the args associate with these results as well
                self.__results["args"] = self.args
                self.__results["main"] = res
                self.__results["tags"] = {}
        else:
            # the object setting this is the downstream func
            if overwrite or (not "downstream" in self.__results):
                self.__results["downstream"] = res


        if not self.results is None and self.results == {}:
            # The function returns but the user has
            # not set results - do the honors
            self.results = results

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
        it = self.image_title
        # check if window currently has an image
        if it == prefix: it = None
        prefix = prefix + "." + it if not (it is None or it == "") else prefix
        if not self.overwrite_file:
            # get a unique file name
            prefix += "."
            # we're just going to leave this file lying around
            _, full_path_name = tempfile.mkstemp(
                                # makes it easy to find
                                prefix=prefix
                                ,suffix=suffix
                                ,dir=self.wip_dir
                                ,text=True
                                )
        else:
            # we can overwrite the func_name.image_name file
            full_path_name = os.path.join(self.wip_dir, prefix + suffix)
            full_path_name = os.path.realpath(full_path_name)
        return full_path_name

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


