from collections import UserDict
import tkinter as tk
from tkinter import ttk
from turtle import onclick

from async_generator import yield_from_

from core.tk.FormattedException import FormattedException

class StatusBar(UserDict):
    def __init__(self, master:tk.Tk, in_row:int, segments:dict, add_error_panel=True) -> None:
        '''
        Args
        master: the main window on which the status bar appears
        row: the row within master's grid to place this bar on.
                This row will have its resize weight set to 0, you have to set
                the weights on your other rows.
                All columns will be spanned with this bar.
        segments: the additional segments besides the default "status" segment
        The default will grow and shrink as the window resizes, these additional
        ones will stay at their min width.
        Set a segment status thus: myStatusBar["caps"] = value
        Set the main status thus" myStatuBar.status = value OR myStatusBar["status"] = value
        Note - segments:
        1. must not include the default status area
        2. must be in the form:
        {
            "caps":{
                #this is how text is justified
                "justify":"center"
                # this is the minwidth px
                ,"minwidth":25
            }
        }
        What we are holding in super is the def of the status bar
        When the user sets a status value, we just update the bound
        variable held in the dictionary.
        '''

        super().__init__()
        self.master = master
        # self.master:tk.Tk = master
        # set up the frame that contains everything else
        bar:tk.Frame = tk.Frame(
                                master
                                ,border=1
                                ,borderwidth=2
                                ,relief=tk.RIDGE
                                ,background="silver"
                                ,padx=2
                                ,pady=2
                                )
        bar.rowconfigure(0,pad=5,weight=0)
        # add the bar into the parent - on a new row
        cols, rows = master.grid_size()
        # set ourselves in it - this creates a new row
        # on the master's grid
        # span all columns, sticky on the bottom
        bar.grid( in_= master
                    ,row=in_row
                    ,column=0
                    ,columnspan=cols+1
                    ,sticky="swe"
                    ,ipadx=1
                    ,ipady=1
                    )
        # configure that new row which we own
        master.rowconfigure(in_row
                    # tall enough for the status bar
                    ,minsize=bar.winfo_height()
                    # does not expand with window resizing
                    ,weight=0
                    )

        # We should not be mucking with other rows on master
        # so assume that the caller has set things set up correctly
        self.__bar = bar

        # this is the hardcoded main status
        key = self.__main_status = "status"
        this = {}
        this["var"] = tk.StringVar(bar)
        this["label"] = l = tk.Label(master=bar
                ,anchor="w"
                ,justify="left"
                ,border=1
                # ,borderwidth=1
                ,relief=tk.FLAT
                ,background="silver"
                ,padx=1
                ,pady=1
                ,textvariable=this["var"]
                )
        # add this label in to the bar
        l.grid(in_ = bar, row=0,column=0,sticky="w")
        # this label will be the only one that grows
        bar.columnconfigure(0,weight=1)
        super().__setitem__(key,this)

        col = 0
        # build out everything else - sub panels within the main status bar
        for key in segments:
            col += 1
            this = {}
            this["var"] = tk.StringVar(self.__bar)
            this["label"] = l = tk.Label(self.__bar
                                        ,justify = segments[key]["justify"] #text within
                                        ,border=1
                                        # ,bd=1
                                        ,relief=tk.RIDGE
                                        ,background= "silver"
                                        ,padx=1
                                        ,width=segments[key]["minwidth"]
                                        ,textvariable=this["var"])
            # add this label in to the bar
            l.grid(in_ = bar, row=0,column=col,sticky="w")
            # this label will not expand
            bar.columnconfigure(col,weight=0)
            # connect to user event handler
            if "callback" in segments[key]:
                l.bind("<Button-1>",segments[key]["callback"])
            super().__setitem__(key,this)

        # finally add in the error panel
        self.__error = None
        if add_error_panel:
            col += 1
            this = {}
            # no bound var for this
            l = tk.Label(self.__bar
                            ,justify = "center" #text within
                            ,relief=tk.RIDGE
                            ,background= "silver"
                            ,padx=1
                            ,pady=1
                            ,width=5
                            )
            l.columnconfigure(0,weight=1)
            l.columnconfigure(1,weight=0)
            l.columnconfigure(2,weight=1)

            this["label"] = l1 = tk.Label(l,justify="center"
                                            , relief=tk.FLAT
                                            , background="black"
                                            , border=2,width =2,padx=2,pady=1
                                            )
            l1.grid(in_=l,row=0,column=1)

            # add this label in to the bar
            l.grid(in_ = bar, row=0,column=col,sticky="w")
            # this label will not expand
            bar.columnconfigure(col,weight=0)
            super().__setitem__("error",this)
            # This is the thing that we will be
            # switching colors around on
            self.error_label = l1
            l.bind("<Button-1>",self.onclick_error)
            l1.bind("<Button-1>",self.onclick_error)
        else:
            self.error_label = None
        return




    def __getitem__(self, key:str) -> str:
        var:tk.StringVar = super().__getitem__(key)["var"]
        return var.get()

    def __setitem__(self, key:str, item:str) -> None:
        var:tk.StringVar = super().__getitem__(key)["var"]
        return var.set(str(item))

    def onclick_error(self, *args, **kwargs):
        if self.__error is not None:
            self.error.show()
        return
    @property
    def status(self):
        return self[self.__main_status]

    @status.setter
    def status(self,val):
        self[self.__main_status] = val
        return
    @property
    def error(self):
        return self.__error

    @error.setter
    def error(self,val:FormattedException):
        self.__error = val
        if self.error_label is not None:
            # we have one of those set up
            if val is None:
                self.error_label.configure(background="green")
            else:
                self.error_label.configure(background="red")
        return
if __name__ == "__main__":

    # needs to be done here, presumably done
    # differently in your real app
    win = tk.Tk("boo")
    win.rowconfigure(0,weight=1)
    win.columnconfigure(0,weight=1)

    # copy and past the next couple commands
    # set up your definition like below
    sdef = {
            "caps":{
                "justify":"center"
                ,"minwidth":10
            }
            ,"num":{
                "justify":"right"
                ,"minwidth":10
            }
    }
    # check row number
    myStatusBar = StatusBar(win,1,sdef)

    myStatusBar["caps"] = 99
    myStatusBar["num"] = "On"
    myStatusBar["status"] = "hey you, out there in the cold, getting lonely, getting old, can you feel me?"

    win.mainloop()
    # print(myStatusBar.status)
    # print(myStatusBar["caps"])
    # print(myStatusBar["num"])
