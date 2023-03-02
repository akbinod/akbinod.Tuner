import cv2
from enum import Enum
class param():
    '''
    This class should be left as is.

    Pass in the UI classs that implements the on_control_x set of
    callbacks that this delegates to.

    '''
    def __init__(self, ui, name, *, max, min, default) -> None:
        if max is None: raise ValueError("Must have 'max' to define a regular trackbar.")
        self.ui = ui
        # We want this ref instead of directly calling an UI
        # interface method so that update propagation can be
        # turned on and off as needed.
        self.on_update = ui.on_control_changed
        self.name = name
        self.max = max
        self.min = 0 if min is None else (min if min >= 0 else 0)
        self.default = self.min if default is None else (self.min if default <= self.min or default > self.max else default)
        self._value = self.default

        # init UI
        ui.on_control_create(self)

        # do not trigger the event - things are just getting set up
        # the "begin()" and other methods will reach out for the args anyway
        self.set_value(self.default,True)
        return


    def spec(self):
        # these must be ints, not floats
        return int(self.max), int(self.default)

    @property
    def range(self):

        # range will not return the 'max' value
        ret = range(self.min, self.max + 1)
        return ret

    @property
    def value(self):

        return self.get_value()

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
        # # this gives derivers a chance to finesse the value
        # val = self.get_value()
        if headless_op:
            # This call is from code, not from an event generated
            # by a click. So update the UI without triggerin an update event
            boo = self.on_update
            try:
                self.on_update = None
                self.ui.on_control_update(self,val)
            finally:
                self.on_update = boo

        else:
            # python will delegate to the most derived class
            # the next line will kick off a refresh of the image
            if not self.on_update is None: self.on_update(self,self.get_value())
        return

    def get_value(self):
        '''
        Must be overridden by derivers creating new types of params.
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

class bool_param(param):
    def __init__(self, ui, name, *, default=False) -> None:
        '''
        Represents True/False values.
        '''
        default=0 if default == False else 1
        super().__init__(ui, name,min=0,max=1,default=default)

    def get_value(self):
        ret = super().get_value()
        ret = False if ret <= 0 else True
        return ret

class list_param(param):
    def __init__(self, ui, name, *, data_list, display_list=None, default_item=None, return_index=True) -> None:
        '''
        Represents a list of values. The trackbar is used to pick the list index
        and the returned value is the corresponding item from the list.
        When display_list is provided, then the corresponding value from it
        is used in Tuner's displays - but not returned anywhere.
        '''
        if data_list is None: raise ValueError("Must have data_list to define a list trackbar.")
        self.data_list = data_list
        self.display_list = display_list
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
        else:
            # let's create one
            self.display_list = []
            self.guess_display_list()
        self.__return_index = return_index
        super().__init__(ui, name, max=max, min=0, default=default)
    def guess_display_list(self):
        for li in self.data_list:
            val = "<unknown>"
            if isinstance(li,dict):
                # just add the first key in there - the user will soon get the drift
                if len(li.keys()):
                    l = list(li.keys())
                    if len(l) > 0:val = li[l[0]]
            elif isinstance(li,list):
                val = li[0]
            else:
                val = str(li)
            self.display_list.append(val)
        return
    def get_value(self):
        ret = super().get_value()
        if not self.__return_index:
            ret = self.data_list[ret]
        return ret

    def get_display_value(self):

        if self.display_list is None:
            ret = self.get_value()
        else:
            ret = super().get_value()
            ret = self.display_list[ret]
        return ret

class dict_param(list_param):
    def __init__(self, ui, name, dict_like, *, default_item_key, return_key=True) -> None:
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
            # data_list = [obj for obj in [dict_like[key] for key in dict_like]]
            data_list = [dict_like[key] for key in dict_like]
            assert data_list is not None and len(data_list) > 0
        except:
            raise ValueError("Dict like object must be populated and support key iteration.")

        try:
            if default_item_key is None: default_item_key = display_list[0]
            assert  default_item_key in dict_like
        except:
            raise ValueError("Default item not found in dict_like.")

        # given the setup in init, we want the list index back
        super().__init__(ui, name
                            , data_list=data_list
                            , display_list=display_list
                            , default_item=default_item_key
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

class file_param(param):
    def __init__(self, ui, name, title, invoke_on_change) -> None:
        '''
        Represents a file name.
        '''
        self.title = title
        self.fileName = None
        self.invoke_on_change = invoke_on_change
        super().__init__(ui, name,max=0, min=0, default=0)

    def get_value(self):
        if self._value == self.min: return None
        return self._value
    def set_value(self,val, headless_op=False):
        # we're not looking up an index or anything - just our fileName
        return super().set_value(self.fileName,headless_op)
class enum_param(list_param):
    def __init__(self, ui, name, *, enum:Enum) -> None:
        '''
        Represents a list of values derived from an Enum.
        '''
        if enum is None: raise ValueError("Must have an Enum to track.")

        self.enum = enum
        data_list = [e.name for e in enum]
        display_list = data_list

        super().__init__(ui, name
                        , data_list = data_list
                        , display_list = display_list
                        # pick the first item by default
                        , default_item=0
                        , return_index= False)
    def get_value(self):
        # we just display the enum.name, so that is what we will get back
        ret = super().get_value()

        return self.enum[ret]
