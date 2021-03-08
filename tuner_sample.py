import numpy as np
import cv2
from TunedFunction import TunedFunction

img_sample_1 = "./tuner_sample_1.png"
img_sample_2 = "./tuner_sample_2_bw.jpg"

@TunedFunction()
def draw_circle(image, radius, color, center, tuner):
    img = np.copy(image)
    img = cv2.circle(img,center=center
                        ,radius=radius
                        ,color=color
                        ,thickness=-1)
    tuner.image = img
    tuner.result = {"result":"OK"}
    return image

def simple_draw_circle():
    '''
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
    img = draw_circle(img,mmd,colors,centers)

    return

if __name__ == "__main__":
    simple_draw_circle()