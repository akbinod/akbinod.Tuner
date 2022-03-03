
import tkinter as tk
from tkinter import ttk


class ExceptionWindow():
    def __init__(self, master=None, *, fex=None) -> None:

        self.master = master
        # do this as a child window
        self.win = tk.Toplevel(master=master)
        self.fex = fex
        # Adjust the grid on the main body, we want a grid
        # with just the one col and one row
        self.win.columnconfigure(0,weight=1)
        self.win.rowconfigure(0,weight=1)

        # Since this is a child window, do not overwrite
        # the parent's menus

        try:
            self.t:ttk.Treeview = ttk.Treeview(self.win,selectmode='browse'
                                            # ,style=style
                                            ,columns=["file", "line_num", "line", "path"])
            self.t.grid(column=0,row=0,in_=self.win,sticky="nswe",padx=3,pady=3)
            self.tree_root = "" # self.t.insert("",'end',text="stack")
        except Exception as e:
            pass

        self.exception = fex

    def show(self):
        self.win.deiconify()

    def clear(self):
        if self.tree_root != "":
            cn = self.t.get_children(self.tree_root)
            if len(cn) > 0 : self.t.delete(cn)
        return
    def __build(self):
        if self.fex is None: return
        self.win.title(self.fex.error)
        j = self.fex.json_tree
        self.clear()

        iid = self.tree_root
        this = j["stack"]
        while not this is None:
            # replace tree_root with iid to gt the nested structure (meh)
            iid = self.t.insert(self.tree_root,'end',text=this["method"]
                        , values=[
                            this["line"]
                            ,this["file"]
                            ,this["line_num"]
                            ,this["path"]
                            ]
                        )
            this = this["item"]

        return
    @property
    def exception(self,val):
        return self.fex

    @exception.setter
    def exception(self,val):
        self.fex = val
        self.__build()
        return

if __name__ == "__main__":
    ww = tk.Tk("boo")
    ww.deiconify()
    w = ExceptionWindow(ww)
    w.show()
    ww.mainloop()