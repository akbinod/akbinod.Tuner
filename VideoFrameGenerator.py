from Frame import Frame
import cv2
from constants import *

class VideoFrameGenerator():
    def __init__(self, full_path:str, gs:FrameGenStyle = FrameGenStyle.yield_all_new & FrameGenStyle.yield_1) -> None:
        '''
        Generates images for the carousel to iterate. Uses a video to capture consecutive frames.
        full_path: path to video, or video itself
        gs: Flags for how to treat frames. See FrameGenStyle
        '''
        self.full_path = full_path
        self.return_frames = 2 if (gs | FrameGenStyle.yield_2) else 1
        # If we are only returning one frame,
        # or the user has explicitly asked for all_new
        # then the last one does not stick
        self.last_image_sticks = False if self.return_frames == 1 or (gs | FrameGenStyle.yield_all_new) else True
        self.convert_grayscale = True if (gs | FrameGenStyle.convert_grayscale) else False
        self.normalize = True if (gs | FrameGenStyle.convert_normalize) else False

        self.video = cv2.VideoCapture()
        self.video.open(full_path)
        self.last_image = None
        # part of the frame_generator protocol
        self.index = -1
        self.length = self.video.get(cv2.CAP_PROP_FRAME_COUNT)

    def __iter__(self):

        def read():
            r, f = self.video.read()
            if not r:
                self.index +=1
                if self.convert_grayscale: f = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
                if self.normalize: f /= 255

            return r, f

        while self.video.isOpened():
            self.index += 1
            frame = Frame()
            frame.tray_length = self.length

            ret,image = read()
            if not ret: break

            if self.return_frames == 1:
                frame.image = image
                frame.images.append(image)
            else:
                if self.last_image_sticks:
                    if self.last_image is None:
                        # next go round, this will be "last_one"
                        ret,self.last_image = read()
                        # really unlikely that we would have less than 2 frames in a video
                        if not ret:break
                    else:
                        self.last_image, image = image, self.last_image
                else:
                    # two fresh frames requested (not sure why, but hey)
                    ret, self.last_image = read()

                frame.image = self.last_image
                # this yields frame1, frame2
                frame.images.append(image)
                frame.images.append(self.last_image)

            # do this bit after gathering all images
            # our indexing is 0 based
            frame.index = self.index + 1
            yield frame

        # done iterating our video
        self.video.release()
        return

    def reset(self):
        # video does not support this
        return

    def reverse(self):
        # video does not support this
        return
    def skip(self):
        # video does not support this
        return