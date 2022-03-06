import tkinter as tk
from tkinter import ttk

class Panes():
    def __init__(self, win:tk.Tk, panes_def:dict) -> None:

        self.win = win
        if panes_def is None: panes_def = {}
        # if things are out of bounds - get a default def
        if len(panes_def) < 3 or len(panes_def) > 4:
            panes_def = get_default_3_part_def()

        if len(panes_def) == 3:
            if not ("left" in panes_def and "right_top" in panes_def and "right_bottom" in panes_def):
                panes_def = get_default_3_part_def()
        else:
            if not ("left_top" in panes_def and "left_bottom" in panes_def and "right_top" in panes_def and "right_bottom" in panes_def):
                panes_def = get_default_4_part_def()

        self.__panes_def = panes_def
        return

    def build(self):
        if len(self.__panes_def.keys()) == 3:
            self.__panes = self.__add_3panes(False)
        else:
            pass
        return self.__panes

    @property
    def panes(self) -> dict:
        return self.__panes

    def __add_3panes(self, test=False):

        frames = {}

        sticky = "nsew"
        sashrelief = tk.GROOVE
        sasshwidth = 5

        # add in our panes
        pn = tk.PanedWindow(master = self.win,orient="horizontal",sashwidth=sasshwidth, sashrelief=sashrelief)
        # take up all the real estate on the window
        pn.grid(in_ = self.win,row= 0, column=0,sticky="nswe")


        k = self.__panes_def["left"]["name"]
        st = self.__panes_def["left"]["stretch"]
        fr = frames[k] = tk.Frame(master=pn)
        pn.add(fr,stretch=st)

        right_child= tk.PanedWindow(master = pn,orient="vertical",sashwidth=sasshwidth, sashrelief=sashrelief)
        pn.add(right_child)


        k = self.__panes_def["right_top"]["name"]
        st = self.__panes_def["right_top"]["stretch"]
        fr = frames[k] = tk.Frame(master=right_child)
        right_child.add(fr,stretch=st)

        k = self.__panes_def["right_bottom"]["name"]
        st = self.__panes_def["right_bottom"]["stretch"]
        fr = frames[k] = tk.Frame(master=right_child)
        right_child.add(fr,stretch=st)

        # right_child.rowconfigure(0,weight=8)
        # right_child.rowconfigure(1,weight=2)

        for key in frames:
            f:tk.Frame = frames[key]
            # each frame just has one col, one row for grid geometry manager
            f.rowconfigure(0,weight=1)
            f.columnconfigure(0,weight=1)

            if test:
                # this is a test
                l = tk.Label(master=f,justify='center',anchor="center", text=key,border=10,relief=tk.FLAT)
                # t = ttk.Treeview(f,selectmode='browse')
                l.grid(sticky=sticky)


        return frames

    def __add_4panes(self,test=False):
        # UNTESTED
        frames = {}
        # style = {"sticky":"nswe"}
        style = "TFrame"
        sticky = "nsew"
        sashrelief = tk.GROOVE
        sasshwidth = 5

        # add in our panes
        pn = tk.PanedWindow(master = self.win,orient="vertical",sashwidth=sasshwidth, sashrelief=sashrelief)
        # take up all the real estate on the window
        pn.grid(in_ = self.win, row=0,column=0, sticky="nswe")

        top_child= tk.PanedWindow(master = pn,orient="horizontal",sashwidth=sasshwidth, sashrelief=sashrelief)
        pn.add(top_child)

        bot_child= tk.PanedWindow(master = pn,orient="horizontal",sashwidth=sasshwidth, sashrelief=sashrelief)
        pn.add(bot_child)


        # within the top
        k = self.__panes_def["top_left"] if "top_left" in self.__panes_def else "top_left"
        fr = frames[k] = tk.Frame(master=top_child)
        top_child.add(fr)


        k = self.__panes_def["top_right"] if "top_right" in self.__panes_def else "top_right"
        fr = frames[k] = tk.Frame(master=top_child)
        top_child.add(fr)

        # within the bottom
        k = self.__panes_def["bottom_left"] if "bottom_left" in self.__panes_def else "bottom_left"
        fr = frames[k] = tk.Frame(master=bot_child)
        bot_child.add(fr)

        k = self.__panes_def["bottom_right"] if "bottom_right" in self.__panes_def else "bottom_right"
        fr = frames[k] = tk.Frame(master=bot_child)
        bot_child.add(fr)

        for key in frames:
            f:tk.Frame = frames[key]
            # each frame just has one col, one row for grid geometry manager
            f.rowconfigure(0,weight=1)
            f.columnconfigure(0,weight=1)

            if test:
                # l = tk.Label(master=f,justify='center',anchor="e", text=key,border=10,relief=tk.RAISED)
                t = ttk.Treeview(f,selectmode='browse')
                t.grid(sticky=sticky)


        return frames

    @staticmethod
    def get_default_3_part_def():
        d = {   "left":{"name":"left", "stretch":"always"}
                ,"right_top":{"name":"right_top", "stretch":"always"}
                ,"right_bottom":{"name":"right_bottom", "stretch":"always"}
                }
        return d

    @staticmethod
    def get_default_4_part_def():
        d = {   "left_top":{"name":"left_top", "stretch":"always"}
                ,"left_bottom":{"name":"left_bottom", "stretch":"always"}
                ,"right_top":{"name":"right_top", "stretch":"always"}
                ,"right_bottom":{"name":"right_bottom", "stretch":"always"}
            }
        return d