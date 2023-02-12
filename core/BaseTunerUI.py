
from distutils import core
import string
from typing import List

from core.Carousel import Carousel
import numpy as np
import cv2
import sys

from TunerConfig import TunerConfig
from core.Tuner import Tuner
from core.Params import Params
from core.Carousel import *
from TunerConstants import *

from core.CodeTimer import CodeTimer


class BaseTunerUI:
    def __init__(self, func_main
                , pinned_params = None
                , parms_json = None
                ):
        '''
        Tuning interface for users.
        Please see the readme for detail.
        Args:
        func_main:  Required. The main target of tuning.
        func_downstream: Optional. Similar to func, this is a downstream function to be called after func.
        pinned_params: Params that tuner should pass in to the tuned function as is, without creating controls to manipulate them.
        parms_json: json to define the parameters you're tuning
        '''
        # Initialize some safe defaults here
        self.ctx = None
        self.headless = False
        self.in_grid_search = False

        # set up config
        self.config = TunerConfig()
        # args handler - only deals with the main func
        self._parms = Params(self, func_main, pinned_params, parms_json)
        # tuning engine
        self.ctx = Tuner(self,self.config,self._parms, func_main)

        # various UI elements
        self.build()

        return

    def build(self):
        '''
        User facing UI specific.
        This is about as good as it gets for a non Qt UI. Trackbars
        get added later when userland code adds params.
        '''
        # Must override.
        raise NotImplementedError()

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

    def on_before_invoke(self):
        '''
        Called from the tuner. Override this if you want to
        clear status, error indicators etc
        '''
        return

    def on_after_invoke(self,invocation):
        '''
        Called from the tuner. Override this if you want to
        do some comprehensive post processing results.
        '''
        return

    def on_error_update(self, error):
        '''
        For downstream objects  to communicate errors.
        '''
        # Must override.
        raise NotImplementedError()

    def on_timing_update(self, ct:CodeTimer):
        '''
        For downstream objects to communicate timing.
        '''
        # Must override.
        raise NotImplementedError()

    def on_status_update(self, status):
        '''
        For downstream objects to set general status
        '''
        # Must override.
        raise NotImplementedError()

    def on_show_main(self, img, arg_hash):
        '''
        Shows the main image.
        '''
        # Must override.
        raise NotImplementedError()

    def on_show_downstream(self,img, arg_hash):
        '''
        Shows the downstream image
        '''
        # Must override.
        raise NotImplementedError()

    def on_show_results(self, res):
        '''
        Shows results from the tuned function.
        '''
        # Must override.
        raise NotImplementedError()

    def on_await_user(self, delay=None):
        '''
        Show results and wait for user input for next action. This is
        a GUI callback expected by the TuningContext
        '''
        # Must override.
        raise NotImplementedError()

    def on_control_create(self,param):
        '''
        Create a control that represents a tracked param.
        '''
        # Must override.
        raise NotImplementedError()
    def on_control_update(self, param, val):
        '''
        Update a control based on value set in code.
        '''
        # Must override.
        raise NotImplementedError()
    def on_control_changed(self, param, val):
        '''
        Called after a value has changed.
        '''
        # UI stuff must be handled by the deriver
        # invoke() the tuner
        return self.ctx.invoke()

    def on_frame_changed(self, new_frame):
        '''
        When the carousel changes the frame.
        UI stuff should be handled by derivers.
        '''
        if self.ctx is None: return
        self.frame = new_frame

        return

    def grid_search(self, carousel, headless=False,delay=500):
        # because of how different the two UIs are...
        raise NotImplemented()

    def begin(self, carousel=None, delay=0):
        # because of how different the two UIs are...
        raise NotImplemented()


    def build_from_call(self, call_is_method:bool, param_kwargs, call_args, call_kwargs):
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
        return self._parms.build_from_call(call_is_method, param_kwargs, call_args, call_kwargs)

        return

    def save_invocation(self):
        return self.ctx.force_save()

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

    def inspect(self, image,status,delay=0):
        '''
        When you want to show something and pause before the next iteration.
        '''
        self.image = image
        self.on_status_update(status)
        self.on_await_user()
        return
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
    def status(self):
        return ""

    @status.setter
    def status(self,val):
        self.on_status_update(val)


    @property
    def window(self):
        return self.ctx.func_name

    @property
    def func_name(self):
        return self.ctx.func_name

    @property
    def sampling(self):
        '''
        For the rich UI
        '''
        return

    @sampling.setter
    def sampling(self,val):
        '''
        For the rich UI
        '''
        return


