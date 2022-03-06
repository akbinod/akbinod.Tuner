
import tkinter as tk

from tkinter import ttk
from tkinter import messagebox as mb
from tkinter import dialog as dlg
from tkinter import filedialog as fd
from core.ParamCheck import ParamCheck
from core.ParamControl import ParamControl
from core.ParamCombo import ParamCombo
from core.ParamSpin import ParamSpin

from core.tk.Panes import Panes
from core.tk.jsonToTtkTree import jsonToTtkTree
from core.tk.StatusBar import StatusBar
from core.tk.Canvas import Canvas
from core.CodeTimer import CodeTimer


import numpy as np

from TunerConfig import TunerConfig
from core.Carousel import Carousel
from core.Tuner import Tuner
from core.Params import Params
from core.BaseTunerUI import BaseTunerUI
from core.FormattedException import FormattedException
from constants import *
from core.param import param,list_param,bool_param,dict_param

class ThetaUI(BaseTunerUI):

    def build(self):
        def config_menus(win):
            # sets up a menu system
            mm = tk.Menu(win)
            win.config(menu=mm)

            # Add a File menu as a child of the main menu
            # Since we do not need to hold on to the items
            # coming off the main menu, we do not set them
            # up as instance memebers
            mnu = tk.Menu(mm, tearoff=0)
            # add it in
            mm.add_cascade( menu=mnu, label="File")
            # add commands to the File menu
            mnu.add_command(label="Open json",command=self.onClick_File_Open)
            mnu.add_separator()
            mnu.add_command(label="Save Image",accelerator="F2")
            win.bind("<F2>", self.onClick_File_SaveImage)
            mnu.add_command(label="Save Results",accelerator="F3")
            win.bind("<F3>", self.onClick_File_SaveResult)
            mnu.add_separator()
            mnu.add_command(label="Quit", command=self.onClick_File_Exit,accelerator="Ctrl+Q")

            mnu = tk.Menu(mm, tearoff=0)
            mm.add_cascade( menu=mnu, label="Theta")
            mnu.add_command(label="Close",accelerator="F8",)
            win.bind("<F8>", self.onClick_RateClose)
            mnu.add_command(label="Exact",accelerator="F9")
            win.bind("<F9>", self.onClick_RateExact)
            mnu.add_command(label="Avoid",accelerator="F10")
            win.bind("<F10>", self.onClick_RateAvoid)
            mnu.add_separator()
            mnu.add_command(label="Run Grid Search",accelerator="F5")
            win.bind("<F5>", self.onClick_GridSearch)

            mnu = tk.Menu(mm, tearoff=0)
            mm.add_cascade( menu=mnu, label="View")
            mnu.add_command(label="Next",accelerator="Return")
            win.bind("<Return>", self.onClick_View_Next)
            mnu.add_command(label="Previous",accelerator="Shift+Return")
            win.bind("<Shift Return>", self.onClick_View_Prev)

            return mm
        def config_status(win):
            sdef = {
                    "frame":{
                        "justify":"right"
                        ,"minwidth":10
                    }
                    ,"timing":{
                        "justify":"center"
                        ,"minwidth":20
                    }
                    ,"sampling":{
                        "justify":"center"
                        ,"minwidth":5
                    }

            }
            # check row number
            myStatusBar = StatusBar(win,1,sdef)
            return myStatusBar


        self.className = "ak.binod.Tuner.Theta"
        self.winMain = tk.Tk(baseName=self.className,className=self.className)
        self.winMain.title(self.ctx.func_name)

        # Adjust the grid on the main body, we want a grid with just the
        # one col and one row PLUS the one row for the status bar.
        self.winMain.columnconfigure(0,weight=1)
        self.winMain.rowconfigure(0,weight=1)
        self.winMain.rowconfigure(1,weight=0)

        # add in the status bar
        self.StatusBar = config_status(self.winMain)

        # replace the default tk menu
        self.main_menu = config_menus(self.winMain)

        # get a 3 paned window going
        d = Panes.get_default_3_part_def()
        d["left"]["name"] = "results"
        d["right_top"]["name"] = "image"
        d["right_bottom"]["name"] = "tuner"
        d["right_bottom"]["stretch"] = "never"
        pns = Panes(self.winMain,d).build()
        # we're going to do things with this guy
        self.tuner_pane:tk.PanedWindow  =pns["tuner"]
        self.results_frame:tk.Frame = pns['results']
        self.image_frame:tk.Frame = pns['image']
        self.tuner_frame:tk.Frame = pns['tuner']

        # configure its grid
        self.controls = []
        self.control_columns = 3
        for i in range(self.control_columns):
            self.tuner_frame.columnconfigure(i,pad=2,weight=1)


        # non proportional font on Mac, used to be a system font
        res_style = ttk.Style().configure('results.Treeview', font='Menlo 16')
        self.results_tree = jsonToTtkTree(self.results_frame, "results",style=res_style)

        # this is where we will put images
        # self.canvas = Canvas(self.image_frame, self.StatusBar, "sampling")
        self.canvas = Canvas(self.image_frame, self)
        # style = ttk.Style()
        # style.theme_use("alt")

        self.controlrefs = {}
        #This is not the place to do a blocking show()
        return

    def __del__(self):

        return
    def onClick_File_Exit(self, *args):
        # delete all resources
        self.winMain.quit()
        # don't do an exit() here, the parent might want to post process
        return

    def onClick_File_Open(self, *args, **kwargs):
        f = fd.askopenfilename(defaultextension="json", title="Open a JSON file..."
                                    ,filetypes=(("JSON files", "*.json")
                                    ,("All files", "*.*") )
                                )
        if f is not None and f != "":
            self.results_tree.build_from_file(f)
        return

    def onClick_File_SaveImage(self, *args, **kwargs):
        self.ctx.save_image()
        return

    def onClick_File_SaveResult(self, *args, **kwargs):
        # force this invocation data to be saved
        self.save_invocation()
        return

    def onClick_View_Next(self, *args, **kwargs):
        # advance the carousel and invoke
        if not self.in_grid_search:
            self.ctx.advance_frame()
        return

    def onClick_View_Prev(self, *args, **kwargs):
        if not self.in_grid_search:
            self.ctx.regress_frame()
        return

    def onClick_RateClose(self, *args, **kwargs):
        # TODO - genericize how these rating menus are created and handled
        self.ctx.tag(Tags.close)
        return

    def onClick_RateExact(self, *args, **kwargs):
        self.ctx.tag(Tags.exact)
        return

    def onClick_RateAvoid(self, *args, **kwargs):
        self.ctx.tag(Tags.avoid)
        return

    def onClick_GridSearch(self, *args, **kwargs):
        if not self.in_grid_search:
            self.__grid_search()
        return

    def on_before_invoke(self):
        '''
        Called from the tuner.
        '''
        self.StatusBar.error = None
        self.status = ""
        return

    def on_after_invoke(self,invocation):
        self.results_tree.build(invocation,under_heading="invocation",replace=True)
        return

    def on_error_update(self, e):
        try:
            if not e is FormattedException: e = FormattedException()
            self.StatusBar.error = e
        except:
            pass
        return

    def on_timing_update(self, ct:CodeTimer):
        self.StatusBar["timing"] = str(ct)
        return

    def on_status_update(self, status):
        self.StatusBar["status"] = status
        return

    def on_show_main(self, img):
        if not self.headless:
            self.canvas.render("main",img)

        return

    def on_show_downstream(self,img):
        if not self.headless:
            self.canvas.render("downstream",img)
            pass
        return

    def on_show_results(self, res):
        if not self.headless:
            self.results_tree.build(res, under_heading="results", replace=True)
        return

    def on_await_user(self):
        # TODO: should probably check to see if we are already loaded first
        self.winMain.mainloop()
        return

    def on_frame_changed(self, new_frame):
        super().on_frame_changed(new_frame)

        # do UI stuff
        title = f"{self.window}: {new_frame.title}"
        try:
            self.winMain.title(title)
            self.StatusBar["frame"] = f"{new_frame.index} of {new_frame.tray_length}"
        except:
            pass

        return

    def on_control_create(self,param):
        '''
        Create a control that represents a tracked param.
        '''
        self.add_control(param)

        return

    def on_control_update(self,param,val):
        '''
        Update a control based on value set in code.
        '''
        if param.name in self.controlrefs:
            c:ParamControl = self.controlrefs[param.name]
            c.value = val

        return

    # def on_control_changed(self, param, val):
    #     '''
    #     The value of this param just changed
    #     '''
    #     self.on_status_update(param.name + ":" + str(param.get_display_value()))
    #     super().on_control_changed(param, val)
    #     return

    @property
    def sampling(self):
        return self.StatusBar["sampling"]

    @sampling.setter
    def sampling(self,val):
        self.StatusBar["sampling"] = val
        return

    def add_control(self, param):
        def wrap_control(c):
            cc = tk.Frame(self.tuner_frame,border=2, padx=2,pady=2,relief=tk.FLAT)
            cc.rowconfigure(0,weight=0)
            cc.columnconfigure(0,weight = 0)
            if isinstance(c,ttk.Checkbutton):
                # this thing comes with its own label
                cc.columnconfigure(0,weight = 1)
                c.grid(in_=cc,row=0,column=0,sticky="nwe")
            else:
                cc.columnconfigure(1,weight = 1)
                l = tk.Label(cc,justify="right")
                l.configure(text=param.name)
                l.grid(in_=cc,row=0,column=0,sticky="nw")
                c.grid(in_=cc,row=0,column=1,sticky="nwe")
            return cc
        def space_controls():
            # this might be all it takes :)
            self.tuner_pane.configure()
            return

        if isinstance(param, (dict_param,list_param)):
            # build list
            c = ttk.Combobox(None,values=param.display_list)
            self.controlrefs[param.name] = ParamCombo(c,param)

        elif isinstance(param, (bool_param)):
            # build checkbox
            c = ttk.Checkbutton(None,text=param.name,offvalue=0,onvalue=1)
            self.controlrefs[param.name] = ParamCheck(c,param)

        else:
            # build spinbox
            c = ttk.Spinbox(None,justify="left",values=list(param.range),wrap=False)
            self.controlrefs[param.name] = ParamSpin(c,param)


        # only add the actual control in here - not the control container
        self.controls.append(c)
        wc = wrap_control(c)
        i = len(self.controls) - 1
        row = i // self.control_columns
        col = i % self.control_columns
        wc.grid(in_=self.tuner_frame,column=col,row=row,sticky="nwe")
        # the row does not grow in height
        self.tuner_frame.rowconfigure(row,weight=0)
        # expands width equally
        self.tuner_frame.columnconfigure(col,weight=1)
        space_controls()
        return