from distutils import core
from typing import List

from core.Carousel import Carousel
import numpy as np
import cv2
import sys

from core.BaseTunerUI import BaseTunerUI
from TunerConfig import TunerConfig
from core.Tuner import Tuner
from core.Params import Params
from core.Carousel import *
from constants import *
from core.CodeTimer import CodeTimer
from core.FormattedException import FormattedException

class TunerUI(BaseTunerUI):

    def build(self):
        '''
        User facing UI specific.
        This is about as good as it gets for a non Qt UI. Trackbars
        get added later when userland code adds params.
        '''
        # build the menuing system
        function_keys ={118:"F4", 96: "F5", 98:"F7", 100: "F8", 101:"F9", 109:"F10"}
        key_map = "Esc: exit Enter: next img Bksp: prev img F1: grid srch F2:save img F3:save args | Tag & Save ["
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
        if not self.ctx.func_name_down is None:
            cv2.destroyWindow(self.ctx.func_name_down)
        pass

    def on_error_update(self, e):
        try:
            es = FormattedException(None)
            cv2.displayStatusBar(self.ctx.func_name,es.Error,60_000)
        except:
            pass
        return

    def on_timing_update(self, ct:CodeTimer):
        cv2.displayStatusBar(self.ctx.func_name, f"processed in {str(ct)}",5_000)
        return

    def on_status_update(self, status):
        cv2.displayStatusBar(self.ctx.func_name,status,60_000)
        return

    def on_show_main(self, img, arg_hash):
        if not self.headless and img is not None:
            cv2.imshow(self.ctx.func_name, img)
        return

    def on_show_downstream(self,img, arg_hash):
        if not self.headless:
            cv2.imshow(self.ctx.func_name_down, img)
        return

    def on_show_results(self, res):
        if not self.headless:
            # TBD - no great way to show results in a purely cv2 UX
            pass
        return

    def on_await_user(self, delay=None):
        '''
        Show results and wait for user input for next action. This is
        a GUI callback expected by the TuningContext
        '''
        # can only "show" in the context of some tuner
        if self.ctx is None: return True
        if delay is None: delay = self.delay
        # And now we wait
        while(not self.headless):
            # Wait forever (when delay == 0)
            # for a keypress.
            # This is skipped when in headless mode.
            k = cv2.waitKeyEx(delay) #& 0xFF

            if k == 122:
                # F1 pressed
                if self.in_grid_search:
                    # Cannot start a grid search while
                    # another one is one. Just continue waiting
                    pass
                else:
                    self.__grid_search()
                    # done with the search,

                # continue to wait for esc
                # or next or whatever the user wants to do next
                continue
            elif k == 120:
                # F2 pressed = save image
                self.ctx.save_image()
                # don't exit just yet - clock starts over
                continue
            elif k == 99:
                # F3 - force this invocation data to be saved
                self.save_invocation()
                # don't exit just yet - clock starts over
                continue
            elif k in self.config.tag_codes:
                # tag the current result - stays in here
                self.ctx.tag(k)
                continue
            elif k == 27:
                # cancel the stack if the Esc key was pressed
                return False
            else:
                # Any other key including spacebar,
                # enter etc. Or the wait time elapsed.
                if self.in_grid_search:
                    # done with a set of params
                    # just return so the next set
                    # can be presented
                    return True
                else:
                    # Done with this image.
                    if k == 8:
                        self.ctx.regress_frame()
                    elif k == 13:
                        # advance the carousel and invoke
                        self.ctx.advance_frame()
                    else:
                        # ignore all other keys
                        pass
                continue

        return True

    def on_frame_changed(self, new_frame):
        super().on_frame_changed(new_frame)

        # do UI stuff
        title = f"{self.window}: {new_frame.title} [{new_frame.index} of {new_frame.tray_length}]"
        cv2.setWindowTitle(self.ctx.func_name,title)
        if not self.ctx.func_name_down is None:
            # keep this in sync with the main window title
            title = f"{self.ctx.func_name_down }: {new_frame.title} [{new_frame.index} of {new_frame.tray_length}]"
            cv2.setWindowTitle(self.ctx.func_name_down, title )

        return

    def on_control_create(self,param):
        '''
        Create a control that represents a tracked param.
        '''
        param.trackbar = cv2.createTrackbar(param.name
                                            ,self.window
                                            ,param.default
                                            ,param.max
                                            ,param.set_value)
        cv2.setTrackbarMin(param.name, self.window,param.min)

    def on_control_update(self,param,val):
        '''
        Update a control based on value set in code.
        '''
        try:
            cv2.setTrackbarPos(param.name, self.window, val)
        except Exception as e:
            self.on_error_update(e)

        return

    def on_control_changed(self, param, val):
        '''
        The value of this param just changed
        '''
        self.on_status_update(param.name + ":" + str(param.get_display_value()))
        super().on_control_changed(param, val)
        return

    def grid_search(self, carousel, headless=False,delay=500):
        '''
        This should only be called from userland code.
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
        # old_delay = self.delay
        self.delay = delay
        try:
            # enter the carousel
            self.ctx.enter_carousel(carousel, self.headless)
            self.__grid_search()
            self.on_await_user()
        finally:
            # self.delay = old_delay
            pass
        return

    def __grid_search(self):
        # only called internally
        try:
            self.in_grid_search = True
            ret = self.ctx.grid_search()
        finally:
            self.in_grid_search = False
            self.on_status_update("Grid search complete.")
        return
    def begin(self, carousel=None, delay=0):
        '''
        Display the Tuner window.
        carousel: A fully initialize Carousel, use the carousel_from_() helper functions to gin one up. See readme for more information.
        delay:    Milliseconds to show each image in the carousel until interrupted by the keyboard. 0 for indefinite.
        '''
        try:
            self.headless = False
            self.delay = delay
            # enter the carousel
            self.ctx.enter_carousel(carousel, self.headless)
            # turn over control to the message pump
            self.on_await_user()
            # when we're back, it's time to leave
        except Exception as e:
            self.on_error_update(e)
        finally:
            # todo: do we need to do this?
            # will this be a problem for the tk gui?
            self.ctx.exit_carousel()
        return