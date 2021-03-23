# from PropertyBag import PropertyBag
# import cv2
from tb import tb, tb_boolean, tb_dict, tb_list
import copy
class prop:

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

class Args():
    '''
    Implementation is openCV specific. Extenders should instantiate
    their own UX controls like lists, checkboxes etc in the track_x
    methods.
    ui: The main UI class that users interact with;
    e.g., and instance of Tuner.
    '''
    def __init__(self, ui) -> None:

        self.ui = ui
        self.__params = {}

        return
    def __contains__(self, key):
        return key in self.__params

    def __getattr__(self, key):
        if key in self.__params:
            tb = self.__params[key]
            return tb.get_value()
        else:
            return super().__getattr__(key)


    def __add_trackbar(self, name, t):
        self.__params[name] = t
        # create an attribute with the same name as the tracked property
        setattr(type(self.ui) ,name, prop(t.get_value))

        return

    def track(self, name, max, min=None, default=None):
        '''
        Add an int parameter to be tuned.
        Please see the readme for details.
        '''
        t = tb(self.ui,name,min=min,max=max,default=default, cb_on_update=self.__update_arg)
        self.__add_trackbar(name,t)

        return

    def track_boolean(self, name, default=False):
        '''
        Add a boolean parameter to be tuned.
        Please see the readme for details.
        '''
        default = False if default is None else default
        t = tb_boolean(self.ui,name,default=default, cb_on_update=self.__update_arg)
        self.__add_trackbar(name,t)
        return

    def track_list(self, name, data_list, default_item=None, display_list=None, return_index=True):
        '''
        Add a list of values to be tuned.Please see the readme for details.
        data_list: A list of values.
        default_item: Initial pick.
        display_list: An item corresponding to the selected index is used for display in Tuner.
        return_index: When True, the selection index is returned, otherwise the selected item in data_list is returned.
        '''

        if not data_list is None:
            t = tb_list(self.ui,name
                            ,data_list=data_list
                            ,display_list = display_list
                            ,default_item=default_item
                            ,cb_on_update=self.__update_arg
                            ,return_index=return_index
                            )
        self.__add_trackbar(name,t)
        return

    def track_dict(self, name, dict_like, default_item_key=None, return_key=True):
        '''
        Add a list of values to be tuned. Dict keys are displayed as selected values.
        dict_like: Typically a dict or a json object.
        default_item: Initial pick.
        return_key: When True, the selected key is returned, otherwise, its object.
        '''

        if not dict_like is None:
            t = tb_dict(self.ui,name
                            ,dict_like=dict_like
                            ,default_item_key=default_item_key
                            ,return_key=return_key
                            ,cb_on_update=self.__update_arg
                            )
            self.__add_trackbar(name,t)
        return

    def get_ranges(self):
        '''
        Returns a list containing the range of each of the trackbars in this tuner.
        And another of the keys with which this list was butilt.
        There is a positional correspondence between the two lists.
        '''
        # Eventually will get to filtering the set of params we actually take
        keys = list(self.__params.keys())
        ranges = [r for r in [self.__params[key].range() for key in keys]]
        return ranges, keys

    def set_values_headless(self, t, keys):
        '''
        t:      tuple or values
        keys:   list of keys to update
        '''
        # Each tuple t is a combination of trackbar values
        # and will have the same length as keys
        for i in range(len(keys)):
            # skip the UI refresh on every property set
            self.__params[keys[i]].set_value(t[i],headless_op=True)

        return

    def gather(self):
        # this looks like a slower way of doing things,
        # especially given the __update_arg just up above;
        # but it actually avoids a whole lot of refresh
        # during trackbar init which can get really
        # expensive out in userland
        ret = {}
        for key in self.__params:
            ret[key] = self.__params[key].get_value()

        return ret

    def __update_arg(self, key, val):
        # kick off a refresh of the UI
        self.ui.on_controls_changed()

    @property
    def args(self):
        '''
        A dictionary containing all the tuned args, and their current settings.
        '''
        return self.gather()

