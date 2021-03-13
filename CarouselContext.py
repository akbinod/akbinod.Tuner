import numpy as np
import cv2
import copy
import os
import tempfile
import sys
import json
import time
from Tuner import SaveStyle, Tags, Tuner

class CarouselContext:
    def __init__(self, tuner, files, headless):
        '''
        tuner: set to self
        files: what the cat dragged in
        headless: what the cat says

        Usage:
        Context Manager and Generator: manages the current carousel.
        generator of image files, result tracker, updater of the tuner GUI's
        WindowCaption.
        '''
        if isinstance(files,str): val = [files]
        if not (files is None or isinstance(files,list)):
            # don't accept anything else
            # we probably got a single image
            raise ValueError("Carousel can only be set to a single file name, or a list of file names.")

        self.tuner = tuner
        self.files = files
        self.headless = headless
        self.file_count = 0 if files is None else len(files)

        self.results = {}
        # placeholders
        self.results["headless"] = headless
        self.results["duration"] = ""
        # probably only makes sense in the context of a grid search
        self.results["iterations"] = 0

        self.t1 = time.time()
        self.proc_time1 = time.process_time()

    def __enter__(self):
        # weird way of doing it, but OK
        return self
    def __exit__(self, *args):

        # figure duration
        proc_time2 = time.process_time()
        t2 = time.gmtime(time.time() - self.t1)
        outp = f"{time.strftime('%H:%M:%S', t2 )}"
        if t2.tm_sec <= 1 or (proc_time2 - self.proc_time1) < 1:
            outp += f"\t[process_time: {round(proc_time2 - self.proc_time1,5)}]"
        self.results["duration"] = outp

        try:
            self.save_results()
        except:
            pass

        return
    def __iter__(self):
        '''
        Generator. Iterate over the user supplied carousel.
        '''
        self.title = None
        img = None

        if self.files is None:
            # We want one iteration when there's nothing
            # - so yield this once. This is prob coming
            # from the decorator impl
            # No image title - let the tuner default
            # to what it will
            self.tuner.image_title = None
            self.title = "no_image"
            yield img
        else:
            for index, fname in enumerate(self.files):
                img = cv2.imread(fname)
                if img is None: raise ValueError(f"Tuner could not find file {fname}. Check full path to file.")
                self.title = os.path.split(fname)[1]
                self.tuner.image_title = (self.title,index+1,self.file_count)
                yield img
            # done iterating the images
        return


    @property
    def iterations(self):
        return self.results["iterations"]

    @iterations.setter
    def iterations(self,val):
        self.results["iterations"] = val
        return

    def capture_result(self, user_requested=False):
        stash = False

        this_result = self.tuner.results
        if user_requested or self.tuner.save_all:
            # either user requested save,
            # or we are configured to save all
            stash = True
        else:
            # this save is not user requested
            # and we should only save tagged results
            if ("tags" in this_result and len(this_result["tags"]) > 0):
                # must have the tags object and one that is not empty
                stash = False

        # make a hive for this result
        if stash:
            if not self.title in self.results:
                res = self.results[self.title] = []
            else:
                res = self.results[self.title]

            # we're getting a copy from tuner
            # - no need to make another
            res.append(this_result)

        return
    def get_temp_file(self, suffix=".png"):
        '''
        Creates a temporary file with the specified suffix.
        The temp file is prefixed with the name of the main target,
        and image currently being processed
        '''
        prefix = self.tuner.window
        if self.file_count <= 1 or suffix.endswith(".png"):
            # results for a single file, or it's
            # an image file being saved.
            # Use the file name
            it = self.image_title
        else:
            # we are going to be saving multiple
            # image results to this file, there's
            # no need to put the image name in the
            # file name.
            it = None

        # check if window currently has an image
        if it == prefix: it = None
        prefix = prefix + "." + it if not (it is None or it == "") else prefix
        if not self.overwrite_file:
            # get a unique file name
            prefix += "."
            # we're just going to leave this file lying around
            _, full_path_name = tempfile.mkstemp(
                                # makes it easy to find
                                prefix=prefix
                                ,suffix=suffix
                                ,dir=self.wip_dir
                                ,text=True
                                )
        else:
            # we can overwrite the func_name.image_name file
            full_path_name = os.path.join(self.wip_dir, prefix + suffix)
            full_path_name = os.path.realpath(full_path_name)
        return full_path_name
    def save_results(self):
        '''
        Saves the current set of results to a file following name conventions.
        Let result be None to grab the last set, or provide your own.
        '''
        ret = True
        # j = self.results if result is None else result
        j = self.results
        fname = self.get_temp_file(suffix=".json")
        try:
            with open(fname,"w") as f:
                try:
                    f.write(json.dumps(j))
                except:
                    # could not get a formatted output
                    f.write(str(j))
                f.write("\n")
        except:
            # dont let this screw anything else up
            self.tuner.status = "Failed to write results."
            ret = False

        return ret

    def save_image(self):
        '''
        Saves the current image to a temp file in
        the working directory set during initialization.
        '''
        fname = self.get_temp_file(suffix=".main.png")
        cv2.imwrite(fname,self.tuner.main_image)
        if not self.downstream_image is None:
            fname = fname.replace(".main.", ".downstream.")
            cv2.imwrite(fname,self.tuner.downstream_image)
        return