import numpy as np
import cv2


class VideoFrameGenerator():
    def __init__(self, full_path:str, background_frame_count=3, tuner=None) -> None:
        '''
        Generates consecutive image pairs to iterate.
        full_path: path to video

        '''
        self.full_path = full_path
        self.background_frame_count = background_frame_count
        self.tuner = tuner

        self.scale_range = (0,1)
        self.convert_grayscale = True
        self.index = -1


        # TODO: tune this
        # used to suppress subtraction noise
        self.noise_q = 0.99
        # if tuner: self.noise_q = tuner.noise_q
        self.denoise = False
        # if tuner: self.denoise = tuner.denoise

        # get the background that will be subtracted later
        self.background = None
        self.frame_shape = None
        self.shape = None
        self.frame_count = None

        self.analyze_basics()

        self.video = cv2.VideoCapture()
        self.video.open(full_path)
        self.prev_image = None

        return


    def analyze_basics(self):
        '''
        A one time op to get a background defined as the avg of the first 3(?) frames
        Also determines shape, so this must be run.
        '''

        vid = None
        try:
            vid = cv2.VideoCapture()
            vid.open(self.full_path)

            # read the first one so we know what the frame size is
            _, f = vid.read()
            if f is None: return
            # determine the shape that will be used later to store Bt
            self.frame_shape = f.shape
            self.frame_count = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
            self.shape = (self.frame_count,f.shape[0], f.shape[1])
            # don't want to denoise the background - it's all noise, eh?
            f = self.pre_treat(f,suppress_denoise=True)

            fs = np.zeros(shape=(self.background_frame_count,f.shape[0], f.shape[1]),dtype=np.float32)
            fs[0] = f.copy()
            for i in range(1,self.background_frame_count):
                _, f = vid.read()
                f = self.pre_treat(f,suppress_denoise=True)
                fs[i] = f.copy()

            # we've generated a dynamic background that is the average of (3?) frames
            self.background = np.mean(fs,axis=0)

        finally:

            if vid: vid.release()

        return
    def pre_treat(self, f:np.ndarray, *, suppress_denoise=False) -> np.ndarray:
        # ret = f.astype(np.float32)
        if self.convert_grayscale: f = cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
        if self.denoise and not suppress_denoise: f = cv2.fastNlMeansDenoising(f,h=3,templateWindowSize=7,searchWindowSize=21)

        # no normalization before MorphologyEx

        return f
    def subtract_background(self, f:np.ndarray) -> np.ndarray:
        '''
        Subtracts the background, and gets rid of the noise left behind by frame subtraction
        '''
        f = np.abs(f - self.background)
        noise = int(np.quantile(f,(self.noise_q)))
        if noise > 0:
            noise_kernel = np.full(shape=(5,5), fill_value = noise, dtype=np.uint8)
            f = abs(cv2.morphologyEx(f,cv2.MORPH_OPEN,kernel=noise_kernel))
        return f

    def _read(self,vid=None):
        if vid is None: vid = self.video
        r, f = vid.read()
        if r:
            self.index +=1
            f = self.pre_treat(f)
            # f = self.subtract_background(f)

        return r, f

    def __iter__(self):
        return self

    def __next__(self):
        '''
        Returns:
        2 tuples.
            Tuple1: previous frame, and current frame
            Tuple2: index of previous frame, and index of current frame
        '''
        while self.video.isOpened():

            ret,image = self._read()
            if not ret: break

            if self.prev_image is None:
                # first time around
                self.prev_image = image
                ret,image = self._read()
                # really unlikely that we would have less than 2 frames in a video
                if not ret:break

            t_fr = (self.prev_image, image)
            t_ix = (self.index - 1, self.index)
            yield t_fr, t_ix

            self.prev_image = image
        # done iterating our video
        self.video.release()
        return
