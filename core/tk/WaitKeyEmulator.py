import tkinter as tk
# import numpy as np
import math
# import functools as ft

class WaitKeyEmulator():
    def __init__(self, win, *, func=None, delay=1000, key_response_map =None, default_value=True) -> None:
        '''
        The map should be in the form keysym:value. On keypress,
        the value associated with keysym will become the value of
        this sink. If an unmapped key is pressed, the default value of True
        will be returned to the blocking call.
            The map defaults to False on Escape keypress.
            Returns default_value if there has been no keypress, or keypress not in map
        '''
        self.delay = delay if delay > 0 else math.inf
        self.win = win
        self.__value = None
        self.default_value = default_value
        # stash the old one
        self.captured_func = func


        self.funcid = None
        self.key_response_map = key_response_map
        if self.key_response_map is None:
            self.key_response_map = {"Escape":False}
        # grab keypress immediately - this may be used as just a timer
        self.funcid = self.win.bind_all('<KeyPress>',self.on_keypress)

        # if self.captured_func is None:
        #     # special case - the user has no need to
        #     # null route - but needs interruptible
        #     # timer functionality
        #     boo = self.sink
        return

    @property
    def sink(self):
        # capture calls to client func

        return self.null_route

    def release(self):
        '''
        Call this when you are ready for things to go back
        to normal. Is needed bacause py does not do references -
        the only way to get unwind the ref is to assign a val
        back to the text name of the func
        '''
        try:
            # stop hogging keys
            if not self.funcid is None: self.winMain.unbind('<KeyPress>',self.funcid)
        except:
            # swallow
            pass

        return self.captured_func

    def null_route(self, *args, **kwargs):
        '''
        Comes here when the client funciton is invoked
        (typically when asked to wait)
        '''
        try:
            delay = self.delay
            # actual wait is just 100ms - lets us
            # process user events frequently
            step = 25
            while delay > 0:
                # must check against the member here
                # get out if there has been a keypress
                if self.__value is not None: break

                # Let the win loop process
                # which then responds to a keypress,
                # which then sets __value
                self.win.update()
                self.win.update_idletasks()

                # actual wait
                self.win.after(step)
                delay -= step

            # set focus
            self.win.deiconify()
            # must use the property here
        except:
            # user may have unloaded their form by this point
            pass
        return self.value #to the blocking call

    def on_keypress(self, e, *args, **kwargs):

        self.__value = self.default_value
        if e.keysym in self.key_response_map:
            # usually looking for 27/Escape
            self.__value = self.key_response_map[e.keysym]

        return

    @property
    def value(self):
        if self.__value is None:
            return self.default_value
        return self.__value


