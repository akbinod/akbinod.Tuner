import os
from platform import java_ver
import numpy as np
import cv2
import scipy.ndimage as nd

from TunedFunction import TunedFunction
from TunerUI import TunerUI
from TunerConfig import TunerConfig
from constants import *
img_sample_1 = "./images/tuner_sample_color.png"
img_sample_2 = "./images/tuner_sample_bw.jpg"
img_sample_3 = "./images/tuner_circle.png"

@TunedFunction()
def find_circle(image, radius,tuner=None):
    # show the original
    display = image.copy()
    # convert grayscale
    image = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    # apply a light blur
    image = cv2.medianBlur(image,9)
    # find circles
    circles = cv2.HoughCircles(image,method=cv2.HOUGH_GRADIENT
                                ,dp=1 ,minDist=10
                                ,param1=15 ,param2=10
                                ,minRadius=radius
                                ,maxRadius=radius)
    if not circles is None:
        # flatten a dim
        circles = circles.reshape(circles.shape[-2],3).astype(np.uint)
        # mark up the display with what we've found
        for c in circles:
            cv2.circle(display
                        ,(c[0],c[1]),c[2]
                        ,color=Highlight.highlight.value
                        )

    if not tuner is None:
        # update Tuner's UI
        tuner.image = display
    return

def demo_find_circle():
    '''
    This func launches a tuning session. The simplest demo.
    '''
    img = cv2.imread(img_sample_2)

    # this launches the tuner
    img = find_circle(img,42)

    return

def demo_decorator_2():
    '''
    Demonstrates using tuples, lists and dicts with TunedFunction()
    '''
    @TunedFunction()
    def draw_circle_on_image(image, radius, color, center, tuner):
        img = np.copy(image)
        img = cv2.circle(img,center=center
                            ,radius=radius
                            ,color=color
                            ,thickness=-1)
        tuner.image = img
        tuner.result = {"result":"OK"}
        return image

    img = cv2.imread(img_sample_1)

    # circles can be drawn in one of these colors
    colors = {
        "red" : (0,0,255)
        , "green": (0,255,0)
        , "blue": (255,0,0)
    }
    # the center will be one of these vals
    centers = [(50,50), (100,100), (200,200), (300,300)]
    # radius will max out at 100, have a min val of 20 and default to 50
    mmd = (100,20,50)

    # this launches the tuner
    img = draw_circle_on_image(img,mmd,colors,centers)

    return

def demo_instantiation():
    '''
    This demonstratess:
        a simple instantiation and the use of begin();
        using two displays
    '''
    def pre_process(tuner=None):
        image = tuner.image
        image = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        image = cv2.medianBlur(image,7)
        image = cv2.Canny(image,15,10)
        tuner.image = image
        return
    def draw_circle(image, radius, tuner):
        '''
        This is a target of tuning.
        '''
        img = np.copy(image)
        img = cv2.circle(img,center=(200,200)
                            ,radius=radius
                            ,color=0
                            ,thickness=4)
        tuner.image = img
        tuner.result = {"result":"OK"}
        return image


    # watch 2 functions
    tuner = TunerUI(draw_circle,func_downstream=pre_process)
    # this is the trackbar for radius
    tuner.track("radius",max=120,min=80,default=100)
    # set up a carousel with just one image
    car = tuner.carousel_from_images(
                        ["image"]       #this is the parameter to feed images to
                        ,[img_sample_2] #these are the images to feed into the parameter above
                        )
    # this launches the tuner
    tuner.begin(car)

    return

