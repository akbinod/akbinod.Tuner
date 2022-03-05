import tkinter as tk
from tkinter import ttk

class Panes():
    def __init__(self, win:tk.Tk, names:list) -> None:
        self.win = win
        if names is None: names = []
        if len(names) < 3 or len(names) > 4: names = ["left", "right_top", "right_bottom"]
        if len(names) == 3:
            self.__panes_map = {"left":names[0], "right_top":names[1], "right_bottom":names[2]}
        else:
            self.__panes_map = {"left_top":names[0], "left_bottom": names[1], "right_top":names[2], "right_bottom":names[3]}

        return

    def build(self):
        if len(self.__panes_map.keys()) == 3:
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

        k = self.__panes_map["left"] if "left" in self.__panes_map else "left"
        fr = frames[k] = tk.Frame(master=pn)
        pn.add(fr)

        right_child= tk.PanedWindow(master = pn,orient="vertical",sashwidth=sasshwidth, sashrelief=sashrelief)
        pn.add(right_child)

        k = self.__panes_map["right_top"] if "right_bottom" in self.__panes_map else "right_top"
        fr = frames[k] = tk.Frame(master=right_child)
        right_child.add(fr)

        k = self.__panes_map["right_bottom"] if "right_bottom" in self.__panes_map else "right_bottom"
        fr = frames[k] = tk.Frame(master=right_child)
        right_child.add(fr)

        # this is a test
        for key in frames:
            f:tk.Frame = frames[key]
            # each frame just has one col, one row for grid geometry manager
            f.rowconfigure(0,weight=1)
            f.columnconfigure(0,weight=1)

            if test:
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
        k = self.__panes_map["top_left"] if "top_left" in self.__panes_map else "top_left"
        fr = frames[k] = tk.Frame(master=top_child)
        top_child.add(fr)


        k = self.__panes_map["top_right"] if "top_right" in self.__panes_map else "top_right"
        fr = frames[k] = tk.Frame(master=top_child)
        top_child.add(fr)

        # within the bottom
        k = self.__panes_map["bottom_left"] if "bottom_left" in self.__panes_map else "bottom_left"
        fr = frames[k] = tk.Frame(master=bot_child)
        bot_child.add(fr)

        k = self.__panes_map["bottom_right"] if "bottom_right" in self.__panes_map else "bottom_right"
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
