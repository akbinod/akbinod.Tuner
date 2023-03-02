import tkinter as tk
from tkinter import ttk
from core import param
from core.ParamControl import ParamControl
from tkinter import filedialog as fd

class ParamFile(ParamControl):
    def __init__(self, c:ttk.Button, p:param, ui) -> None:
        super().__init__(p)

        # self.var = tk.StringVar (master=c,name=p.name,value=None)
        self.c:ttk.Button = c
        c.configure(command=self.onSelectFile)
        self.ui = ui

        return
    def onSelectFile(self, *args, **kwargs):
        filetypes=(("CSV files", "*.csv")
                ,("JSON files", "*.json")
                ,("All files", "*.*")
                )
        f = self.ui.askopenfilename(title=self.p.title
                                    ,filetypes=filetypes
                                    ,defaultextension='csv')
        headless = True if f is None or f == "" else False
        # not self.p.invoke_on_change
        # we do not want a file name clearing to trigger
        # an event that leads to the func running.
        self.p.fileName = f
        # seems redundant - but we want to want to get the message pump going
        self.p.set_value(f,headless_op = headless)
        return


    @property
    def value(self):

        # return self.p.get_value()
        return self.p.get_value()

    @value.setter
    def value(self,val):
        '''
        called to update a control - not used unles we start showing the file name
        '''
        try:
            pass

        except:
            pass
        finally:
            # turn event handling back on
            pass
        return
