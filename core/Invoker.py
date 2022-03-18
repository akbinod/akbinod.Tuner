import tkinter as tk
import functools as ft
from core.CodeTimer import CodeTimer

class Invoker():
    '''
    This can invoke a partial handed to it. This partial must be fully loaded
    with args, and a ref to the tuner if any.
    It calls provided callbacks for timing, success, and error.
    and such, but does nothing else with the tuner.
    '''
    def __init__(self, ui, func_name, *,
                    cb_completed:ft.partial=None
                    , cb_errored:ft.partial=None
                    , cb_timing=None) -> None:
        self.ui = ui
        self.func_name = func_name
        self.completed = cb_completed
        self.errored = cb_errored
        self.timing = cb_timing

        return

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self,val:ft.partial):
        self.__target = val
        return

    def invoke(self):
        '''
        This is going to get triggered on some button or menu item click.
        Invoke the target function. That should handle all interactions
        with the tuner.
        '''

        if self.__target is None: return
        ct = CodeTimer(self.func_name)
        try:
            with ct:
                self.target()
                if not self.completed is None: self.completed()

        except:
            if not self.errored is None: self.errored()
        finally:
            # show timing
            if not self.timing is None: self.timing(ct)
        return
