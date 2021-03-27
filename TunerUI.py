from Carousel import Carousel
import numpy as np
import cv2

from TunerConfig import TunerConfig
from Tuner import Tuner
from Params import Params
from Carousel import *
from constants import *

class TunerUI:
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
        # args handler - only deals with the main func
        self._parms = Params(self, func_main)
        # tuning engine
        self.ctx = Tuner(self,self.config,self._parms, func_main,func_downstream)

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
        return key in self._parms

    def track(self, name, max, min=None, default=None):
        '''
        Add an int parameter to be tuned.
        Please see the readme for details.
        '''

        return self._parms.track(name, max, min, default)

    def track_boolean(self, name, default=False):
        '''
        Add a boolean parameter to be tuned.
        Please see the readme for details.
        '''
        return self._parms.track_boolean(name,default)

    def track_list(self, name, data_list, *, default_item=None, display_list=None, return_index=True):
        '''
        Add a list of values to be tuned.Please see the readme for details.
        data_list: A list of values.
        default_item: Initial pick.
        display_list: An item corresponding to the selected index is used for display in Tuner.
        return_index: When True, the selection index is returned, otherwise the selected item in data_list is returned.
        '''

        return self._parms.track_list(name,data_list,default_item,display_list,return_index)

    def track_dict(self, name, dict_like, *, default_item_key=None, return_key=True):
        '''
        Add a list of values to be tuned. Dict keys are displayed as selected values.
        dict_like: Typically a dict or a json object.
        default_item: Initial pick.
        return_key: When True, the selected key is returned, otherwise, its object.
        '''

        return self._parms.track_dict(name,dict_like,default_item_key,return_key)

    def on_status_changed(self, val):
        try:
            cv2.displayStatusBar(self.ctx.func_name,val,30_000)
        except:
            pass

    def on_show_main(self, img):
        if not self.headless and img is not None:
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

    def on_context_changed(self, new_frame):
        self.frame = new_frame
        title = new_frame.title + f" [{new_frame.index} of {new_frame.tray_length}]"
        cv2.setWindowTitle(self.ctx.func_name,title)
        if not self.ctx.func_name_down is None:
            cv2.setWindowTitle(self.ctx.func_name_down, "Downstream: " + title )

        return

    def on_controls_changed(self, key, val):
        # special Ui processing goes here

        # invoke() the tuner
        self.ctx.invoke()
        return

    def grid_search(self, carousel=None, headless=False,delay=500, esc_cancels_carousel = False):
        '''
        Conducts a grid search across the trackbar configuration, and saves
        aggregated results to file. When not in headless mode, you can
        save images and results for individual files as they are displayed.
        carousel:   A fully initialize Carousel, use the carousel_from_() helper functions to gin one up.
        headless:   When doing large searches, set this to True to suppress the display.
        delay   :   When not in headless mode, acts like begin()
        esc_cancels_carousel: When you submit a carousel, does the 'Esc' key get you:
                            -- out of tuning the current image only (False), or
                            -- out of the entire carousel as well (True)
        '''
        self.headless = headless
        self.delay = delay
        # here in support of TunedFunction
        if carousel is None: carousel = self.null_carousel()
        if not type(carousel) is Carousel: raise ValueError("carousel: Either pass none, or use the carousel_ helper functions to gin one up.")
        return self.ctx.grid_search(carousel,headless,esc_cancels_carousel)

    def begin(self, carousel=None, delay=0):
        '''
        Display the Tuner window.
        carousel: A fully initialize Carousel, use the carousel_from_() helper functions to gin one up. See readme for more information.
        delay:    Milliseconds to show each image in the carousel until interrupted by the keyboard. 0 for indefinite.
        '''
        self.headless = False
        self.delay = delay
        # here in support of TunedFunction
        if carousel is None: carousel = self.null_carousel()
        if not  type(carousel) is Carousel: raise ValueError("carousel: Either pass none, or use the carousel_ helper functions to gin one up.")
        ret = self.ctx.begin(carousel)
        # should we just leave this hanging around? Or unload?

        return ret

    def build_from_call(self, call_is_method:bool, call_args, call_kwargs):
        '''
        This is meant for use by the TunedFunction decorator - not
        for direct use by userland code.
        This is called from the middle of an intercepted call to create
        a tuner, and configure its args.
        cb      : the main function to tune (tuning target)
        is_method: whether this is a class method or not
        args    : should contain the args from your invocation
        kwargs  : ditto
        '''
        return self._parms.build_from_call(call_is_method, call_args, call_kwargs)

        return


    def null_carousel(self):
        # here just to support TunedFunction
        c = Carousel(self.ctx,None,None)
        return c
    def carousel_from_images(self, params:list, images:list, im_read_flag=None, normalize=False):
        '''
        Builds a carousel from the supplied parameters.
        params: A list of names of parameters to the tuned function.
        images: A list of tuples. Each tuple has exactly as many file names as len(params). Cannot be any other type.
        im_read_flag: One of the IMREAD_ flags from openCV. Match this to your test cases.
        normalize: Whether to normalize the image on read. Match this to your test cases.
        '''
        return Carousel.from_images(self.ctx, params,images,im_read_flag,normalize)
    def carousel_from_video(self, params:list, video, gs:FrameGenStyle):
        '''
        Builds a carousel from the supplied parameters.
        params: A list of names of parameters to the tuned function.
        video: Full path to video file.
        gs: Governs how many images are yielded, how they are pre-processed etc.
        '''

        return Carousel.from_video(self.ctx, params,video,gs)

    def inspect(self, image:np.ndarray = None, comment:str = None, state:dict=None, delay=40):
        '''
        Meant to be called to show interim results,
        e.g., while your particle filter is SLOWLLLLLY converging.
        Returns whatever the waitkey() call returns
        image: will be shown in the UI
        comment: in the status bar
        state: perhaps in the next version, we'll show this
        delay: how long to wait for a keyboard interrupt in ms
        '''
        ret = None
        self.on_status_changed(comment)
        self.on_show_main(image)
        # what to do with state?

        if not delay is None: ret = cv2.waitKey(delay)

        return ret

    @property
    def args(self):
        return self._parms.theta

    @property
    def files(self):
        '''
        When your code works with multiple files, e.g., in Motion Detection, you will
        need to specify sets of images that go together. You do this by constructing
        a list, each item of which is a tuple of n file names. Each frame in the
        carousel makes the files in the tuple available through this property.
        '''
        return self.frame.files

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







