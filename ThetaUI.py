
import tkinter as tk

from tkinter import Variable, ttk
from tkinter import messagebox as mb
from tkinter import dialog as dlg
from tkinter import filedialog as fd
from turtle import shape

# import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# from typing_extensions import IntVar

from core.ParamCheck import ParamCheck
from core.ParamControl import ParamControl
from core.ParamCombo import ParamCombo
from core.ParamSpin import ParamSpin
from core.tk.WaitKeyEmulator import WaitKeyEmulator
# from core.tk.Figure import Figure

from core.tk.Panes import Panes
from core.tk.jsonToTtkTree import jsonToTtkTree
from core.tk.StatusBar import StatusBar
from core.tk.Canvas import Canvas
from core.CodeTimer import CodeTimer


import numpy as np
import random

from TunerConfig import TunerConfig
from core.Carousel import Carousel
from core.Tuner import Tuner
from core.Params import Params
from core.BaseTunerUI import BaseTunerUI
from core.FormattedException import FormattedException
from constants import *
from core.param import param,list_param,bool_param,dict_param



class ThetaUI(BaseTunerUI):
    max_display_images = 2
    def __init__(self, func_main, *, func_downstream=None, pinned_params=None, parms_json=None, qi_plot_map=None):

        super().__init__(func_main, func_downstream=func_downstream, pinned_params=pinned_params, parms_json=parms_json)

        # default miliseconds to wait in grid search
        self.gs_delay = 500
        self.__qi = []
        self.__qi_plot_map = qi_plot_map


        # this is where we will put images
        self.canvas = Canvas(self.image_frame, self, ThetaUI.max_display_images)
        # this will hold a matplotlib plot
        self.plot_canvas = None
        self.__figure:Figure = None

        self.controlrefs = {}

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
            mnu.add_command(label="Save Image",accelerator="F2",command=self.onClick_File_SaveImage)
            win.bind("<F2>", self.onClick_File_SaveImage)
            mnu.add_command(label="Save Results",accelerator="F3",command=self.onClick_File_SaveResult)
            win.bind("<F3>", self.onClick_File_SaveResult)
            mnu.add_command(label="Save Plot",accelerator="F4",command=self.onClick_File_SavePlot)
            win.bind("<F4>", self.onClick_File_SaveResult)
            mnu.add_separator()
            mnu.add_command(label="Quit",accelerator="Ctrl+Q", command=self.onClick_File_Exit)

            mnu = tk.Menu(mm, tearoff=0)
            mm.add_cascade( menu=mnu, label="Theta")
            mnu.add_command(label="Close",accelerator="F8",command=self.onClick_RateClose)
            win.bind("<F8>", self.onClick_RateClose)
            mnu.add_command(label="Exact",accelerator="F9",command=self.onClick_RateExact)
            win.bind("<F9>", self.onClick_RateExact)
            mnu.add_command(label="Avoid",accelerator="F10",command=self.onClick_RateAvoid)
            win.bind("<F10>", self.onClick_RateAvoid)
            mnu.add_separator()
            mnu.add_command(label="Clear QI",command=self.onClick_Clear_QI)
            mnu.add_command(label="Quite Interesting Plot",command=self.onClick_Plot_QI)


            mnu = tk.Menu(mm, tearoff=0)
            mm.add_cascade( menu=mnu, label="Grid Search")
            mnu.add_command(label="Run",accelerator="F5",command=self.onClick_GridSearch)
            win.bind("<F5>", self.onClick_GridSearch)
            mnu.add_separator()
            self.gs_delay_var = tk.IntVar(self.winMain,500,"gs_delay")
            mnu.add_radiobutton(label="500 ms delay", var=self.gs_delay_var, value=500, command=self.set_gs_delay) #
            mnu.add_radiobutton(label="1 second", var=self.gs_delay_var, value=1000, command=self.set_gs_delay)
            mnu.add_radiobutton(label="2 seconds", var=self.gs_delay_var, value=2000, command=self.set_gs_delay)
            mnu.add_radiobutton(label="3 seconds", var=self.gs_delay_var, value=3000, command=self.set_gs_delay)

            mnu = tk.Menu(mm, tearoff=0)
            mm.add_cascade( menu=mnu, label="View")
            mnu.add_command(label="Next",accelerator="Return",command=self.onClick_View_Next)
            win.bind("<Return>", self.onClick_View_Next)
            mnu.add_command(label="Previous",accelerator="Shift+Return",command=self.onClick_View_Prev)
            win.bind("<Shift Return>", self.onClick_View_Prev)


            return mm
        def config_status(win):
            sdef = {
                    "file":{
                        "justify":"left"
                        ,"minwidth":20
                    }
                    ,"frame":{
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
        def config_styles(win):
            '''
            https://pypi.org/project/ttkthemes/
            AWESoME!
            https://ttkbootstrap.readthedocs.io/en/latest/license/
            '''
            self.style = ttk.Style(win)
            self.style.theme_use("aqua")

            self.style.configure("tuner.Toolbutton", None
                        , padding=0
                        , border=0
                        , width = 24
                        , height = 18
                        # , background = "silver"
                        # , relief = tk.RIDGE
                        )

            self.style.configure('results.Treeview'
                        , font='Monoisome 16')
            return

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

        # create our custom ttk styles
        config_styles(self.winMain)

        # get a 3 paned window going
        d = Panes.get_default_3_part_def()
        d["left"]["name"] = "results"
        d["right_top"]["name"] = "image"
        d["right_bottom"]["name"] = "tuner"
        d["right_bottom"]["stretch"] = "never"

        pns = Panes(self.winMain,d).build()
        self.tuner_pane:tk.PanedWindow =pns["tuner"]
        self.tuner_frame = pns['tuner']
        self.results_frame:tk.Frame = pns['results']


        # add a notebook to the image frame so we can show an image and a plot
        nb:ttk.Notebook = ttk.Notebook(master = pns['image'])
        # add the notebook to the pane
        # grid does not work with notebooks and anything contained
        # in a notebook, only pack does
        nb.pack(expand=1,fill=tk.BOTH)

        # add the image and plot tabs to the notebook
        self.image_frame= ttk.Frame(master=nb)
        nb.add(self.image_frame ,text="Image",sticky="nswe")

        self.plot_frame = ttk.Frame(master=nb)
        nb.add(self.plot_frame  ,text="Plot",sticky="nswe")


        # configure its grid
        self.controls = []
        self.control_columns = 3
        for i in range(self.control_columns):
            self.tuner_frame.columnconfigure(i,pad=2,weight=1)

        self.results_tree = jsonToTtkTree(self.results_frame, "results",style="tuner.Treeview")


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

    def onClick_File_SavePlot(self, *args, **kwargs):
        # save the plot if any
        if not self.plot_canvas: return
        f = fd.asksaveasfilename(defaultextension="png", title="Save this plot..."
                                    ,filetypes=(("png files", "*.png")
                                    ,("All files", "*.*") )
                                )
        if f and f != "":
            self.__figure.savefig(f)
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
        try:
            self.__grid_search()

        except Exception as e:
            self.on_error_update(e)

        return
    def onClick_Clear_QI(self, *args, **kwargs):
        self.__qi.clear()
        return
    def onClick_Plot_QI(self, *args, **kwargs):
        # TODO: make a gui for building this map
        # colors = ['blue', 'green','red','cyan','magenta','yellow','black']
        colors = ['tab:blue', 'tab:orange', 'tab:green','tab:red','tab:purple','tab:brown','tab:pink','tab:gray','tab:olive','tab:cyan']
        x = None
        x_fld = None
        map = self.__qi_plot_map
        qi = self.__qi
        if not (map and qi): return
        if not "y" in map: return


        if "x" in map:
            # user specified the x
            x_fld = map["x"]
            if not x_fld in qi[0]: return
            xlabel = x_fld
        else:
            # just a simple series - use the ordinal position as x
            x = np.linspace(1, len(qi), len(qi))
            xlabel = "index"

        y_flds = map["y"]
        # check that all the things in the y set actually exist
        for item in y_flds:
            if not item in qi[0]: return
        # mix it up, get a random bunch of colors
        these = random.choices(range(len(colors)),k=len(y_flds))
        these_colors = []
        for i in these:
            these_colors.append(colors[i])

        if x_fld: x = np.empty(shape=(len(qi),),dtype=np.object_)
        y = np.empty(shape=(len(qi),len(y_flds)))
        for i, item in enumerate(qi):
            if x_fld: x[i] = item[x_fld]
            for j, col in enumerate(y_flds):
                y[i][j] = item[col]

        handles = []
        fig:Figure = Figure()
        ax = None
        tkw = dict(size=4, width=1.5)
        for i,label in enumerate(y_flds):
            if not ax:
                ax = fig.add_subplot()
                ax.set_xlabel(xlabel)
                ax.tick_params(axis='x', **tkw)
                style = "-"
            else:
                ax = ax.twinx()
                style = "-"
            data = y[:,i]
            ax.set_ylim(np.min(data), np.max(data))
            ax.set_ylabel(label)
            ax.yaxis.label.set_color(these_colors[i])
            ax.tick_params(axis='y', colors=these_colors[i], **tkw)
            p, = ax.plot(x, data, style, label=label,color=these_colors[i])
            handles.append(p)



        if 'title' in map: ax.set_title(map['title'])
        ax.legend(handles=handles)
        # if 'ylabel' in map: ax.set_ylabel(map['ylabel'])
        # if 'xlabel' in map: ax.set_xlabel(map['xlabel'])
        self.figure = fig

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
        self.results_tree.build(self.quite_interesting,under_heading="Quite Interesting",replace=True)
        # sooooo important to have the next line
        self.winMain.update_idletasks()
        self.winMain.bell()
        return

    def on_error_update(self, e):
        try:

            e = FormattedException(self.winMain)
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

    def on_show_main(self, img, arg_hash):
        if not self.headless: self.canvas.render(img, arg_hash + "_m")

        return

    def on_show_downstream(self,img, arg_hash):
        if not self.headless: self.canvas.render(img, arg_hash + "_d")

        return

    def on_show_results(self, res):
        if not self.headless: self.results_tree.build(res, under_heading="results", replace=True)
        return

    def on_await_user(self, up_next=None):
        def null_route(*args, **kwargs):
            # Here because of the way things
            # had to be done with openCV

            # self.winMain.after(500)
            self.winMain.deiconify()
            return True

        self._on_await_user = null_route

        if not up_next is None:
            # set this up to be called after all the screen refreshes etc
            self.winMain.after(1000, up_next)

        # so these next lines should be called exactly once
        # self.winMain.update()
        # self.winMain.deiconify()
        # things go away if you do not call this mainloop thing
        self.winMain.mainloop()
        return

    def on_frame_changed(self, new_frame):
        super().on_frame_changed(new_frame)

        # do UI stuff
        # title = f"{self.window}"
        try:
            # self.winMain.title(title)
            self.StatusBar["file"] = new_frame.title
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

    def grid_search(self, carousel, headless=False,delay=500):
        '''
        This should only be called from userland code.
        Conducts a grid search across the trackbar configuration, and saves
        aggregated results to file. When not in headless mode, you can
        save images and results for individual files as they are displayed.
        carousel:   A fully initialize Carousel, use the carousel_from_() helper functions to gin one up.
        headless:   When doing large searches, set this to True to suppress the display.
        delay   :   When not in headless mode, acts like begin()
        '''
        try:
            self.headless = headless
            self.gs_delay = delay

            # enter the carousel
            self.ctx.enter_carousel(carousel, self.headless)
            # do a show, and it looks like modal show is all there is
            self.on_await_user(up_next=self.__grid_search)


        except:
            self.on_error_update(None)
        finally:
            pass
        return

    def set_gs_delay(self, *args, **kwargs):
        # user selected a different wait time
        self.gs_delay = self.gs_delay_var.get()
        return

    def __grid_search(self):
        '''
        only called internally
        '''

        if self.in_grid_search: return

        kp = WaitKeyEmulator(self.winMain, func=self.on_await_user, delay=self.gs_delay)
        try:
            self.status = "In grid search..."
            self.in_grid_search = True
            self.on_await_user = kp.sink
            ret = self.ctx.grid_search()

        except Exception as e:
            self.on_error_update(e)
        finally:
            self.in_grid_search = False
            if kp.value == False:
                self.status = "Grid search cancelled..."
            else:
                self.status = "Grid search complete."
            self.on_await_user = kp.release()

        return

    def begin(self, carousel=None, delay=0):
        '''
        Display the Tuner window.
        carousel: A fully initialize Carousel, use the carousel_from_() helper functions to gin one up. See readme for more information.
        delay:    Milliseconds to show each image in the carousel until interrupted by the keyboard. 0 for indefinite.
        '''
        try:
            self.headless = False
            # enter the carousel
            self.ctx.enter_carousel(carousel, self.headless)
            # turn over control to the message pump
            self.on_await_user()

            # hang out - see wht the user wants to do :)
        except Exception as e:
            self.on_error_update(e)
        finally:
            pass
        return

    def inspect(self, image,comment,delay=None):
        '''
        When you want to show something and pause before the next iteration.
        delay is not used - the setting for grid search pauses is used
        '''
        self.image = image
        self.status = comment
        if delay is None: delay = self.gs_delay
        insp = WaitKeyEmulator(self.winMain,delay=delay)

        return insp.null_route()

    @property
    def figure(self) -> Figure:
        # because py won't let me do a write-only property
        return self.__figure
    @figure.setter
    def figure(self,val:Figure) -> None:
        if not isinstance(val,Figure): return

        # get rid of old stuff
        if self.plot_canvas: self.plot_canvas.get_tk_widget().pack_forget()

        # get a new canvas in
        self.__figure = val
        self.plot_canvas = FigureCanvasTkAgg(self.__figure, master=self.plot_frame)
        w = self.plot_canvas.get_tk_widget()
        w.pack(expand=1,fill=tk.BOTH)
        # grid does not work with things in a notebook
        # w.grid(in_=self.master,column=0,row=0,sticky="nswe")

        # finally, draw the figure
        self.plot_canvas.draw()

        return

    @property
    def quite_interesting(self):
        return self.__qi

    @quite_interesting.setter
    def quite_interesting(self,val:dict):
        self.__qi.append(val)

        return
    def save_qi(self):

        return