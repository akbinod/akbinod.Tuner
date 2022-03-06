import tkinter as tk
from tkinter import ttk
# from tkinter.ttk import ComboBox
from core import param

class ParamControl():
    def __init__(self, p:param) -> None:
        self.p:param = p

        return

    @property
    def value(self):
        raise NotImplemented()

    @value.setter
    def value(self,val):
        raise NotImplemented()
        return
