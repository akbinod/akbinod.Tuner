import json
import tkinter as tk
from tkinter import ttk
import numpy as np
import sys
import os

class jsonToTtkTree():
    def __init__(self, master, root_node_text, *, list_inline_expansion_limit = 2, style=None) -> None:
        if style == None: style = 'Treeview'
        self.t:ttk.Treeview = ttk.Treeview(master,selectmode='browse'
                            ,style=style
                            ,columns=["value"])
        # t.column("item",minwidth=25,stretch=1)
        self.t.column("value",minwidth=25,stretch=3,anchor="e")
        self.t.grid(sticky="nsew")

        self.root_node_text = root_node_text if root_node_text is not None else "root"
        self.inline_expansion_limit = list_inline_expansion_limit
        self.headings = {}

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
    def build(self, j, *,root_node_text=None,under_heading=None,replace=False):

        if j is None: return
        if root_node_text is None or root_node_text == "" :
            if under_heading is None or under_heading == "":
                root_node_text = self.root_node_text

        parent = ""

        if under_heading is not None:
            if under_heading in self.headings:
                parent = self.headings[under_heading]
                if replace:
                    # out with the old
                    self.delete(under_heading=under_heading)
                    # in with the new
                    parent = self.t.insert("", 'end', text=under_heading)
                    self.headings[under_heading] = parent
            else:
                # create the heading
                parent = self.t.insert(parent, 'end', text=under_heading)
                self.headings[under_heading] = parent


        self.paint(parent,root_node_text,j)


        return

    def paint(self, parent, name, it):
        if isinstance(it,type(np.array)):
            self.t.insert(parent,index="end",text=name , values =["<np opbject>"])
            # nothing to be built under this thing, so no use of IID
        elif isinstance(it, dict):
            if name is None:
                # don't want a label for this
                iid = parent
            else:
                iid = self.t.insert(parent,index="end",text=name)

            for key in it:
                self.paint(iid, key, it[key])
        elif isinstance(it, list):
            self.render_list(parent, name, it)

            # When you render a list, it is a complete
            # rendering, and nothing outside the list
            # should get built under it. The current parent
            # should continue to be the parent for the
            # next item from the json. Therefore, we do
            # not set an iid.

        else:
            # plain old field
            if it is None: it = "None"
            if name is None: name = "None"
            self.t.insert(parent, 'end', text=name, values=[it])

        return

    def render_list(self,parent,name,it):
        def render_scalars(parent, name, it):
            # return True if we build
            can_list = True
            for li in it:
                if isinstance(li,(tuple,list,dict,type(np.array))):
                    can_list = False
                    break
            if can_list:
                if len(it) <= self.inline_expansion_limit:
                    # bunch of scalars that we can jam into the display
                    entry:str = "("
                    for li in it:
                        entry += str(li) + ","
                    entry = entry.rstrip(",") + ")"
                    # gotta have something because the list items
                    # have been jammed into a value field
                    if name is None: name = "list"
                    self.t.insert(parent, 'end', text=name, values= [entry])
                else:
                    # just do a flat rendering under parent
                    # these are all just scalars, but the list
                    # size is too long to compress to one line item
                    iid = self.t.insert(parent, 'end', text=name)
                    for li in it:
                        self.t.insert(iid, 'end', text=li)
            return can_list

        def render_tuples(parent, name, it):
            # return True if we build
            can_list = True
            for li in it:
                if not (isinstance(li, tuple) and len(li) == 2):
                    can_list = False
                    break
            if can_list:
                # just do a flat rendering under parent
                iid = self.t.insert(parent, 'end', text=name)
                for li in it:
                    self.t.insert(iid, 'end', text=li[0], values=[li[1]])
            return can_list

        ret = False
        if not render_scalars(parent,name,it):
            if not render_tuples(parent,name,it):
                # now you've gotto go full on recursive descent
                # convert to a dict using the item index
                d = {i:li for i,li in enumerate(it)}
                if name is None:
                    iid = parent
                else:
                    iid = self.t.insert(parent,index="end",text=name)
                ret = self.paint(iid,None,d)
        return

    def delete(self, *, under_heading):
        parent = ""
        if under_heading is not None and under_heading in self.headings:
            parent = self.headings[under_heading]
        if parent != "":
            self.t.delete([parent])
            # cn = self.t.get_children(parent)
            # if len(cn) > 0: self.t.delete(cn)
        return