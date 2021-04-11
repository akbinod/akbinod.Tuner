import numpy as np
import cv2
from TunedFunction import TunedFunction
from core.constants import *
img_sample_1 = "./images/tuner_sample_color.png"
img_sample_2 = "./images/tuner_sample_bw.jpg"
img_sample_3 = "./images/tuner_circle.png"

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

def launch_draw_circle_on_image():
    '''
    This func launches a tuning session.
    Demonstrates using tuples, lists and dicts to init Tuner.
    '''
    img = cv2.imread(img_sample_1)

    # circles can be drawn in one of these colors
    colors = {
        "red" : (0,0,255)
        , "green": (0,255,0)
        , "blue": (255,0,0)
    }
    # the center will be one of these vals
    centers = [(200,200), (300,300), (400,400), (500,500)]
    # radius will max out at 100, have a min val of 20 and default to 50
    mmd = (100,20,50)

    # this launches the tuner
    img = draw_circle_on_image(img,mmd,colors,centers)

    return

@TunedFunction()
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

def launch_draw_circle():
    '''
    This func launches a tuning session. The simplest demo.
    '''
    img = cv2.imread(img_sample_2)

    # this launches the tuner
    img = draw_circle(img,100)

    return

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

def launch_find_circle():
    '''
    This func launches a tuning session. The simplest demo.
    '''
    img = cv2.imread(img_sample_2)

    # this launches the tuner
    img = find_circle(img,42)

    return

if __name__ == "__main__":
    # launch_draw_circle()
    # launch_draw_circle_on_image()
    launch_find_circle()
    pass
