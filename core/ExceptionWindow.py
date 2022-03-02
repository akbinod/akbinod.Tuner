
import tkinter as tk
# from tkinter import ttk


class ExceptionWindow():
    def __init__(self, title, *, fex=None, className=None) -> None:
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
            mnu.add_command(label="Quit", command=self.onClick_File_Exit,accelerator="Ctrl+Q")


            return mm

        self.className = title if className is None else className
        self.winMain = tk.Tk(baseName=self.className,className=self.className)
        self.fex = None
        # Adjust the grid on the main body, we want a grid
        # with just the one col and one row
        self.winMain.columnconfigure(0,weight=1)
        self.winMain.rowconfigure(0,weight=1)

        # replace the default tk menu
        self.main_menu = config_menus(self.winMain)

        # # non proportional font on Mac, used to be a system font
        # style = ttk.Style()
        # # style.configure('tree.Treeview', font='Menlo 16')
        # style.theme_use("alt")
        try:
            self.t:ttk.Treeview = ttk.Treeview(self.winMain,selectmode='browse'
                                            # ,style=style
                                            ,columns=["file", "line_num", "line", "path"])
            self.t.grid(column=0,row=0,in_=self.winMain,sticky="nswe",padx=3,pady=3)
            self.tree_root = self.t.insert("",'end',text="stack")
        except Exception as e:
            pass

        self.exception = fex

    def show(self):
        self.winMain.mainloop()

    def onClick_File_Exit(self, *args):
        # delete all resources
        self.winMain.quit()
        # don't do an exit() here, the parent might want to post process
        return
    def clear(self):
        if self.tree_root != "":
            cn = self.t.get_children(self.tree_root)
            if len(cn) > 0 : self.t.delete(cn)
        return
    def __build(self):
        if self.fex is None: return
        self.winMain.title(self.fex.error)
        j = self.fex.json_tree
        self.clear()
        # self.t.insert(self.tree_root,'end',text="error", values=[j["error"]])
        # self.t.insert(self.tree_root,'end',text= "in proc", value=j["in proc"])
        # self.t.insert(self.tree_root,'end',text= "first call", value=j["first call"])
        # iid = self.t.insert(self.tree_root,'end',text='stack')

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
    w = ExceptionWindow("Hello, Exception",className="tara")
    w.show()