import cv2

class tb_prop:

    def __init__(self, get_val_method):
        self.get_val_method = get_val_method
    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            # TODO: shouldn't we pass it the instance?
            return self.get_val_method()
    def __set__(self, instance, value):
        return

class tb:
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
        cv2.setTrackbarMin(self.name, self.tuner.window,self.min)
        # do not trigger the event - things are just getting set up
        # the "begin()" and other methods will reach out for the args anyway
        self.set_value(self.default,True)

    def spec(self):
        # these must be ints, not floats
        return int(self.max), int(self.default)
    def range(self):
        # if the user wants to see a certain min, why default to 0
        # range will not return the 'max' value
        ret = range(self.min, self.max + 1)
        return ret

    def set_value(self,val, headless_op=False):
        '''
        This callback for OpenCV cannot be modified. It's not particularly
        necessary to override this either. You must override get_value
        Call this to generate a "data changed" event. Set headless_op
        to True if you just want to update the value, and the UI, but
        not to trigger the data changed event.
        '''
        # Just put away whatever value you get.
        # We'll interpret (e.g. nulls) when get_value is accessed.
        self._value = val
        # show the new parameter for 10 seconds
        self.tuner.status = self.name + ":" + str(self.get_display_value())
        if headless_op:
            # This call is from code, not from an event generated
            # by a click. So update the UI safely
            # this will not trigger an update event
            try:
                boo = self.on_update
                # turn off event handling
                self.on_update = None
                # the following line sometimes triggers a callback from Qt
                # so this
                cv2.setTrackbarPos(self.name, self.tuner.window,val)
            except:
                pass
            finally:
                # turn event handling back on
                self.on_update = boo
        else:
            # python will delegate to the most derived class
            # the next line will kick off a refresh of the image
            if not self.on_update is None: self.on_update(self.name,self.get_value())
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

    def ticks(self):
        # generator over the range of values
        for i in range(self.max):
            # tick over and set value to new
            # do this "headless" so that we
            # are not refreshing unnecessarily
            self._value = i
            yield i
        return
class tb_boolean(tb):
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
class tb_list(tb):
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
class tb_dict(tb_list):
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
