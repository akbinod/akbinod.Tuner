import numpy as np
from core.PropertyBag import PropertyBag
class Frame(PropertyBag):
    default_title = "frame"
    def __init__(self) -> None:
        self.__image = None
        self.title = Frame.default_title

        self.index =  0
        self.tray_length = 0
        self.files = []
        self.images = []
        self.params = {}
        #Holds user input so that we can save, etc.
        self.user_image_main = None

        return

    @property
    def image(self):
        return self.__image.copy()
    @image.setter
    def image(self, val):
        self.__image = val
        return