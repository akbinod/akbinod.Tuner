import numpy as np
import matplotlib.pyplot as plt
import cv2
import copy
import os
import json
import tempfile

HIGHLIGHT_COLOR = (173,255,47)
HIGHLIGHT_THICKNESS_LIGHT = 1
HIGHLIGHT_THICKNESS_HEAVY = 2
PUT_TEXT_FONT = cv2.FONT_HERSHEY_PLAIN
PUT_TEXT_SMALL = 0.7
PUT_TEXT_NORMAL = 1.0
wip_dir = "."

class tb_prop:
    def __init__(self, get_val_method):
        self.get_val_method = get_val_method
    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return self.get_val_method()
    def __set__(self, instance, value):
        return

class Tuner:
    class __tb:

        def __init__(self, tuner, name, *, max, min, default, cb_on_update=None) -> None:
            if max is None: raise ValueError("Must have 'max' to define a regular trackbar.")
            self.tuner = tuner
            self.on_update = cb_on_update
            self.name = name
            self.max = max
            self.min = 0 if min is None else (min if min >= 0 else 0)
            self.default = self.min if default is None else (self.min if default <= self.min or default > self.max else default)
            self._value = self.default
            self.trackbar = cv2.createTrackbar(name, tuner.window
                                                ,self.default
                                                ,self.max
                                                ,self.set_value)
            # create an attribute with the same name as the tracked property
            setattr(Tuner,name, tb_prop(self.get_value))
            # do not trigger the event - things are just getting set up
            # the "begin()" and other methods will reach out for the args anyway
            self._value = self.default
            # self.set_value(self.default)
        def spec(self):
            # these must be ints, not floats
            return int(self.max), int(self.default)

        def set_value(self,val):
            '''
            This callback for OpenCV cannot be modified. It's not particularly
            necessary to override this either. You must override get_value
            '''
            # Just put away whatever value you get.
            # We'll interpret (e.g. nulls) when get_value is accessed.
            self._value = val
            # python will delegate to the most derived class
            # the next line will kick off a refresh of the image
            if not self.on_update is None: self.on_update(self.name,self.get_value())
            # show the new parameter for 10 seconds
            try:
                cv2.displayStatusBar(self.tuner.window,
                                    self.name + ":" + str(self.get_display_value())
                                    ,10_000
                                )
            except:
                pass
            return

        def get_value(self):
            '''
            Must be overridden by derivers.
            Provides a class specific interpretation of trackbar values

            '''
            # guard for None
            ret = self.min if self._value is None else self._value
            # guard for bad input by the user
            ret = self.min if ret < self.min else self._value
            return ret

        def get_display_value(self):
            '''
            Override this if you have a special formatting to apply
            '''
            return self.get_value()
    class __tb_boolean(__tb):
        def __init__(self, tuner, name, *, default=False, cb_on_update=None) -> None:
            '''
            Represents True/False values.
            '''
            default=0 if default == False else 1
            super().__init__(tuner, name,min=0,max=1,default=default,cb_on_update=cb_on_update)

        def get_value(self):
            ret = super().get_value()
            ret = False if ret <= 0 else True
            return ret
    class __tb_list(__tb):
        def __init__(self, tuner, name, *, data_list, display_list=None, default_item=None, return_index=True, cb_on_update=None) -> None:
            '''
            Represents a list of values. The trackbar is used to pick the list index
            and the returned value is the corresponding item from the list.
            When display_list is provided, then the corresponding value from it
            is used in Tuner's displays - but not returned anywhere.
            '''
            if data_list is None: raise ValueError("Must have data_list to define a list trackbar.")
            self.__data_list = data_list
            self.__display_list = display_list
            max = min = default = 0
            if not data_list is None:
                max = len(data_list) - 1
                default = 0
                if not default_item is None:
                    if default_item in data_list:
                        # user specified a list item
                        default = data_list.index(default_item)
                    elif isinstance(default_item,int) and default_item < len(data_list):
                        # user specified a list index
                        default = default_item

            if not display_list is None:
                if len(data_list) != len(display_list):
                    raise ValueError("Display list must match data list in length.")

            self.__return_index = return_index
            super().__init__(tuner, name, max=max, min=0, default=default
                            , cb_on_update=cb_on_update)

        def get_value(self):
            ret = super().get_value()
            if not self.__return_index:
                ret = self.__data_list[ret]
            return ret

        def get_display_value(self):

            if self.__display_list is None:
                ret = self.get_value()
            else:
                ret = super().get_value()
                ret = self.__display_list[ret]
            return ret
    class __tb_dict(__tb_list):
        def __init__(self, tuner, name, dict_like, *, default_item_key, return_key=True, cb_on_update) -> None:
            '''
            Like a list tracker. Keys become data items, and associated data become display items.
            When return_key is True: you get the key back
            When return_key is False: you get the object relating to key

            '''
            self.__return_key = return_key
            self.data = dict_like
            try:
                # make a list of the keys
                display_list = list(dict_like.keys())
                # and a list of values
                data_list = [obj for obj in [dict_like[key] for key in dict_like]]
                assert data_list is not None and len(data_list) > 0
            except:
                raise ValueError("Dict like object must be populated and support key iteration.")

            try:
                if default_item_key is None: default_item_key = display_list[0]
                assert  default_item_key in dict_like
            except:
                raise ValueError("Default item not found in dict_like.")

            # given the setup in init, we want the list index back
            super().__init__(tuner, name
                                , data_list=data_list
                                , display_list=display_list
                                , default_item=default_item_key
                                , cb_on_update=cb_on_update
                                , return_index=True)

            return
        def get_value(self):
            key_index = super().get_value()
            key =  list(self.data.keys())[key_index]
            if self.__return_key:
                ret =key
            else:
                ret = self.data[key]
            return ret

    def __init__(self, name, *
                , cb_main = None
                , cb_downstream = None
                ):
        '''
        Please see the readme.
        cb_main: The target of tuning.
        cb_downstream: Similar to cb_main, this is a downstream function to be called after cb_main.
        This is not tuned, but it can display its results in a downstream window.
        '''

        self.__window_name = name
        # provided later
        self.__unprocessed_image = None

        self.__args = {}
        self.__params = {}
        # the safe default
        self.__calling_main = True

        # primary function to tune with its attendant image and other params
        self.__cb_main = cb_main
        # result of tuning
        self.__image_main = None
        self.__thumbnail_main = None
        self.__results_main = None
        self.__image_file_name = None
        # cv2.WINDOW_NORMAL|
        # we need this window regardless of there the user wants a picture in it
        cv2.namedWindow(self.window,cv2.WINDOW_KEEPRATIO|cv2.WINDOW_GUI_EXPANDED)

        # optional secondary function which is passed
        # the tuned parameters and the image from primary tuning
        self.__cb_downstream = cb_downstream
        self.__image_downstream = None
        self.__results_downstream = None
        self.__thumbnail_downstream = None
        if not cb_downstream is None:
            # we have 2 pictures to show
            cv2.namedWindow(self.downstream_window,cv2.WINDOW_KEEPRATIO|cv2.WINDOW_GUI_EXPANDED)

        return

    def __del__(self):
        cv2.destroyWindow(self.window)
        if not self.__cb_downstream is None:
            cv2.destroyWindow(self.downstream_window)
        pass

    def track(self, name, max, min=None, default=None):
        '''
        Add an int parameter to be tuned.
        Please see the readme for details.
        '''
        tb = Tuner.__tb(self,name,min=min,max=max,default=default, cb_on_update=self.__update_arg)
        self.__params[name] = tb
        return
    def track_boolean(self, name, default=False):
        '''
        Add a boolean parameter to be tuned.
        Please see the readme for details.
        '''
        default = False if default is None else default
        tb = Tuner.__tb_boolean(self,name,default=default, cb_on_update=self.__update_arg)
        self.__params[name] = tb
        return
    def track_list(self, name, data_list, *, default_item=None, display_list=None, return_index=True):
        '''
        Add a list of values to be tuned.Please see the readme for details.
        data_list: A list of values.
        default_item: Initial pick.
        display_list: An item corresponding to the selected index is used for display in Tuner.
        return_index: When True, the selection index is returned, otherwise the selected item in data_list is returned.
        '''

        if not data_list is None:
            tb = Tuner.__tb_list(self,name
                                    ,data_list=data_list
                                    ,display_list = display_list
                                    ,default_item=default_item
                                    ,cb_on_update=self.__update_arg
                                    ,return_index=return_index
                                    )
            self.__params[name] = tb
        return
    def track_dict(self, name, dict_like, *, default_item_key=None, return_key=True):
        '''
        Add a list of values to be tuned. Dict keys are displayed as selected values.
        dict_like: Typically a dict or a json object.
        default_item: Initial pick.
        return_key: When True, the selected key is returned, otherwise, its object.
        '''

        if not dict_like is None:
            tb = Tuner.__tb_dict(self,name
                                    ,dict_like=dict_like
                                    ,default_item_key=default_item_key
                                    ,return_key=return_key
                                    ,cb_on_update=self.__update_arg
                                    )
            self.__params[name] = tb
        return

    def __refresh(self):

        def show_main():
            # call the user proc that does the calc/tuning
            self.__calling_main = True
            self.__cb_main(tuner=self)

            img = self.main_image
            if not img is None:
                img = self.__insert_thumbnail(img, self.__thumbnail_main)
                # show the main image here
                cv2.imshow(self.window, img)
                try:
                    # user does not have the Qt backend installed. Pity.
                    cv2.displayOverlay(self.window, self.main_results,delayms=1_000)
                except:
                    pass

            return
        def show_downstream():
            if not self.__cb_downstream is None:
                #  call the user proc that does the secondary processing/application
                self.__calling_main = False
                # Always send in a copy of the "pristine" image/ We're not in the
                # business of inserting ourself into the workflow of another codebase
                # so we will not take results from one function and pass them to another
                self.__cb_downstream(tuner = self)
                try:
                    cv2.displayOverlay(self.downstream_window,
                                        self.downstream_result
                                        ,delayms=10_000)
                except:
                    # ignore these
                    pass

                img = self.downstream_image
                if not img is None:
                    # show it in the secondary window
                    img = self.__insert_thumbnail(self.downstream_image, self.__thumbnail_downstream)
                    cv2.imshow(self.downstream_window, img)

                return

        # # things not fully set up yet
        # if self.__unprocessed_image is None: return
        show_main()
        show_downstream()

        return
    def __show(self, img, img_title="",delay=0):
        '''
        delay is only set in review/creep mode; 0 means "until the user does something."
        '''
        cancel = False
        # this may be None and that is OK
        self.__unprocessed_image = img
        self.__image_title = img_title
        # the first step in the message pump
        self.__refresh()

        while(1):
            # wait forever until a key is pressed
            k = cv2.waitKey(delay) #& 0xFF
            if k == 120:
                # F2 pressed = save image
                self.__save_image(self.__image_title)
                # don't exit just yet - clock starts over
                continue
            elif k == 99:
                # F3 - dump params
                self.__save_results(self.__image_title)
                # don't exit just yet - clock starts over
                continue
            else:
                # any other key - done with this image
                # cancel the stack if the Esc key was pressed
                cancel = (k==27)
                break
        return not cancel

    def review(self, fnames:list, img_title=None,delay=2_000):
        '''
        Does a 2 second review of each image in the list unless interrupted.
        Sit back and enjoy the slideshow, saving image/result files
        as you go. Typically used in your regression test.
        1. create a tuner and set defaults to the best of your knowledge
        2. call this to flip through the images from your project
        Leave img_title null to use the name of the file being shown.
        '''
        if isinstance(fnames,list):
            # we got a list of names
            for fname in fnames:
                img = cv2.imread(fname)
                if img is None:
                    raise ValueError(f"Tuner could not find file {fname}. Check full path to file.")
                title = os.path.split(fname)[1] if img_title is None else img_title
                ret  = self.__show(img,title,delay)
                if not ret: break
        else:
            # we got a single image
            img = fnames
            title = img_title
            ret  = self.__show(img,title,delay)
        return ret

    def begin(self, fnames:list, img_title=None):
        '''
        Display the Tuner window.
        fnames: See readme. can be None, a single image, or a list of file names.
                When a list, each image is processed until interruped via the keyboard.
                Hit Esc to cancel the whole stack.
        img_title: When none, it will be inferred from the image file name.
        '''

        return self.review(fnames=fnames,img_title=img_title,delay=0)

    def save_image(self, fname=None):
        '''
        Saves the current image to fname, falling back to image_title, and temp file name.
        '''
        if fname is None: fname = self.__image_title
        self.__save_image(fname)

    def save_results(self, fname):
        '''
        Saves the set of results to fname, falling back to {image_title}.json, and temp file name.
        The fille includes the last set of results set via the .results attribute, and the current
        args (hyper-parameter values).
        '''
        if fname is None: fname = self.__image_title
        self.__save_results(fname)

    def __save_image(self,fname):
        if fname is None or fname == "":
            fname = Tuner.get_temp_file(suffix=".tuned.png")
        else:
            fname = Tuner.wip_dir + self._img_title + "tuned.png"
        cv2.imwrite(fname,self.__image_main)
        if not self.downstream_image is None:
            fname = fname.replace(".tuned.", ".downstream.")
            cv2.imwrite(fname,self.downstream_image)
        return

    def __save_results(self,fname):
        if fname is None or fname == "":
            fname = Tuner.get_temp_file(suffix=".json")
        else:
            fname = Tuner.wip_dir + self._img_title + ".json"
        Tuner.dump_json(self.results,fname=fname)

        return

    @property
    def __image_title(self):
        return self.__image_file_name

    @__image_title.setter
    def __image_title(self,val):

        if not (val is None or val == ""):
            self.__image_file_name = val
            cv2.setWindowTitle(self.window,val)
            if not self.__cb_downstream is None:
                cv2.setWindowTitle(self.downstream_window, "Downstream: " + val )
        return

    def __update_arg(self, key, val):
        self.__args[key] = val
        self.__refresh()
    @property
    def args(self):
        '''
        A dictionary containing all the tuned args, and their current settings.
        '''
        # this looks like a slower way of doing things,
        # especially given the __update_arg just up above;
        # but it actually avoids a whole lot of refresh
        # during trackbar init which can get really
        # expensive out in userland
        # Also, don't use a comprehension to replace - just update
        for key in self.__params:
            self.__args[key] =  self.__params[key].get_value()

        return self.__args

    @property
    def main_image(self):
        '''
        The image as updated by the main function - the target of tuning.
        '''
        return self.__image_main

    @property
    def main_results(self):
        '''
        Results as set by the main function - the target of tuning.
        '''
        if self.__results_main is None:
            self.__results_main = {}
        return self.__results_main

    @property
    def downstream_image(self):
        '''
        The image as updated by the downstream function.
        '''

        return self.__image_downstream

    @property
    def downstream_results(self):
        '''
        The results as set by the downstream function.
        '''
        return self.__results_downstream

    @property
    def results(self):
        '''
        Returns json which includes the image title, the current state of tuned args, the results set by main, and the results set by downstream.
        '''
        # return the combined results, and add args in there for good measure
        j = {}
        j["image_title"] = self.__img_title
        j["args"] = self.args
        j["main"] = self.main_results
        j["downstream"] = self.downstream_results
        return j

    @results.setter
    def results(self, val):
        if self.__calling_main:
            self.__results_main = val
        else:
            # the object setting this is the downstream func
            self.__results_downstream = val

    @property
    def image(self):
        '''
        Always return a fresh copy of the user supplied image.
        '''
        return np.copy(self.__unprocessed_image)

    @image.setter
    def image(self, val):
        if self.__calling_main:
            self.__image_main = val
        else:
            # the object setting this is the downstream func
            self.__image_downstream = val

    @property
    def window(self):
        '''
        Window title.
        '''
        return self.__window_name

    @property
    def downstream_window(self):
        '''
        Downstream window title.
        '''
        return self.window + " :Downstream"
    @property
    def thumbnail(self):
        '''
        This image is inserted into the upper left hand corner of the main image. Keep it very small.
        '''
        if self.__calling_main:
            return self.__thumbnail_main
        else:
            return self.__thumbnail_downstream


    @thumbnail.setter
    def thumbnail(self,val):
        # this is the current thumbnail
        if self.__calling_main:
            self.__thumbnail_main = val
        else:
            self.__thumbnail_downstream = val
        return

    def __insert_thumbnail(self, mn, tn):
        '''
        mn: main image to insert the thing into
        '''
        # do not use the property - use what has been set
        if not tn is None:
            # Draw a bounding box 1 pixel wide in the top left corner.
            # The box should have enough pixels for all of the image
            bt = 1
            tl = (3,3)
            br = (tl[0] + tn.shape[1] + (2*bt), tl[1] + tn.shape[0] + (2*bt))
            cv2.rectangle(mn,tl,br,Tuner.HIGHLIGHT_COLOR,thickness=bt)
            # adjust for offset border
            tl = (tl[0] + bt, tl[1] + bt)
            x,x1,y,y1 = Tuner.image_to_array_indices(tl,img_shape=tn.shape)

            tn_dim = np.ndim(tn)
            if np.ndim(mn) == 3:
                mn[x:x1,y:y1, 0] = tn if tn_dim == 2 else tn[:,:,0]
                mn[x:x1,y:y1, 1] = tn if tn_dim == 2 else tn[:,:,1]
                mn[x:x1,y:y1, 2] = tn if tn_dim == 2 else tn[:,:,2]
            else:
                mn[x:x1,y:y1] = tn if tn_dim == 2 else cv2.cvtColor(tn,cv2.COLOR_BGR2GRAY)
        return mn

    @staticmethod
    def tuner_from_json(name, cb_main:function, cb_downstream:function, json_def:dict):
        '''
        Returns an instance of Tuner configured to the json you pass in.
        '''
        tuner = Tuner(name,cb_main=cb_main,cb_downstream=cb_downstream)
        keys = list(json_def.keys())
        for key in keys:
            # each is a new trackbar
            this = json_def[key]
            # what type
            this_type = this["type"] if "type" in this else None
            # starting value
            default = this["default"] if "default" in this else None

            if this_type is None:
                min = this["min"] if "min" in this else None
                max = this["max"] if "max" in this else None
                tuner.track(key, max, min, default)
            elif this_type in ["bool", "boolean"]:
                tuner.track_boolean(key,default)
            elif this_type == "list":
                data_list = display_list = None
                if "data_list" in this: data_list = this["data_list"]
                if "display_list" in this: display_list = this["display_list"]
                tuner.track_list(key,data_list,default,display_list=display_list)
            # elif this_type == "json":
            #     TOO RECURSIVE

        return tuner

    @staticmethod
    def minimal_preprocessor( window_title="Minimal Preprocessor", *, cb_downstream = None, thumbnail=None):
        '''
        Tuning the pre-processing is a common task in CV. Use this method to
        get a minimal (you will need more for your projects) preprocessing
        tuner that meets some goals like blurring, canny edge detection, etc.
        Pass it the downstream function that consumes the tuned parameters
        to meet your project goals; e.g., finding lines, or matching templates.
        Call the begin() method on the returned object, passing it your image.

        You can use this to develop pre-processing presets. Get to a point
        with the trackbars that you like, and then save the results to file
        to review/copy into your code.

        This function could just as easily have made calls to the track_ set of
        trackbar creation functions. It takes the json def approach as an
        illustration. Use this tuner to get your image to a good stage of
        pre-processing, and save the results. Use the results json in your code.
        '''

        def tune(tuner:Tuner):
            res = {}
            img = tuner.image
            # we got nothing to say about preprocessing
            res["preprocessing"] = copy.deepcopy(tuner.args)
            tuner.results = res

            # get the processed image
            tuner.image = Tuner.preprocess_to_spec(img,tuner.args)
            # process the thumbnail if one exists
            if not thumbnail is None:
                tuner.thumbnail = Tuner.preprocess_to_spec(thumbnail,tuner.args)
            return

        json_def={
        "img_mode":{
            "type":"list"
            ,"data_list":["grayscale","blue","green","red"]
            ,"default":"grayscale"
            }
        ,"blur":{
            "type":"boolean"
            ,"default":True
            }
        ,"blur_ksize":{
            "type":"list"
            ,"data_list":[(3,3), (5,5), (7,7)]
            ,"default":0
            }
        ,"blur_sigmaX":{
            "max":20
            ,"min":0
            ,"default":4
            }
        ,"contrast":{
            "type":"boolean"
            ,"default":False
            }
        ,"contrast_kept_val":{
            "max":255
            ,"default":0
            }
        ,"contrast_flip":{
            "type":"boolean"
            ,"default":False
            }
        ,"detect_edge":{
            "type":"boolean"
            ,"default":False
            }
        ,"edge_threshold1":{
            "max":200
            ,"default":150
            }
        ,"edge_threshold2":{
            "max":200
            ,"default":50
            }
        ,"edge_apertureSize":{
            "type":"list"
            ,"data_list":[3,5,7]
            }
        }

        tuner = Tuner.tuner_from_json(name=window_title
                                        ,cb_main= tune
                                        ,cb_downstream=cb_downstream
                                        ,json_def= json_def)


        return tuner

    @staticmethod
    def bin_these(iterable_1d,wt="Bin These"):
        plt.hist(iterable_1d,bins='auto',)
        plt.title(wt +  ":auto binned")
        plt.show()
        hist = bins = mid = None
        try:
            hist, bins = np.histogram(a=iterable_1d)
            # print(hist,bins)
            mid = bins[np.argmax(hist)]
        except:
            # not all data is amenable to this
            pass
        return hist,bins,mid


    @staticmethod
    def get_temp_file(dir=wip_dir, suffix=".png"):
        # we're just going to leave this file lying around
        _, full_path_name = tempfile.mkstemp(suffix=suffix,dir=dir,text=True)

        return full_path_name

    @staticmethod
    def get_file_path(dir, fname, ext=""):
        duh = os.path.split(fname)
        if duh[0] == "":
            # no path provided in fname
            if dir is None or dir == "":
                dir = "./"
            fname = dir + fname


        duh = os.path.splitext(fname)
        if duh[1] == "":
            # no ext provided
            fname += ext
        else:
            # fname has an extension
            if not ext is None and ext != "":
                # need to overwrite the extension
                fname = duh[0] + ext
        return fname

    @staticmethod
    def dump_json(j , dir = wip_dir, fname="dump_json.json", mode = 'a+'):

        fname = get_file_path(dir,fname,".json")
        try:
            with open(fname,mode) as f:
                try:
                    f.write(json.dumps(j))
                except:
                    # could not get a formatted output
                    f.write(str(j))
                f.write("\n")
        except:
            # dont let this screw anything else up
            pass
        return

    @staticmethod
    def dump_to_file(vals:np.array, *, dir = wip_dir, fname="", mode = 'w'):
        if fname == "":
            fname = get_temp_file(suffix=".csv")
        else:
            fname = get_file_path(dir,fname, ".csv")

        with open(fname, mode) as f:
            for i in range(vals.shape[0]):
                # f.write(f"a[{i}] = [" )
                srow = ""
                if vals.ndim > 1:
                    for j in range(vals.shape[1]):
                        if srow != "":
                            srow += ","
                        srow += str(vals[i,j])
                else:
                    srow = vals[i]
                f.writelines(f"{srow}\n")
