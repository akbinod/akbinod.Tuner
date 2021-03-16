
import numpy as np
import cv2
import copy
import os
import tempfile
import sys
import json
import time
# import datetime

from constants import *
import hashlib as hl

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
        self.title = ""
        self.save_all = tuner.save_all

        # How many iterations on
        # the current image from the carousel
        self.image_iter = 0

        # gets reset in the begore_invoke
        # here just to register the var with
        # compile tools
        self.invocation = None
        self.results = {}
        # placeholders
        self.results["ts"] = time.strftime('%Y-%m-%d %H:%M', time.localtime())
        self.results["headless"] = headless
        self.results["duration"] = ""
        # probably only makes sense in the context of a grid search
        self.results["iterations"] = 0
        # used when saving args
        self.tag_map = {}
        for tag in self.tuner.tag_names:
            self.tag_map[tag] = False

        self.t1 = time.time()
        self.proc_time1 = time.process_time()

    def __enter__(self):
        self.tuner.cc = self
        self.image_iter = 0

        # weird way of doing it, but OK
        return self
    def __exit__(self, *args):
        try:
            # figure duration
            proc_time2 = time.process_time()
            t2 = time.gmtime(time.time() - self.t1)
            outp = f"{time.strftime('%H:%M:%S', t2 )}"
            if t2.tm_sec <= 1 or (proc_time2 - self.proc_time1) < 1:
                outp += f"\t[process_time: {round(proc_time2 - self.proc_time1,5)}]"
            self.results["duration"] = outp
            # set a count of how many iterations happened for
            # this image in the carousel
            self.results["iterations"] = self.image_iter
            # this one may be redundant - but if hte user
            # cancels out - this is the only place to capture
            self.capture_result()
            self.save_results()
        except:
            pass
        finally:
            # not traversing a carousel anymore
            self.tuner.cc = None
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
            self.tuner.context_files = []

            yield img
            self.capture_result()
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
                    self.tuner.context_files = [f for f in obj]

                img = cv2.imread(fname)
                if img is None: raise ValueError(f"Tuner could not find file {fname}. Check full path to file.")
                self.title = os.path.split(fname)[1]
                self.tuner.image_title = (self.title,index+1,self.file_count)
                # about to move to a new image - save off the last lot

                yield img
                self.capture_result()
            # done iterating the images
        return

    def before_invoke(self):
        # about to call the target with a new
        # set of params, save the last set if
        # we ought to. The user may have tagged
        # stuff after viewing it, etc, etc
        self.capture_result()

        # this is the current set of args
        a = self.tuner.args
        # hash only user args
        inv = json.dumps(a)
        a = hl.md5(inv.encode('utf-8'))
        self.arg_hash = a.hexdigest()

        self.invocation = {}
        # flags
        # tags go here - all set to false initially
        self.invocation.update(self.tag_map)
        # whether there was an error - for convenience in querying
        self.invocation["errored"] = False
        # errors go here
        self.invocation["error"] = ""
        # args, and results last - just a visual thing
        self.invocation["args"] = self.tuner.args
        self.invocation["results"] = {}

        # for saving later
        self.image_iter += 1
        return
    def after_invoke(self):
        # important safety tip - do not clear out the last invocation record
        # results from tuner will be grabbed if we need to save them
        return

    def tag(self, obs:Tags):
        if self.invocation is None: return
        tag = Tags(obs).name
        self.invocation[tag] = True

        return

    def capture_error(self, error, invoking_main=True):
        # TODO: some day use this invoking_main thing
        self.invocation["errored"] = True
        self.invocation["error"] = repr(error)


    def capture_result(self, force=False):

        # return if nothing initialized yet
        if self.invocation is None: return

        # user requested save,
        # or we are configured to save all
        # or this carousel is running headless (e.g. in a long grid search)
        save = force or self.save_all or self.headless
        # or we have an error
        save = save or ("errored" in self.invocation and self.invocation["errored"] == True)
        # or this invocation got tagged by the user
        save = save or (len([tag for tag in self.tuner.tag_names if self.invocation[tag] == True]) > 0)


        if save:
            hive = None
            # we're getting a copy from tuner
            # - no need to make another
            self.invocation["results"] = self.tuner.results

            if self.title in self.results:
                hive = self.results[self.title]
            else:
                # make a hive for this result
                hive = self.results[self.title] = {}

            # save this invocation
            # in the file hive,
            # keyed by the args hash
            hive[self.arg_hash] = self.invocation


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
            it = self.title
        else:
            # we are going to be saving multiple
            # image results to this file, there's
            # no need to put the image name in the
            # file name.
            it = None

        # check if window currently has an image
        if it == prefix: it = None
        prefix = prefix + "." + it if not (it is None or it == "") else prefix
        if not self.tuner.overwrite_file:
            # get a unique file name
            prefix += "."
            # we're just going to leave this file lying around
            _, full_path_name = tempfile.mkstemp(
                                # makes it easy to find
                                prefix=prefix
                                ,suffix=suffix
                                ,dir=self.tuner.wip_dir
                                ,text=True
                                )
        else:
            # we can overwrite the func_name.image_name file
            full_path_name = os.path.join(self.tuner.wip_dir, prefix + suffix)
            full_path_name = os.path.realpath(full_path_name)
        return full_path_name
    def save_results(self):
        '''
        Saves the current set of results to a file following name conventions.
        Use capture_results() to add individual results to the set.
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
        if not self.tuner.downstream_image is None:
            fname = fname.replace(".main.", ".downstream.")
            cv2.imwrite(fname,self.tuner.downstream_image)
        return