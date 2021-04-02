from param import param, bool_param, dict_param, list_param
import inspect


class prop:

    def __init__(self, name, cls, cb_read, cb_write=None):
        '''
        Creates an attribute on a given class. The property is added to the class,
        not to an instance of an object as of Python 3.7
        name:       of the property
        cls:        the type() of the object you want a property on. The property gets

        cb_read:    callback to the @property
        cb_write:   (careful with that axe Eugene)
        '''

        self.get_val_method = cb_read
        setattr(cls ,name, self)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            # TODO: shouldn't we pass it the instance?
            return self.get_val_method()
    def __set__(self, instance, value):
        return

class Params():
    '''
    In the default implementation that comes with Tuner, the GUI implementation is openCV highGui
    specific. Extenders should instantiate their own UX controls like lists, checkboxes etc.
    You could do this by overriding the on_ui_ set of methods within the param classes.
    This class should be left as is.
    tuner_ui: The main UI class that users interact with. E.g., an instance of TunerUI.
    '''
    def __init__(self, tuner_ui, func) -> None:

        self.ui = tuner_ui
        self.tuned_params = {}
        self.target_params = {}
        self.target_defaults = {}
        self.aspec = aspec = None

        # put this away here - it will get picked up
        # when packing kwargs
        self.target_defaults["tuner"] = self.ui
        # if this is null routing, there's not a lot to do
        if func is None: return

        # Once the parameters this tracks are fully identified, they should
        # fall into one of two categories: args, and locals. This is done
        # by comparing tracked parameters to the argspec for the target function.

        self.aspec = aspec = inspect.getfullargspec(func)
        # get the args we can do something about- i.e., the NOT var args
        # get the positional args

        if not aspec.args is None: self.target_params = aspec.args.copy()
        # add in the keyword only args : the ones after " *,"
        self.target_params.extend(aspec.kwonlyargs)
        # we don't deal with varargs and varkwargs

        # construct our list of defaults:
        #   1. if the user has set up a default - use it
        #   2. if there's no default - push None.

        # kwonlyargs
        if not aspec.kwonlydefaults is None: self.target_defaults = aspec.kwonlydefaults.copy()
        # for all the other kwonly args, the default should be None
        argdef = {arg:None for arg in aspec.kwonlyargs if arg not in aspec.kwonlydefaults}
        self.target_defaults.update(argdef)

        # positionalargs
        stopat = 0
        ld = 0 if aspec.defaults is None else len(aspec.defaults)
        la = 0 if aspec.args is None else len(aspec.args)
        if ld < la:
            # fewer defaults than args
            # do the first few where default is None

            stopat = la - ld
            argdef = {aspec.args[i]:None for i in range(0,stopat,1)}
            # push the Nones over to our list of defaults
            self.target_defaults.update(argdef)
        # do the rest where a positional arg has a default
        # when all args have defaults, this still woks because stopat = 0
        argdef = {
                    aspec.args[i + stopat]:aspec.defaults[i]
                    for i in range(0,ld,1)
                }
        self.target_defaults.update(argdef)

        # do the following validation after everything else
        # throw if 'tuner' is not found in the argset
        if not "tuner" in self.target_params:
            # the user needs to set up a param called tuner
            raise ValueError(f"There must be a parameter to the tuned function called 'tuner'.")


        # DO NOT get rid of 'self' here
        # if self.target_params[0] == "self":
        #     self.target_params.pop(0)
        #     del self.target_defaults["self"]

        return

    def __contains__(self, key):
        return key in self.tuned_params

    def __getattr__(self, key):
        if key in self.tuned_params:
            p = self.tuned_params[key]
            return p.get_value()
        else:
            return super().__getattr__(key)

    def build_from_call(self, call_is_method, call_args, call_kwargs):
        '''
        This is called from the middle of an intercepted call to
        configure the params on a tuner. Not to be called from userland.
        Uses the args, and kwargs of a call to:
            1. create trackbars
            2. Update default values for parameters mapped out at init.
        For a user to pin an arg value durin tuning, use a default value for the param
        in the formal function signature and leave it out of the build/setup call.

        call_is_method: is this a class method, or a static (True/False)
        args    : args to the function from a setup call
        kwargs  : ditto
        params  : just the positional parameters to the function
        cb      : the main function to tune
        '''
        def create_param(parm, val):
            # Note, the track calls below are being routed via the UI
            # back to us. Deliberate desing choice: give the UI the
            # chance to chime in or do some processing of its own.
            ty = type(val)
            if ty == int:
                # int arg - create a vanilla param
                self.ui.track(parm, max=val)
            elif ty == tuple:
                # also a vanilla arg, but we got a tuple
                # describing max, min, default
                this_max = this_min = this_default = None
                this_max = val[0]
                if len(val) == 2: this_min = val[1]
                if len(val) == 3: this_default = val[2]
                self.ui.track(parm, max=this_max,min=this_min,default=this_default)
            elif ty == bool:
                # its a boolean arg
                self.ui.track_boolean(parm,default=val)
            elif ty == list:
                # track from a list
                # nothing fancy here like display_list etc
                self.ui.track_list(parm,val,return_index=False)
            elif ty == dict:
                # track from a dict/json
                self.ui.track_dict(parm,val, return_key=False)
            else:
                # Something we cannot tune, so curry it.
                # As long as it's not 'self'
                # we can use this value as the default.
                if parm not in ['tuner']: self.target_defaults[parm] = val
                # if parm not in ['self']: self.target_defaults[parm] = val
                # if parm not in ['tuner', 'self']: self.target_defaults[parm] = val

            return

        # At this point, all formal parameters have
        # been identified, and their defaults set up.
        # We are going to use the values in the call
        # to create tuning controls.

        # # we're going to ignore the 'self' param
        # a_off = 1 if call_is_method else 0
        a_off = 0

        # First do the positionionals which must
        # come before the kwonly args in the call
        # Restricting to the length of the formal
        # positional arg set drops the *args out of
        # this equation.
        # There may be positional args in the signature
        # that get converted to kwonly args by the call,
        # so we traverse the shorter list - the rest
        # will be in the call_kwargs
        la = 0 if self.aspec.args is None else len(self.aspec.args)
        lca = 0 if call_args is None else len(call_args)
        stopat = min([la,lca])
        for i in range(a_off, stopat, 1):
            # formal positional parameter name
            parm = self.aspec.args[i]
            # arg passed in to the call that kicks off tuning
            val = call_args[i]
            create_param(parm,val)

        # Next deal with the kwargs in this call if
        # they fall within the kwonly args we plan to handle.
        # The way to pin an arg is to specify the default in the function
        # signature, and omit it from the set up call.
        # Therefore, if it appears here, it's fair game as a tunable param
        usable = [parm for parm in call_kwargs if parm in self.target_params]
        for parm in usable: create_param(parm,call_kwargs[param])

        # done defining what to track

        return
    def update_defaults(self, args:dict):
        '''
        Called to update the value of default arguments.
        Typical usage - specify an invocation's image files.
        This will have no effect on tracked/tuned parameters,
        as those are gathered on arg resolution.

        args: dict in the form param_name:value
        '''
        self.target_defaults.update(args)
        return
    def __track_param(self, name, parm):
        self.tuned_params[name] = parm

        # create an attribute on the tuner facade/ui:
        #   1. with the same name as the tuned param; and
        #   2. binds to the get_value method on the param

        # Do not hold on to this tuner UI prop, it's
        # bound to the UI and is not going anywhere
        # until the UI itself is garbage collected/
        tp = prop(name,type(self.ui),parm.get_value)

        return

    def track(self, name, max, min=None, default=None):
        '''
        Add an int parameter to be tuned.
        Please see the readme for details.
        '''
        t = param(self.ui,name,min=min,max=max,default=default, cb_on_update=self.__update_arg)
        self.__track_param(name,t)

        return

    def track_boolean(self, name, default=False):
        '''
        Add a boolean parameter to be tuned.
        Please see the readme for details.
        '''
        default = False if default is None else default
        t = bool_param(self.ui,name,default=default, cb_on_update=self.__update_arg)
        self.__track_param(name,t)
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
            t = list_param(self.ui,name
                            ,data_list=data_list
                            ,display_list = display_list
                            ,default_item=default_item
                            ,cb_on_update=self.__update_arg
                            ,return_index=return_index
                            )
        self.__track_param(name,t)
        return

    def track_dict(self, name, dict_like, default_item_key=None, return_key=True):
        '''
        Add a list of values to be tuned. Dict keys are displayed as selected values.
        dict_like: Typically a dict or a json object.
        default_item: Initial pick.
        return_key: When True, the selected key is returned, otherwise, its object.
        '''

        if not dict_like is None:
            t = dict_param(self.ui,name
                            ,dict_like=dict_like
                            ,default_item_key=default_item_key
                            ,return_key=return_key
                            ,cb_on_update=self.__update_arg
                            )
            self.__track_param(name,t)
        return

    def __update_arg(self, key, val):
        # kick off a refresh of the UI
        self.ui.on_controls_changed(key,val)

    def get_ranges(self, filter:list=None) -> dict:
        '''
        Returns a dict containing the range of each of the
        trackbars in this tuner, limited by 'filter'

        filter:   When None, ranges are returned for all of the params
        '''
        # if no filter, return all
        if filter is None: filter = list(self.tuned_params.keys())
        # return those ranges that:
        # a. are in our params; if
        # b. they are requested - if

        ranges = {k:param.range for (k,param) in self.tuned_params.items() if k in filter}
        return ranges

    @property
    def theta(self) -> dict:
        '''
        The current set of args to a tuned function.
        '''
        # This looks like a slower way of doing things,
        # especially given the __update_arg just up above;
        # but it actually avoids a whole lot of refresh
        # during trackbar init which can get really
        # expensive out in userland
        ret = {k:param.value for (k,param) in self.tuned_params.items()}

        return ret

    @theta.setter
    def theta(self, val:dict):
        '''
        It's assumed that this is part of a headless op, since values are being set en masse.
        The automatic UI refresh on value change will be skipped.
        '''
        for k in val:
            # k must be a parameter we currently track
            if k in self.tuned_params: self.tuned_params[k].set_value(val[k],headless_op=True)
        return

    @property
    def resolved_args(self) -> dict:
        '''
        Prepares a kwargs object for use in target invocation.
        The returned dict contains all positional and kwonly args
        with tracked values (matched by name), or with defaults
        set by user code. If the user has not set up a default,
        then that parameter has None as its argument.

        This does not handle (*args, **kwargs)
        '''
        kewargs = {}
        theta = self.theta
        # build the kwargs for the target function
        # push parameters for which we have tuned args
        keys_has = [arg for arg in self.target_params if arg in theta]
        kwargs = {arg:theta[arg] for arg in keys_has}

        # get a default if we don't have a tuned arg
        keys_def = [arg for arg in self.target_params if (arg not in theta and arg in self.target_defaults)]
        kwargs.update({arg:self.target_defaults[arg] for arg in keys_def})

        return kwargs

