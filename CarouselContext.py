
import numpy as np
import cv2
import copy
import os
import tempfile
import sys
import traceback
import json
import time
from PropertyBag import PropertyBag

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

        # How many invocations on the current carousel
        self.invocation_counter = 0

        # gets reset in the begore_invoke
        # here just to register the var with
        # compile tools
        self.invocation = None
        self.carousel_results = PropertyBag()
        # placeholders
        self.carousel_results.ts = time.strftime('%Y-%m-%d %H:%M', time.localtime())
        self.carousel_results.headless = headless
        self.carousel_results.duration = ""
        self.carousel_results.invocations = 0

        # used when saving args
        self.tag_map = {}
        for tag in self.tuner.tag_names:
            self.tag_map[tag] = False

        self.t1 = time.time()
        self.proc_time1 = time.process_time()

    def __enter__(self):
        self.tuner.cc = self
        self.invocation_counter = 0

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
            self.carousel_results.duration = outp
            # set a count of how many iterations happened for
            # this image in the carousel
            self.carousel_results.invocations = self.invocation_counter

            self.after_context_change()
            self.save_results()
        except:
            pass
        finally:
            # not traversing a carousel anymore
            self.tuner.cc = None
        return

    def after_context_change(self):
        # event - finished showing an image
        # - before moving on to the next.

        # # This capture seems redundant since
        # # we do a capture before each new invoke.
        # # However, when a user just looks at the
        # # first result, tags it, and forwards the
        # # carousel, we need to capture that tagging
        # self.__capture_result()

        return

    def before_context_change():
        # event - before showing an image
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
            self.after_image_iteration()
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
                self.after_context_change()

            # done iterating the images
        return

    def before_invoke(self):
        # about to call the target with a new
        # set of params, save the last set if
        # we ought to. The user may have tagged
        # stuff after viewing it, etc, etc

        def save_last_invocation():
            # we keep track of results, args, tags etc
            # at the invocation level but only move those
            # into the record at the file/image/title level
            # when certain conditions are met

            if self.invocation is None: return
            save = False
            # user requested save,
            # or we are configured to save all
            # or this carousel is running headless (e.g. in a long grid search)
            save = self.invocation.force_save or self.save_all or self.headless
            # or we have an error
            save = save or self.invocation.errored
            # or any of the tags got set on this invocation
            save = save or (len([tag for tag in self.tuner.tag_names if self.invocation[tag] == True]) > 0)

            if save:
                # save this invocation
                # in the file hive,
                # keyed by the args hash
                hive = None
                if self.title in self.carousel_results:
                    hive = self.carousel_results[self.title]
                else:
                    # make a hive for this result
                    hive = self.carousel_results[self.title] = {}
                # get rid of unseemly attributes
                del(self.invocation.force_save)
                hive[self.arg_hash] = self.invocation

            return save

        def init_next_invocation():
            # initialize a complete invocation record
            # with default values here
            self.invocation = PropertyBag()
            # flags
            # tags go here - all set to false initially
            self.invocation.update(self.tag_map)
            # whether there was an error - for convenience in querying
            self.invocation.errored = False
            # errors go here
            self.invocation.error = ""
            # args, and results last - just a visual thing
            self.invocation.args = self.tuner.args
            self.invocation.results = PropertyBag()
            self.invocation.force_save = False

            return

        # # get the results from the UI again
        # self.__capture_result()
        save_last_invocation()
        init_next_invocation()

        # this is the current set of args
        a = self.tuner.args
        inv = json.dumps(a)
        a = hl.md5(inv.encode('utf-8'))
        self.arg_hash = a.hexdigest()

        return

    def after_invoke(self):
        # important safety tip - do not clear out the last invocation record
        # results from tuner will be grabbed if we need to save them
        # for saving later
        self.invocation_counter += 1

        return

    def tag(self, obs:Tags):
        if self.invocation is None: return
        tag = Tags(obs).name
        self.invocation[tag] = True

        return

    # @property
    # def result(self):
    #     return self.invocation.result

    # @result.setter
    # def result(self, val):
    #     # this is a call from userland
    #     self.__capture_result(force=True, val=val)
    #     return

    def capture_result(self, val, *, force=False):

        # return if nothing initialized yet
        if self.invocation is None: return
        # we're getting a copy from tuner
        # - no need to make another
        if force:self.invocation.force_save = True
        if val is None: val = self.tuner.results
        self.invocation.results = val

        return

    def capture_error(self, func_name):
        self.invocation.errored = True
        # format the error string and the call stack
        error = f"{sys.exc_info()[0]} - {sys.exc_info()[1]}"
        l = traceback.format_tb(sys.exc_info()[2])
        # we're always at the top, so get rid of that
        l.pop(0)
        # I like to see the most recent call up at the top
        # - not scroll to the bottom for it
        l = l.reverse()
        # put in the nice error message
        l.insert(0,str(error))
        self.invocation.error = l

        # finally, set the gui status display
        self.tuner.status = f"Error executing {func_name}: {error}"

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
        Use capture to add individual results to the set.
        '''
        ret = True

        fname = self.get_temp_file(suffix=".json")
        try:
            with open(fname,"w") as f:
                f.write(str(self.carousel_results))
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