def demo_instantiation_2():
    '''
    Demonstrates:
        instantiation and begin();
        the use of lists (of tuples), and dicts
        creating a carousel for "2 image" functions
        Note: `target` is local to this function, but need not be
    '''
    def target(image, other_image, capital, tuner=None):
        image = image.copy()
        image = markup_image(image,str(capital))
        tuner.image = image
        mu = np.mean(other_image)
        return ('other_image mean', mu)

    def markup_image(image,txt=None):
        if txt is None or txt == "": txt = "Kilroy was here."
        pt = (100,100)
        return cv2.putText(image
                    , text = txt
                    ,org= (50,50)
                    ,fontFace = PUT_TEXT_FONT
                    ,fontScale=PUT_TEXT_NORMAL
                    ,color=Highlight.highlight.value
                    ,thickness=HIGHLIGHT_THICKNESS_HEAVY
                    )

    tuner = TunerUI(target)
    # add parameters to tune
    tuner.track("foo", 3,1,2)
    tuner.track_list("capital"
                        ,data_list=[("US","Washington DC"),("India","New Delhi"),("UK","London")]
                        ,default_item=1
                        ,return_index=False)
    tuner.track_dict("bug"
                    ,{"ladybug":1,"praying_mantis":2,"caterpillar":2}
                    ,default_item_key="caterpillar"
                    ,return_key=True
                    )

    # Create a carousel of 2 simultaneous images
    # If you were tracking motion from frame to frame, your
    # tuner initialization code might look something like this.
    image_params = ["image", "other_image"]
    images = [(img_sample_1,img_sample_2), (img_sample_2,img_sample_3)]
    car = tuner.carousel_from_images(image_params, images)

    # kick off the tuning
    tuner.begin(car)
    print(tuner.bug)

    return

def demo_grid_search():
    def rotation(img_in, angle, reshape, tuner):
    # def rotation(img_in, angle, reshape=True, tuner=None):
    # def rotation(img_in, angle=45, reshape=True, tuner=None):
    # def rotation(img_in=None, angle=45, reshape=True, tuner=None):
        # give your usual args some defaults
        ret = None

        # your usual computation goes here
        rimg = nd.rotate(img_in,angle=angle,reshape=reshape)
        ret = f"rotated by {tuner.angle}"
        # just before you return from the function
        if not tuner is None:
            # Refresh results
            tuner.image = rimg
            # not particularly necessary
            tuner.results = ret

        return ret + " - booyah!"

    # This is where you set up the tuner, and turn
    # control over to it.
    tuner = TunerUI(rotation)
    # do the reshap one first
    tuner.track_boolean("reshape")
    tuner.track("angle",max=180)

    # Set up the carousel you are going to tune with.
    c = []
    c.append(os.path.realpath(img_sample_1))
    c.append(os.path.realpath(img_sample_2))
    c.append(os.path.realpath(img_sample_3))
    c = tuner.carousel_from_images(["img_in"],c)
    # kick things off with a grid search
    tuner.grid_search(c,delay=2)

    return

def demo_tuner_from_json():
    def random_preprocess(img_in, curried, tuner=None):
        print(f"received {curried} in curried. No other action here.")
        tuner.image = img_in
        return
    json_def={
        "img_mode":{
            "type":"list"
            ,"data_list":["grayscale","blue","green","red"]
            ,"default":"grayscale"
            ,"display_list":["grayscale","blue","green","red"]
            ,"return_index":False
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
            ,"min":1
            ,"default":4
            }
        ,"contrast":{
            "type":"boolean"
            ,"default":False
            }
        # this next one will be passed in unchanged
        ,"curried":{
            "pinned":42
            }
        # this next one will be ignored by tuner
        ,"bogus_curried":{
            "pinned":42
            }
        ,"random_json":{
            "type":"dict"
            ,"dict_like":{
                "a":"apple"
                ,"b":"banana"
                ,"c":"cherry"
            }
        }
        }

    tuner = TunerUI.tuner_from_json(random_preprocess,None, json_def=json_def)
    c = []
    c.append(os.path.realpath(img_sample_1))
    c.append(os.path.realpath(img_sample_2))
    c = tuner.carousel_from_images(["img_in"],c)
    tuner.begin(c)

    return
if __name__ == "__main__":
    # good place to set statics
    TunerConfig.save_style = SaveStyle.overwrite | SaveStyle.tagged
    TunerConfig.output_dir = "./wip"

    # simplest example of TunedFunction() from the readme
    demo_find_circle()
    # demo_decorator_2()

    # demo of explicit instantiation: begin() and grid_search()
    # demo_instantiation()
    # demo_instantiation_2()
    # demo_grid_search()
    # demo_tuner_from_json()
    pass
