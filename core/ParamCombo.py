import tkinter as tk
from tkinter import ttk
# from tkinter.ttk import ComboBox
from core import param
from core.ParamControl import ParamControl

class ParamCombo(ParamControl):
    def __init__(self, c:ttk.Combobox, p:param) -> None:
        super().__init__(p)

        self.c:ttk.Combobox = c
        self.c["state"] = 'readonly'
        self.c.bind('<<ComboboxSelected>>', self.onSelectionChanged)

        return
    def onSelectionChanged(self, *args, **kwargs):
        self.p.set_value(self.value)
        return
    @property
    def value(self):
        return self.c.current()

    @value.setter
    def value(self,val):
        '''
        Pass in whatever the param sends which should be a listindex
        '''
        try:
            # turn off event handling?
            self.c.current(newindex=val)
        except Exception as e:
            pass
        finally:
            # turn event handling back on
            pass
        return
