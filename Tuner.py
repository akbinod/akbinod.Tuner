
import numpy as np
import cv2
# import copy
import os
import tempfile
import sys
import traceback
import json
import time
import functools
# import inspect
import itertools as it
import hashlib as hl

from TunerConfig import TunerConfig
# from TunerUI import TunerUI
from Params import Params
from PropertyBag import PropertyBag
from Carousel import Carousel
from constants import *

class Tuner:
    def __init__(self, ui, config:TunerConfig, params:Params, func_main, func_downstream):
        '''
        Usage:
        This class is the main tuning engine, and is only used by the Ui
        component. It should not be directly accessed by userland code.
        Extenders: follow usage you see in TunerUI.

        ui: set to an instance of TunerUI or a derived class
        config: global config for Tuner
        params: instance of params manager
        func_main: tuned function
        func_downstream: downstream function
        '''
        # we'll raise UI update events on this guy
        self.ui = ui
        self.config = config
        self.params = params

        # primary function to tune
        self.func_main = func_main
        # downstream function to call
        self.func_down = func_downstream

        # get something set up to check against
        self.invocation = None
        # other state variables are initialized in before_invoke

        return

    def on_enter_carousel(self,carousel):
        self.carousel = carousel
        self.slot = None

        # How many invocations on the current carousel
        self.invocation_counter = 0

        # gets reset in the before_invoke
        self.carousel_data = PropertyBag()
        # placeholders
        self.carousel_data.ts = time.strftime('%Y-%m-%d %H:%M', time.localtime())
        self.carousel_data.headless = self.headless
        self.carousel_data.duration = ""
        self.carousel_data.invocations = 0

        self.t1 = time.time()
        self.proc_time1 = time.process_time()


        return

    def on_exit_carousel(self, carousel):
        try:
            # figure duration
            proc_time2 = time.process_time()
            t2 = time.gmtime(time.time() - self.t1)
            outp = f"{time.strftime('%H:%M:%S', t2 )}"
            if t2.tm_sec <= 1 or (proc_time2 - self.proc_time1) < 1:
                outp += f" [process_time: {round(proc_time2 - self.proc_time1,5)}]"
            self.carousel_data.duration = outp
            # set a count of how many iterations happened for
            # this image in the carousel
            self.carousel_data.invocations = self.invocation_counter
        except:
            pass
        finally:
            # This may not be necessary, but is the only
            # way to capture results from/issues with the very
            # last image displayed when there is no tagging
            # by the user.
            self.save_last_invocation()
            self.save_carousel()
            # not traversing a carousel anymore
            self.carousel = None
        return

    def end_carousel_advance(self):
        # event - finished showing an image
        # There may or may not be more images
        # to process and show.

        return

    def begin_carousel_advance(self,carousel):
        # event - before showing an image
        '''
        OK! The analogy to my trusty Kodachrome projector is now thoroughly tortured.
        '''

        self.ui.on_context_changed(carousel)
        return

    def get_func_name(self, cb):
        # import TunedFunction
        ret = None
        if not cb is None:
            if type(cb) is functools.partial:
                ret = cb.func.__qualname__
            else:
                ret = cb.__qualname__
        return ret

    def invoke(self):
        '''
        This is where the target function is invoked.
        The function may take parameters. Of these, we can handle
        the positional and kwonly parameters. When we have matching
        names in theta and parameters to the function, we can pass
        in values from theta in those params - converting them to kwonly
        args in the process.
        If there is a parameter to the function for which:
            1. Tuner has nothing in theta, and
            2. No defaults have been provided in the argspec
        then, the arg is set to None.
        It is a design choice which could introduce hard to find bugs,
        but the current thinking is that the dev would set the defaults
        to None to make progress, and a real call, e.g., from the auto-grader
        would pass a real value.
        '''

        def safe_invoke(cb):
            try:
                if cb is None: return

                if self.__calling_main:
                    # invoke
                    res = cb(**self.params.resolved_args)
                else:
                    # the red headed stepchild gets no arg love
                    res = cb(tuner=self.ui)

                # At this point, the target is done.
                # Use whatever returns we have captured.
                self.set_result(res,is_return=True)
            except Exception as error:
                # do not let downstream errors kill us
                # eventually we'll have an appropriate gui
                # for showing this error
                self.capture_error(self.get_func_name(cb))
            finally:
                # Either the user has set results or we have
                pass
            return

        ret = True
        try:

            # now let the context grab what it may
            self.before_invoke()

            # call the user proc that does the calc/tuning
            self.__calling_main = True
            safe_invoke(self.func_main)

            #  call the user proc that does the secondary processing/application
            self.__calling_main = False
            safe_invoke(self.func_down)

            # done calculating - don't need to do anything
            # special to show the image or the results
            # That gets done when the user sets the
            # `image` and `result` properties from
            # within the target function.

        except:
            pass
        finally:
            # last thing
            self.after_invoke()
            ret = self.ui.on_await_user()

        return ret

    def set_result(self, res, *, is_return:bool=False):
        '''
        Calls from userland to the 'results' property
        are forwarded here. This is also called directly
        by us to save return values with overwrite set to False.
        This allows user set results to be overwrittwen only
        by other user calls. The default return capture does
        not overwrite user results.
        res:        result to store
        is_return:  only set to True internally
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

        try:
            # get a result that we can safely stash
            res = format_result()

            if self.__calling_main:
                if (self.invocation.results.main is None) or not is_return :
                    # either forwarded call from userland, or
                    # default result capture and no results saved yet
                    self.invocation.results.main = res
                    if is_return: self.invocation.results.return_capture = True
            else:
                # the object setting this is the downstream func
                if (self.invocation.results.downstream is None) or not is_return:
                    self.invocation.results.downstream = res
                    if is_return: self.invocation.results.return_capture = True
        finally:
            # Since we do stuff to the results forwarde to us, call back up to the UI
            self.ui.on_show_results(self.invocation.results)
            pass

        return

    @property
    def func_name(self):
        return self.get_func_name(self.func_main)

    @property
    def func_name_down(self):
        return self.get_func_name(self.func_down)

    def save_last_invocation(self):
        # we keep track of results, args, tags etc
        # at the invocation level but only move those
        # into the record at the file/image/title level
        # when certain conditions are met

        if self.invocation is None: return
        save = False
        # user requested save,
        # or we are configured to save all
        # or this carousel is running headless (e.g. in a long grid search)
        save = self.invocation.force_save or self.config.save_all or self.headless
        # or we have an error
        save = save or self.invocation.errored
        # or any of the tags got set on this invocation
        save = save or (len([tag for tag in self.config.tag_names if self.invocation[tag] == True]) > 0)

        if save:
            # save this invocation
            # in the file hive,
            # keyed by the args hash
            hive = None
            if self.slot.title in self.carousel_data:
                hive = self.carousel_data[self.slot.title]
            else:
                # make a hive for this result
                hive = self.carousel_data[self.slot.title] = {}
            # get rid of unseemly attributes
            del(self.invocation.force_save)
            hive[self.arg_hash] = self.invocation

        return save

    def before_invoke(self):
        # about to call the target with a new
        # set of params, save the last set if
        # we ought to. The user may have tagged
        # stuff after viewing it, etc, etc

        self.save_last_invocation()

        # this is the current set of args
        theta = self.params.theta
        self.arg_hash = (hl.md5((json.dumps(theta)).encode('utf-8'))).hexdigest()

        # initialize a complete invocation record
        # with default values here
        self.invocation = PropertyBag()
        # flags
        # tags go here - all set to false initially
        self.invocation.update(self.config.default_tag_map)
        # whether there was an error - for convenience in querying
        self.invocation.errored = False
        # errors go here
        self.invocation.error = ""
        # args, and results last - just a visual thing
        # get updated args
        self.invocation.args = theta
        self.invocation.results = PropertyBag()
        # set up placeholders
        self.invocation.results.main=None
        self.invocation.results.downstream=None
        self.invocation.force_save = False

        return

    def after_invoke(self):
        # important safety tip - do not clear out the last invocation record
        # results from tuner will be grabbed if we need to save them
        # for saving later
        self.invocation_counter += 1

        return

    def tag(self, obs:Tags):
        if self.invocation is None: return
        tag = Tags(obs).name
        self.invocation[tag] = True

        return
    @property
    def results(self):

        return self.invocation.results

    @property
    def image(self):
        '''
        Always return a fresh copy of the user supplied image.
        '''
        return np.copy(self.slot.image)

    @image.setter
    def image(self, val):
        '''
        Set this from your tuned function to have Tuner display it.
        '''
        # This call is forwarded to us by the UI
        # However, since we're deciding which img it is,
        # call back up to the UI to do a display
        if self.__calling_main:
            val = self.__insert_thumbnail(val, self.slot.tn_main)
            self.slot.user_image_main = val
            self.ui.on_show_main(val)
        else:
            # the object setting this is the downstream func
            val = self.__insert_thumbnail(val, self.slot.tn_down)
            self.slot.user_image_down = val
            self.ui.on_show_downstream(val)
    def capture_error(self, func_name):
        self.invocation.errored = True
        # format the error string and the call stack
        error = f"{sys.exc_info()[0]} - {sys.exc_info()[1]}"
        l = traceback.format_tb(sys.exc_info()[2])
        # we're always at the top, so get rid of that
        l.pop(0)
        # put in the nice error message
        l.append(error)
        # I like to see the most recent call up at the top
        # - not scroll to the bottom for it
        l.reverse()
        self.invocation.error = l

        # finally, set the gui status display
        self.ui.on_status_changed(f"Error executing {func_name}: {error}")
    def force_save(self):
        self.invocation.force_save = True
    def get_temp_file(self, suffix=".png"):
        '''
        Creates a temporary file with the specified suffix.
        The temp file is prefixed with the name of the main target,
        and image currently being processed
        '''
        if self.slot is None: return
        prefix = self.func_name
        if self.slot.file_count <= 1 or suffix.endswith(".png"):
            # results for a single file, or it's
            # an image file being saved.
            # Use the file name
            it = self.slot.title
        else:
            # we are going to be saving multiple
            # image results to this file, there's
            # no need to put the image name in the
            # file name.
            it = None

        # check if window currently has an image
        if it == prefix: it = None
        prefix = prefix + "." + it if not (it is None or it == "") else prefix
        if not self.config.overwrite_file:
            # get a unique file name
            prefix += "."
            # we're just going to leave this file lying around
            _, full_path_name = tempfile.mkstemp(
                                # makes it easy to find
                                prefix=prefix
                                ,suffix=suffix
                                ,dir=self.config.wip_dir
                                ,text=True
                                )
        else:
            # we can overwrite the func_name.image_name file
            full_path_name = os.path.join(self.config.wip_dir, prefix + suffix)
            full_path_name = os.path.realpath(full_path_name)
        return full_path_name

    def save_carousel(self):
        '''
        Saves the current set of results to a file following name conventions.
        Use capture to add individual results to the set.
        '''
        ret = True

        fname = self.get_temp_file(suffix=".json")
        try:
            with open(fname,"w") as f:
                f.write(str(self.carousel_data))
                f.write("\n")
        except:
            # dont let this screw anything else up
            self.ui.on_status_changed("Failed to write results.")
            ret = False

        return ret

    def save_image(self):
        '''
        Saves the current image to a temp file in
        the working directory set during initialization.
        '''
        fname = self.get_temp_file(suffix=".main.png")
        cv2.imwrite(fname,self.slot.user_image_main)
        if not self.slot.user_image_down is None:
            fname = fname.replace(".main.", ".downstream.")
            cv2.imwrite(fname,self.slot.user_image_down)
        return

    @property
    def thumbnail(self):
        '''
        This image is inserted into the upper left hand corner of the main image. Keep it very small.
        '''
        if self.__calling_main:
            return self.slot.tn_main
        else:
            return self.slot.tn_down

    @thumbnail.setter
    def thumbnail(self,val):
        # this is the current thumbnail
        if self.__calling_main:
            self.slot.tn_main = val
        else:
            self.slot.tn_down = val
        return

    def __insert_thumbnail(self, mn, tn):
        '''
        mn: main image to insert the thing into
        '''
        # do not use the property - use what has been set
        if not (mn is None or tn is None):
            # Draw a bounding box 1 pixel wide in the top left corner.
            # The box should have enough pixels for all of the image
            bt = 1
            tl = (3,3)
            br = (tl[0] + tn.shape[1] + (2*bt), tl[1] + tn.shape[0] + (2*bt))
            cv2.rectangle(mn,tl,br,HIGHLIGHT_COLOR,thickness=bt)
            # adjust for offset border
            tl = (tl[0] + bt, tl[1] + bt)
            x,x1,y,y1 = self.image_to_array_indices(tl,img_shape=tn.shape)

            tn_dim = np.ndim(tn)
            if np.ndim(mn) == 3:
                mn[x:x1,y:y1, 0] = tn if tn_dim == 2 else tn[:,:,0]
                mn[x:x1,y:y1, 1] = tn if tn_dim == 2 else tn[:,:,1]
                mn[x:x1,y:y1, 2] = tn if tn_dim == 2 else tn[:,:,2]
            else:
                mn[x:x1,y:y1] = tn if tn_dim == 2 else cv2.cvtColor(tn,cv2.COLOR_BGR2GRAY)
        return mn

    def begin(self,carousel):
        self.headless = False
        with Carousel(self,carousel) as tray:
            for slot in tray:
                self.slot = slot
                ret  = self.invoke()
                if not ret: break
        return ret

    def grid_search(self, carousel, headless, esc_cancels_carousel = False, subset=None):
        self.headless = headless
        # the ranges that our trackbars have
        ranges = self.params.get_ranges(subset)
        with Carousel(self,carousel) as tray:
            for slot in tray:
                self.slot = slot
                # Bang on this image.
                user_cancelled = False
                # cart(esian) iterates over the complete set of values that this constellation of trackbars could have.
                # It needs to be rebuilt for each file, as an iteration will exhaust it.
                cart = it.product(*ranges.values())
                for theta in cart:
                    args = {k:theta[i] for i,k in enumerate(ranges)}
                    # Update the trackbar values.
                    self.params.theta = args
                    # Invoke target
                    user_cancelled = not self.invoke()
                    if user_cancelled : break #out of this image
                # done with the last image
                if user_cancelled and esc_cancels_carousel: break

        return not user_cancelled

    def image_to_array_indices(self, img_pt_from, *
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



