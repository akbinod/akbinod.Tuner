import cv2
import os
from PropertyBag import PropertyBag

class Carousel():
    def __init__(self, context, files) -> None:
        '''
        Used by the tuner to maintain a carousel state.
        Not immediately useful to end users.
        '''
        self.context = context
        self.files = files
        if isinstance(files,str): val = [files]
        if not (files is None or isinstance(files,list)):
            # don't accept anything else
            # we probably got a single image
            raise ValueError("Carousel can only be set to a single file name, or a list of file names.")
        self.files = files
        self.file_count = 0 if files is None else len(files)

    def __enter__(self):
        self.index = -1
        self.context.on_enter_carousel(self)
        # weird way of doing it, but OK
        return self

    def __exit__(self, *args):
        self.index = -1
        self.context.on_exit_carousel(self)

    def __iter__(self):
        '''
        Generator. Iterate over the user supplied carousel.
        '''
        self.index +=1
        slot = PropertyBag()
        self.slot = slot

        slot.image = None
        slot.title = "no_image"
        # index is 0 based
        slot.index =  self.index + 1
        slot.file_count = self.file_count
        slot.context_files = []

        #TODO: why should user supplied images go here?
        slot.user_image_main = None
        slot.user_image_down = None
        slot.tn_main = None
        slot.tn_down = None

        if self.files is None:
            # We want one iteration when there's nothing
            # - so yield this once. This is prob coming
            # from the decorator impl
            # No image title - let the tuner default
            # to what it will
            self.context.begin_carousel_advance(slot)
            yield slot
            # do this after an image has been dealt with
            self.context.end_carousel_advance()
        else:
            for index, obj in enumerate(self.files):
                if type(obj) is str:
                    fname = obj
                elif type(obj) is tuple:
                    # just get the last image - this is probably
                    # not going to be used by the client anyway
                    fname = obj[len(obj)-1]
                    # client is responsible for how
                    # these are read and used
                    slot.context_files = [f for f in obj]

                slot.image = cv2.imread(fname)
                # if slot.image is None: raise ValueError(f"Tuner could not find file {fname}. Check full path to file.")
                slot.title = os.path.split(fname)[1]
                self.context.begin_carousel_advance(slot)

                yield slot
                # do this after an image has been dealt with
                self.context.end_carousel_advance()

            # done iterating the images
        return
