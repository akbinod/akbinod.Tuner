import numpy as np
import cv2
import matplotlib.pyplot as plt
import copy
import sys
# # at runtime, get python to look in the root folder
# sys.path.append("..")
# from TunerUI import TunerUI

def stitch_images(img_list):
    if len(img_list) == 0: return

    ret = None
    padding = 5
    ret = img_list.pop(0)
    h = ret.shape[0]

    num_colors = 1 if ret.ndim == 2 else 3
    border = np.ones((h, padding, num_colors))

    while len(img_list) > 0:
        this_img = img_list.pop(0)
        sh = this_img.shape
        t = np.zeros(shape=(h,sh[1]))
        t[0:sh[0],0:sh[1]] = this_img
        # add border
        ret = np.hstack((
                        # the last image
                        ret
                        # plus a border
                        , border
                        # plus the current image
                        , t
                        )
                        )

    return ret
def bin_these(iterable_1d,wt="Bin These"):
    plt.hist(iterable_1d,bins='auto',)
    plt.title(wt +  ":auto binned")
    plt.show()
    hist = bins = mid = None
    try:
        hist, bins = np.histogram(a=iterable_1d)
        # print(hist,bins)
        mid = bins[np.argmax(hist)]
    except:
        # not all data is amenable to this
        pass
    return hist,bins,mid

# this needs to move to TunerUI
def minimal_preprocessor( cb_downstream = None, thumbnail=None):
    '''
    Tuning the pre-processing is a common task in CV. Use this method to
    get a minimal (you will need more for your projects) preprocessing
    tuner that meets some goals like blurring, canny edge detection, etc.
    Pass it the downstream function that consumes the tuned parameters
    to meet your project goals; e.g., finding lines, or matching templates.
    Call the begin() method on the returned object, passing it your image.

    You can use this to develop pre-processing presets. Get to a point
    with the trackbars that you like, and then save the results to file
    to review/copy into your code.

    This function could just as easily have made calls to the track_ set of
    trackbar creation functions. It takes the json def approach as an
    illustration. Use this tuner to get your image to a good stage of
    pre-processing, and save the results. Use the results json in your code.
    '''

    def tune(tuner:TunerUI):
        res = {}
        img = tuner.image
        # we got nothing to say about preprocessing
        res["preprocessing"] = copy.deepcopy(tuner.args)
        tuner.results = res

        # get the processed image
        tuner.image = TunerUI.preprocess_to_spec(img,tuner.args)
        # process the thumbnail if one exists
        if not thumbnail is None:
            tuner.thumbnail = TunerUI.preprocess_to_spec(thumbnail,tuner.args)
        return

    json_def={
    "img_mode":{
        "type":"list"
        ,"data_list":["grayscale","blue","green","red"]
        ,"default":"grayscale"
        }
    ,"blur":{
        "type":"boolean"
        ,"default":True
        }
    ,"blur_ksize":{
        "type":"list"
        ,"data_list":[(3,3), (5,5), (7,7)]
        ,"default":0
        }
    ,"blur_sigmaX":{
        "max":20
        ,"min":0
        ,"default":4
        }
    ,"contrast":{
        "type":"boolean"
        ,"default":False
        }
    ,"contrast_kept_val":{
        "max":255
        ,"default":0
        }
    ,"contrast_flip":{
        "type":"boolean"
        ,"default":False
        }
    ,"detect_edge":{
        "type":"boolean"
        ,"default":False
        }
    ,"edge_threshold1":{
        "max":200
        ,"default":150
        }
    ,"edge_threshold2":{
        "max":200
        ,"default":50
        }
    ,"edge_apertureSize":{
        "type":"list"
        ,"data_list":[3,5,7]
        }
    }

    tuner = tuner_from_json(tune
                            ,cb_downstream
                            ,json_def= json_def)


    return tuner



