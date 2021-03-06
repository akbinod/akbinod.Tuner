from core.Frame import Frame
import cv2
import os
import numpy as np
from core.PropertyBag import PropertyBag
from constants import *
from core.VideoFrameGenerator import VideoFrameGenerator
from core.ImageFrameGenerator import ImageFrameGenerator

class Carousel():
    def __init__(self, tuner, params:list, frame_gen) -> None:
        '''
        Use the TunerUI helper functions to instantiate this.
        Used by the tuner to maintain a carousel state.
        As implemented, does not do well with large movies, but should
        be fine for the toy problems found in the assignments.
        tuner:  Instance of Tuner
        param:  List of image parameter names
        frame_gen: Can be an ImageFrameGenerator, or a VideoFrameGenerator (I miss Interfaces)
        '''
        self.tuner = tuner

        self.params = None if (not params is None and len(params) == 0) else params
        # this could be an image or a video frame generator
        self.frame_gen = None
        # we seem to need a redundant next to get the ball rolling
        if not frame_gen is None: self.frame_gen = next(frame_gen)

        return

    def __enter__(self):
        # self.reset()
        self.tuner.on_enter_carousel(self)
        # weird way of doing it, but OK
        return self

    def __exit__(self, *args):
        # self.reset()
        self.tuner.on_exit_carousel(self)

    def __iter__(self):

        return self

    def __next__(self)->Frame:
        '''
        Generator. Iterate over the user supplied carousel.
        '''
        # The frame generator will throw StopIteration, we
        # do not have to worry about doing that.

        if self.frame_gen is None:
            # MUST RETAIN for TunedFunction()
            # We want one iteration when there's nothing
            # - so yield this once.
            # No image title - let the tuner default to what it will
            self.frame = Frame()
            self.tuner.begin_carousel_advance(self.frame)
            return self.frame
        else:
            self.frame = next(self.frame_gen)
            # Map generated images to the param list
            # filling the params from left to right
            # If there are more images than params, ignore them
            # If there are fewer images than there are params, ignore params
            self.frame.params = {
                            self.params[i]:img
                            for i, img in enumerate(self.frame.images)
                            if i < len(self.params)
                            }

            self.tuner.begin_carousel_advance(self.frame)
            return self.frame

    # def reset(self):
    #     if not self.frame_gen is None: self.frame_gen.reset()
    #     self.frame_gen = next(self.frame_gen)

    # def reverse(self):
    #     # Makes the previous frame 'up next'
    #     if not self.frame_gen is None: self.frame_gen.reverse()


    # def skip(self):
    #     # causes the next frame to be skipped
    #     if not self.frame_gen is None: self.frame_gen.skip

    @staticmethod
    def from_images(tuner,params:list, images:list, im_read_flag, normalize):
        gen = ImageFrameGenerator(images,im_read_flag,normalize)
        c = Carousel(tuner,params,gen)
        return c

    @staticmethod
    def from_video(tuner, params:list, video, gs:FrameGenStyle):
        gen = VideoFrameGenerator(video,gs)
        c = Carousel(tuner,params,gen)
        return c
