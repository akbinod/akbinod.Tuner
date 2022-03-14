from importlib.resources import path
import sys
import traceback
import json
import os
import copy
import tkinter as tk
from tkinter import ttk

class FormattedException():
    def __init__(self, master:tk.Tk=None, *, reverse_stack=True) -> None:
        '''
        Instantiating this class with the default constructor is enough
        to show a decent exception window.
        Pass in master if you want to control when the window shows,
        and add the window as a child of your 'master'

        Minimal usage: implement an exception handler, and create a new
        instance of this class. Run this file for an example.
        '''
        try:
            self.master = master
            self.error = ""
            self.start = {}
            self.end = {}
            self.stack = []
            self.reverse_stack = reverse_stack

            # this sets up the exception part of things        #
            self.__build_exc()
            self.__build_ui()

            if self.master is None or self.master.deiconify() == '':
                # do an immediate show
                # this happens when there
                # are errors in initialization
                # or this class is being used
                # standalone outside a tk application
                self.show()
        except Exception as e:
            # kinda sad if the exception handler screws up, oh well
            print(e)


        return
    def __build_exc(self):
        # format the error string and the call stack
        self.error = f"{sys.exc_info()[0]} - {sys.exc_info()[1]}"
        l = traceback.format_tb(sys.exc_info()[2])

        if self.reverse_stack:
            # I like to see the most recent call up at the top
            # - not scroll to the bottom for it
            l.reverse()

        self.__plain_stack = l

        for li in l:
            method = ""
            rest = ""
            line_no = ""
            file = ""
            pat = ""
            t = li.rpartition(", in ", )
            if not t is None:
                method = t[2]
                a = method.split('\n')
                method = a[0]
                line = a[1]
                rest = t[0]
                t = rest.rpartition(", line ", )
                if not t is None:
                    line_no = t[2]
                    rest = t[0]
                    rest = rest.strip()
                    file = rest[6:]
                    file = file.rstrip('"')
                    t = os.path.split(file)
                    file = t[1]
                    pat = t[0]
                    this = {
                        "path": pat.strip()
                        ,"file": file.strip()
                        ,"line_num":line_no.strip()
                        ,"line": line.strip()
                        ,"method":method.strip().replace('\n', ' : ')
                    }
                    # mo betta repr
                    self.stack.append(this)

        f = (0, len(self.stack) - 1) if self.reverse_stack else (len(self.stack) - 1, 0)
        if f[0] >= 0 and len(self.stack) > f[0]:
            self.end = self.format(self.stack[f[0]])
        if f[1] >= 0 and len(self.stack) > f[1]:
            self.start = self.format(self.stack[f[1]])

        return

    def __build_ui(self):
        # if self.master is None:
        if self.master is None or self.master.deiconify() == '':
            # main window is not visible yet
            self.win = tk.Tk()
            # TODO: put in a null menu someday
        else:
            # do this as a child window

            self.win = tk.Toplevel(master=self.master)
            try:
                self.win.tk.call("::tk::unsupported::MacWindowStyle"
                                    , "style", self.win._w, "utility")
                # Besides utility, other useful appearance styles include floating, plain, and modal.
            except:
                pass
            # Since this is a child window, do not overwrite
            # the parent's menus

        # Adjust the grid on the main body, we want a grid
        # with just the one col and one row
        self.win.columnconfigure(0,weight=1)
        self.win.rowconfigure(0,weight=1)
        self.t:ttk.Treeview = ttk.Treeview(self.win,selectmode='browse'
                                        # ,style=style
                                        ,columns=["file", "line_num", "line", "path"])
        self.t.grid(column=0,row=0,in_=self.win,sticky="nswe",padx=3,pady=3)
        self.tree_root = "" # self.t.insert("",'end',text="stack")

        self.win.title(self.error)

        iid = self.tree_root
        if iid != "":
            cn = self.t.get_children(self.tree_root)
            if len(cn) > 0 : self.t.delete(cn)

        if "stack" in self.json_tree:
            this = self.json_tree["stack"]
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


    def format(self, this):
        s = f'{this["file"]} :: {this["method"]} : {this["line"]}  [line:{this["line_num"]}]'
        return s

    @property
    def json(self) -> dict:
        ret = {}
        ret["error"] = self.error
        ret["in proc"] = self.end
        ret["first call"] = self.start

        l = []
        for item in self.stack:
            t = (
                item["file"] + "::" + item["method"]
                , item["line_num"] + " in " + item["path"] + item["file"]
            )
            l.append(t)
        ret["stack"] = l
        return ret

    @property
    def json_tree(self) -> dict:
        ret = {}
        ret["error"] = self.error
        ret["in proc"] = self.end
        ret["first call"] = self.start
        # st = ret["stack"] = {}
        last = None
        # put it into a tree form
        for this in self.stack:
            curr = copy.deepcopy(this)
            curr["item"] = None
            if last is not None:
                last["item"] = curr
            else:
                # only the first item in the
                # list goes on here, from then on
                # new stack frames get appended to
                # the previous
                ret["stack"] = curr
            last = curr

        return ret

    def __str__(self) -> str:
        return json.dumps(self.json)

    def show(self):
        self.win.bell()
        if isinstance(self.win,tk.Toplevel):
            self.win.deiconify()
        else:
            self.win.mainloop()
        return

if __name__ == "__main__":
    try:
        # force an exception to happen
        a=10/0
    except:
        fex = FormattedException()

