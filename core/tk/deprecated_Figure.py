import tkinter as tk

from uuid import RESERVED_FUTURE
from matplotlib.figure import Figure as fig
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class Figure(fig):
    '''
    Impements a matplotlib Figure that is displayed in the tuner.
    When you are ready to show, set the figure property of the tuner
    or call show() on this object.
    '''
    def __init__(self, master) -> None:
        super().__init__()
        self.master = master

        return
    def clear(self):
        # clear out old stuff
        w = self.canvas.get_tk_widget()
        if w:
            try:
                w.pack_forget()
            except:
                pass
        return
    def show(self):
        # A canvas must be manually attached to the figure.
        # This is done by instantiating the canvas with the figure.
        self.canvas = FigureCanvasTkAgg(self,self.master)
        self.clear()
        w = self.canvas.get_tk_widget()
        w.pack(expand=1,fill=tk.BOTH)
        # grid does not work with things in a notebook
        # w.grid(in_=self.master,column=0,row=0,sticky="nswe")
        self.canvas.draw()
        return

