from core.Frame import Frame
import cv2
from core.constants import *
import numpy as np
import os

class ImageFrameGenerator():
    def __init__(self, images:list, im_read_flag, normalize:bool) -> None:
        '''
        Generates frames for the carousel to iterate.
        images: Must be a list of file names. These must be packed into tuples,
        each tuple having length equal to the the number of image parameters.
        im_read_flag: one of the openCV IMREAD_ set.
        normalize: divides by 255 when true
        '''
        self.im_read_flag = im_read_flag
        self.normalize = normalize
        self.images = None if not images is None and len(images) == 0 else images

        # part of the frame_generator protocol
        self.length = 0 if self.images is None else len(self.images)
        self.index = -1

    def __iter__ (self):
        return self

    def __next__ (self):
        while self.index < self.length - 1:
            self.index += 1
            frame = Frame()
            frame.tray_length = self.length
            # our indexing is 0 based
            frame.index = self.index + 1
            # get the next set of images to deal with
            t_images = self.images[self.index]
            # this is expected to be a tuple
            if not type(t_images) is tuple: t_images = tuple([t_images])
            for f in t_images:
                if not type(f) in [str, np.ndarray]: raise ValueError("Args to 'images' can only contain file names or images (np.ndarray).")
                if type(f) == str:
                    # we have a file name
                    if not self.im_read_flag is None:
                        im = cv2.imread(f,self.im_read_flag)
                    else:
                        im = cv2.imread(f)
                    if self.normalize:
                        im /= 255
                    # add this  to the files
                    frame.files.append(f)
                    # create a title based on the name - the last file wins
                    frame.title = os.path.split(f)[1]
                else:
                    im = f

                frame.images.append(im)
                # this is a holdover from the old style - last image wins
                frame.image = im

            yield frame

        # done iterating our files

    def reset(self):
        self.index = -1
        return self.index

    def reverse(self):
        # Makes the previous frame 'up next'
        # yes, - 2
        self.index = max[-1, self.index -2]
        return self.index

    def skip(self):
        # causes the next frame to be skipped
        self.index = min[self.length, self.index+1]
        return self.index
