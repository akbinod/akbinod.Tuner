import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mb
from tkinter import dialog as dlg
from tkinter import filedialog as fd
from panes import panes
from jsonToTtkTree import jsonToTtkTree
from StatusBar import StatusBar

import cv2

class SampleMainWindow():
    def __init__(self, title, *, className=None) -> None:
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
                    "timing":{
                        "justify":"center"
                        ,"minwidth":10
                    }

            }
            # check row number
            myStatusBar = StatusBar(win,1,sdef)
            return myStatusBar

        self.className = title if className is None else className
        self.winMain = tk.Tk(baseName=self.className,className=self.className)
        # Adjust the grid on the main body, we want a grid with just the
        # one col and one row PLUS the one row for the status bar.
        self.winMain.columnconfigure(0,weight=1)
        self.winMain.rowconfigure(0,weight=1)
        self.winMain.rowconfigure(1,weight=0)

        # add in the status bar
        self.StatusBar = config_status(self.winMain)


        # replace the default tk menu
        self.main_menu = config_menus(self.winMain)
        self.panes = panes(self.winMain,["results", "image", "tuner"]).build()

        # non proportional font on Mac, used to be a system font
        res_style = ttk.Style().configure('results.Treeview', font='Menlo 16')
        self.results_tree = jsonToTtkTree(self.panes["results"], "results",style=res_style)
        # this is a test
        self.results_tree.build(None)

        # style = ttk.Style()
        # style.theme_use("alt")

    def show(self):
        self.winMain.mainloop()

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
        # mb.showinfo("Help...","Is not on the way!")
        return

    def onClick_File_SaveResult(self, *args, **kwargs):
        # mb.showinfo("boo..."," onClick_File_SaveResult triggered")
        return

    def onClick_View_Next(self, *args, **kwargs):
        # mb.showinfo("Next...","Next triggered")
        return

    def onClick_View_Prev(self, *args, **kwargs):
        # mb.showinfo("Next...","Prev triggered")
        return

    def onClick_RateClose(self, *args, **kwargs):
        # mb.showinfo("boo..."," onClick_RateClose triggered")
        return

    def onClick_RateExact(self, *args, **kwargs):
        # mb.showinfo("boo..."," onClick_RateExact triggered")
        return

    def onClick_RateAvoid(self, *args, **kwargs):
        # mb.showinfo("boo..."," onClick_RateAvoid triggered")
        return

    def onClick_GridSearch(self, *args, **kwargs):
        mb.showinfo("boo..."," onClick_GridSearch triggered")
        return

if __name__ == "__main__":
    w = myMainWindow("Hello, World",className="tara")
    w.show()