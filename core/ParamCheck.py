import tkinter as tk
from tkinter import BooleanVar, ttk
from typing_extensions import IntVar
from core import param
from core.ParamControl import ParamControl

class ParamCheck(ParamControl):
    def __init__(self, c:ttk.Checkbutton, p:param) -> None:
        super().__init__(p)
        self.var = tk.IntVar(master=c,name=p.name,value=0)
        self.c:ttk.Checkbutton = c
        c.configure(command=self.onSelectionChanged,variable=self.var)


        return
    def onSelectionChanged(self, *args, **kwargs):
        self.p.set_value(self.value)
        return
    @property
    def value(self):
        return self.var.get()

    @value.setter
    def value(self,val):
        '''
        Pass in whatever the param sends which should be a listindex
        '''
        try:
            # turn off event handling?
            self.var.set(val)
        except Exception as e:
            pass
        finally:
            # turn event handling back on
            pass
        return
