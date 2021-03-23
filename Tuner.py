import numpy as np
import cv2

from TunerConfig import TunerConfig
from TuningContext import TuningContext
from Args import Args
from constants import *

class Tuner:
    def __init__(self, func_main, *
                , func_downstream = None
                ):
        '''
        Tuning interface for users.
        Please see the readme for detail.
        func_main:  Required. The main target of tuning.
        func_downstream: Optional. Similar to func, this is a downstream function to be called after func.
        '''

        # set up config
        self.config = TunerConfig()
        # args handler
        self._args = Args(self)
        # tuning engine
        self.ctx = TuningContext(self,self.config,func_main,func_downstream)

        # various UI elements
        self.show_window()

        return

    def show_window(self):
        '''
        User facing UI specific.
        This is about as good as it gets for a non Qt UI. Trackbars
        get added later when userland code adds params.
        '''
        # build the menuing system
        function_keys ={118:"F4", 96: "F5", 98:"F7", 100: "F8", 101:"F9", 109:"F10"}
        key_map = "F1: grid srch F2:save img F3:save args | Tag & Save ["
        for k in self.config.tag_codes:
            fk = function_keys[k]
            name = Tags(k).name
            key_map += fk + ":" + name + " "
        key_map += "]"

        # cv2.WINDOW_NORMAL|
        # build the window
        cv2.namedWindow(self.ctx.func_name,cv2.WINDOW_KEEPRATIO|cv2.WINDOW_GUI_EXPANDED)
        # show the menu
        cv2.displayOverlay(self.ctx.func_name, key_map,delayms=0)

        # no stinking menus or trackbars on this one.
        if not self.ctx.func_name_down is None:
            # we have 2 pictures to show
            cv2.namedWindow(self.ctx.func_name_down,cv2.WINDOW_KEEPRATIO|cv2.WINDOW_GUI_EXPANDED)

        return

    def __del__(self):
        cv2.destroyWindow(self.ctx.func_name)
        if not self.__cb_downstream is None:
            cv2.destroyWindow(self.ctx.func_name_down)
        pass

    def __contains__(self, key):
        # if there's an arg for it,
        # there's a property on this class
        return key in self._args

    def track(self, name, max, min=None, default=None):
        '''
        Add an int parameter to be tuned.
        Please see the readme for details.
        '''

        return self._args.track(name, max, min, default)

    def track_boolean(self, name, default=False):
        '''
        Add a boolean parameter to be tuned.
        Please see the readme for details.
        '''
        return self._args.track_boolean(name,default)

    def track_list(self, name, data_list, *, default_item=None, display_list=None, return_index=True):
        '''
        Add a list of values to be tuned.Please see the readme for details.
        data_list: A list of values.
        default_item: Initial pick.
        display_list: An item corresponding to the selected index is used for display in Tuner.
        return_index: When True, the selection index is returned, otherwise the selected item in data_list is returned.
        '''

        return self._args.track_list(name,data_list,default_item,display_list,return_index)

    def track_dict(self, name, dict_like, *, default_item_key=None, return_key=True):
        '''
        Add a list of values to be tuned. Dict keys are displayed as selected values.
        dict_like: Typically a dict or a json object.
        default_item: Initial pick.
        return_key: When True, the selected key is returned, otherwise, its object.
        '''

        return self._args.track_dict(name,dict_like,default_item_key,return_key)

    def on_status_changed(self, val):
        try:
            cv2.displayStatusBar(self.ctx.func_name,val,10_000)
        except:
            pass

    def on_show_main(self, img):
        if not self.headless:
            cv2.imshow(self.ctx.func_name, img)
        return

    def on_show_downstream(self,img):
        if not self.headless:
            cv2.imshow(self.ctx.func_name_down, img)
        return

    def on_show_results(self, res):
        if not self.headless:
            # TBD
            pass
        return

    def on_await_user(self):
        '''
        Show results and wait for user input for next action. This is
        a GUI callback expected by the TuningContext
        delay:      in ms - 0 means  - *indefinite*

        '''
        # can only "show" in the context of some carousel
        if self.ctx is None: return True
        cancel = False

        while(not self.headless):
            # Wait forever (when delay == 0) for a keypress
            # This is skipped when in headless mode.
            k = cv2.waitKey(self.delay) #& 0xFF
            # need to figure out how to reset cc
            # before opening this back up
            # if k == 122:
            #     # F1 pressed
            #     self.grid_search(None)
            #     continue
            if k == 120:
                # F2 pressed = save image
                self.ctx.save_image()
                # don't exit just yet - clock starts over
                continue
            elif k == 99:
                # F3 - force this invocation data to be saved
                self.ctx.force_save()
                # don't exit just yet - clock starts over
                continue
            elif k in self.config.tag_codes:
                # tag the current result - stays in here
                self.ctx.tag(k)
                continue
            else:
                # any other key - done with this image
                # cancel the stack if the Esc key was pressed
                cancel = (k==27)
                break
        return not cancel

    def on_context_changed(self, carousel):
        self.carousel = carousel
        title = carousel.title + f" [{carousel.index} of {carousel.file_count}]"
        cv2.setWindowTitle(self.ctx.func_name,title)
        if not self.ctx.func_name_down is None:
            cv2.setWindowTitle(self.ctx.func_name_down, "Downstream: " + title )

        return

    def on_controls_changed(self):
        # pass this on to ctx for an invoke
        self.ctx.invoke()

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
        self.headless = headless
        self.delay = delay
        return self.ctx.grid_search(carousel,headless,esc_cancels_carousel)

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
        # TODO: turn off the UI controls
        self.headless = False
        self.delay = delay
        ret = self.ctx.review(carousel)

        return ret

    def begin(self, carousel):
        '''
        Display the Tuner window.
        fnames: See readme. can be None, a single file name, or a list of file names.
                When a list, each image is processed until interruped via the keyboard.
                Hit Esc to cancel the whole stack.
        '''
        self.headless = False
        self.delay = 0
        ret = self.ctx.begin(carousel)
        # should we just leave this hanging around? Or unload?

        return ret


    @property
    def args(self):
        return self._args.args
    @property
    def arg_mgr(self):
        return self._args

    @property
    def context_files(self):
        '''
        When your code works with multiple files, e.g., in Motion Detection, you will
        need to specify sets of images that go together. You do this by constructing
        a list, each item of which is a tuple of n file names. Each slot in the
        carousel makes the files in the tuple available through this property.
        '''
        return self.carousel.context_files

    @property
    def results(self):
        '''
        Returns results json which includes the results set by main, as well as by downstream.
        '''

        return self.ctx.results

    @results.setter
    def results(self, val):
        '''
        Called from userland code to save various results
        '''
        self.ctx.set_result(val)

    @property
    def image(self):
        '''
        Always return a fresh copy of the user supplied image.
        '''
        return self.ctx.image

    @image.setter
    def image(self, val):
        self.ctx.image = val

    @property
    def thumbnail(self):
        return self.ctx.thumbnail
    @thumbnail.setter
    def thumbnail(self, val):
        self.ctx.thumbnail = val

    @property
    def window(self):
        return self.ctx.func_name

    @staticmethod
    def get_sample_image_color():
        return cv2.imread(TunerConfig.img_sample_color)

    @staticmethod
    def get_sample_image_bw():
        return cv2.imread(TunerConfig.img_sample_bw)

    @staticmethod
    def from_call(args, kwargs):
        return TuningContext.from_call(args, kwargs)

    @staticmethod
    def from_call(call_is_method, args, kwargs, params, cb):
        '''
        This is called from the middle of an intercepted call to create
        a tuner, and configure its args.
        args:   args to the function
        kwargs: ditto
        params: just the positional parameters to the function
        cb    : the main function to tune
        '''

        if len(args) == 0 : return
        tuner = Tuner(cb)
        # See if there's anything we can tune
        # If our target is a bound method, we
        # want to ignore that 'self' - it's
        # going to get bound anyway. When the
        # self is passed in, there's a diff between
        # the params we've identified, and the args
        # passed in.
        a_off = 1 if call_is_method else 0
        for i in range(a_off, len(args)):
            # formal positional parameter name
            name = params[i - a_off]
            # arg passed in to the call that kicks off tuning
            arg = args[i]

            this_max = this_min = this_default = None
            ty = type(arg)
            if ty == int:
                # vanilla arg has to be an int
                this_max = arg
                tuner.track(name, max=this_max)
            elif ty == tuple:
                # also a vanilla arg, but we got a tuple
                # describing max, min, default
                this_max = arg[0]
                if len(arg) == 2: this_min = arg[1]
                if len(arg) == 3: this_default = arg[2]
                tuner.track(name, max=this_max,min=this_min,default=this_default)
            elif ty == bool:
                # its a boolean arg
                tuner.track_boolean(name,default=arg)
            elif ty == list:
                # track from a list
                # nothing fancy here like display_list etc
                tuner.track_list(name,arg,return_index=False)
            elif ty == dict:
                # track from a dict/json
                tuner.track_dict(name,arg, return_key=False)
            else:
                # Something we cannot tune, so curry it.
                # Shunt it over to the kwargs for target.
                # Don't both trying to bind 'self' or tuner
                if name not in ['tuner','self']: kwargs[name] = arg

        # done defining what to track

        return tuner





