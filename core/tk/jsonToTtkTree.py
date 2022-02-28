import json
import tkinter as tk
from tkinter import ttk
import numpy as np
import sys
import os

class jsonToTtkTree():
    def __init__(self, master, root_node_text, *, list_inline_expansion_limit = 2, style=None) -> None:
        if style == None: style = 'Treeview'
        t = ttk.Treeview(master,selectmode='browse'
                            ,style=style
                            ,columns=["value"])
        # t.column("item",minwidth=25,stretch=1)
        t.column("value",minwidth=25,stretch=3,anchor="e")
        t.grid(sticky="nsew")

        self.root_node_text = root_node_text if root_node_text is not None else "root"
        self.t = t
        self.inline_expansion_limit = list_inline_expansion_limit


        return
    def get_test(self):
        j = {"image": "rectangle_wall_noisy.png"
            , "tuned": {"crop": 1
                        , "method": 5
                        , "preprocessing": {
                                "img_mode": "blue"
                                , "contrast": False
                                , "contrast_flip": False
                                , "contrast_kept_val": 0
                                , "blur": True
                                , "blur_ksize": [7, 7]
                                , "blur_sigmaX": 4
                                , "detect_edge": False
                                , "edge_threshold1": 150
                                , "edge_threshold2": 50
                                , "edge_apertureSize": 3
                                }
                            , "angle": 0
                        }
            , "downstream": {
                    "tl": {"pt": [197, 288]
                            , "angle": 0}
                    , "tr": {"pt": [980, 100], "angle": 0}
                    , "br": {"pt": [1051, 454], "angle": 180}
                    , "bl": {"pt": [283, 639], "angle": 0}
                    }
            }

        return j
    def build_from_file(self,full_path):
        with open(full_path,"r") as f:
            j = json.load(f)

        fn = os.path.split(full_path)[1]
        self.build(j,root_node_text=fn)
        return
    def build(self, j, *,root_node_text=None):

        def paint(parent, name, it, ):
            if isinstance(it,type(np.array)):
                iid = self.t.insert(parent,index="end",text=name , values =["<np opbject>"])
            elif isinstance(it, dict):
                iid = self.t.insert(parent,index="end",text=name)
                for key in it:
                    paint(iid, key, it[key])
            elif isinstance(it, list):
                if len(it) <= self.inline_expansion_limit:
                    recur = False
                    for li in it:
                        if isinstance(li,(list,dict,type(np.array))):
                            recur = True
                            break
                else:
                    recur = True
                if recur:
                # convert to a dict using the item index and send it over
                    d = {i:li for i,li in enumerate(it)}
                    iid = self.t.insert(parent,index="end",text=name)
                    paint(iid,None,d)
                else:
                    # bunch of scalars that we can jam into the display
                    # entry:str = name +": ["
                    entry:str = "["
                    for li in it:
                        entry += str(li) + ","
                    entry = entry.rstrip(",") + "]"
                    iid = self.t.insert(parent, 'end', text=name, values= [entry])
            else:
                # plain old field
                if it is None: it = "None"
                # entry = f"{name} : {it}"
                iid = self.t.insert(parent, 'end', text=name, values=[it])

        if j is None: j = self.get_test()
        if root_node_text is None or root_node_text == "" : root_node_text = self.root_node_text
        self.t.children.clear()
        # iid = self.t.insert("",index="end",text=self.root_node_text)
        paint("",root_node_text,j)

        return