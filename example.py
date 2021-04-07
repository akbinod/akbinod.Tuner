import numpy as np
import cv2
from TunedFunction import TunedFunction

img_sample_1 = "./tuner_sample_1.png"
img_sample_2 = "./tuner_sample_2_bw.jpg"

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

if __name__ == "__main__":
    launch_draw_circle()
    # launch_draw_circle_on_image()
    pass
