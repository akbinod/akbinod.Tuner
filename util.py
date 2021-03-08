import cv2
import os
import json
import tempfile
import numpy as np
import util

HIGHLIGHT_COLOR = (173,255,47)
HIGHLIGHT_THICKNESS_LIGHT = 1
HIGHLIGHT_THICKNESS_HEAVY = 2
PUT_TEXT_FONT = cv2.FONT_HERSHEY_PLAIN
PUT_TEXT_SMALL = 0.7
PUT_TEXT_NORMAL = 1.0
wip_dir = "./wip/"

def get_temp_file(dir=wip_dir, suffix=".png"):
    # we're just going to leave this file lying around
    _, full_path_name = tempfile.mkstemp(suffix=suffix,dir=dir,text=True)

    return full_path_name

def get_file_path(dir, fname, ext=""):
    duh = os.path.split(fname)
    if duh[0] == "":
        # no path provided in fname
        if dir is None or dir == "":
            dir = "./"
        fname = dir + fname


    duh = os.path.splitext(fname)
    if duh[1] == "":
        # no ext provided
        fname += ext
    else:
        # fname has an extension
        if not ext is None and ext != "":
            # need to overwrite the extension
            fname = duh[0] + ext
    return fname

def dump_json(j , dir = wip_dir, fname="dump_json.json", mode = 'a+'):

    fname = get_file_path(dir,fname,".json")
    try:
        with open(fname,mode) as f:
            try:
                f.write(json.dumps(j))
            except:
                # could not get a formatted output
                f.write(str(j))
            f.write("\n")
    except:
        # dont let this screw anything else up
        pass
    return

def dump_to_file(vals:np.array, *, dir = wip_dir, fname="", mode = 'w'):
    if fname == "":
        fname = get_temp_file(suffix=".csv")
    else:
        fname = get_file_path(dir,fname, ".csv")

    with open(fname, mode) as f:
        for i in range(vals.shape[0]):
            # f.write(f"a[{i}] = [" )
            srow = ""
            if vals.ndim > 1:
                for j in range(vals.shape[1]):
                    if srow != "":
                        srow += ","
                    srow += str(vals[i,j])
            else:
                srow = vals[i]
            f.writelines(f"{srow}\n")
