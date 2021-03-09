
import functools
import inspect
import numpy as np
from DecoratorBase import *
# import DecoratorBase
# import DecoratorBase.OutputTo
from Tuner import *

class TunedFunction(DecoratorBase):
	def __init__(self, *args, **kwargs):

		'''
		This is the Decorator version of Tuner. Please see the readme for general use guidance.
		'''

		self.tuner = None
		self.partial = None
		super().__init__(*args, name = "ak.binod.TunedFunction", verbose=True, output_to=OutputTo.Console)

		return

	def on_func_set(self):
		if not inspect.isfunction(self.target):
			raise ValueError("{self.name} can only work with static functions and regular class functions. Not Descriptors, Generators etc.")
		return

	def intercept(self, tuner):
		# Called by the tuner - this is where
		# all the calls from the tuner are going to come
		# while the original call continues to be blocked
		# below. This function will keep being called by
		# Tuner until the user exits.
		# args have been set, time to process

		if self.partial is None:
			# stuff not fully set up yet, but
			# creating a tb triggered a setting
			# of a value which triggered this.
			return

		kargs = tuner.args

		# t = []
		# # Do it this way to ensure the args go in in the order
		# # of the formal parameter declaration
		# # binod - redo this
		# t.extend([these_args[params[i]] for i in range(start,len(params)) ])
		# t = tuple(t)

		# At this point, self,partial has:
		# 	'self' bound,
		# 	original kwargs bound
		# 	positional parameters that Tuner can't handle shunted into kwargs
		# now invoke it with the args set by the tuner.
		ret = self.partial(tuner=tuner,**kargs)
		return

	def setup_tuner(self, tf_args,tf_kwargs):

		# this gets just the positional parameters
		params = self.argspec.args
		# Create a partial of Intercept with the 'self' frozen.
		# Tuner just needs to call it with the `tuner` arg.
		# Note, doing a partial on a method also curries
		# the self along with it.
		cb = functools.partial(self.intercept)
		self.tuner = Tuner(self.func_name,cb_main=cb)

		# See if there's anything we can tune
		# If our target is a bound method, we
		# want to ignore that 'self' - it's
		# going to get bound anyway
		start = 1 if self.ismethod else 0
		for i in range(start,len(tf_args)):
			# formal positional parameter name
			name = params[i]
			# arg passed in to the call that kicks off tuning
			arg = tf_args[i]

			this_max = this_min = this_default = None
			ty = type(arg)
			if ty == int:
				# vanilla arg has to be an int
				this_max = arg
				self.tuner.track(name, max=this_max)
			elif ty == tuple:
				# also a vanilla arg, but we got a tuple
				# describing max, min, default
				this_max = arg[0]
				if len(arg) == 2: this_min = arg[1]
				if len(arg) == 3: this_default = arg[2]
				self.tuner.track(name, max=this_max,min=this_min,default=this_default)
			elif ty == bool:
				# its a boolean arg
				self.tuner.track_boolean(name,default=arg)
			elif ty == list:
				# track from a list
				# nothing fancy here like display_list etc
				self.tuner.track_list(name,arg,return_index=False)
			elif ty == dict:
				# track from a dict/json
				self.tuner.track_dict(name,arg, return_key=False)
			else:
				# Probably None. At any rate, something we cannot tune
				# so curry it. Shunt it over to the kwargs for target.
				tf_kwargs[name] = arg

		# done defining what to track
		# # self will get curried along with kwargs
		# self.curry = functools.partial(self.target, args[0], **kwargs)

		# curry just the kwargs which we do not touch
		# 'self' will get curried along with kwargs
		self.partial = functools.partial(self.target, **tf_kwargs)
		# can we see function variables?
		return


	def before(self, *args, **kwargs):
		"""Event handler."""

		# Each call at this level is a new call to tune.
		# Tuner calls Intercept - not this function.
		# Create the tuner and shunt the curried args into
		# kwargs
		self.setup_tuner(args, kwargs)
		# The tuner has set up 'args' with default values at this point
		# Check whether we have any args to track
		# binod - reevauate - for now, just let the call through
		if len(self.tuner.args) == 0 : return True



		# Call the begin() method to start up the tuner gui
		# We do not need to explicitly send in an image, since
		# it will be one of the parameters that we are just
		# currying in - along with all the others that
		# Tuner cannot handle. This is what the loop looks like:
		# 1. we call tuner.begin()
		# 2. tuner calls this.intercept()
		# 3. tuner.intercept() calls the target function
		# 4. target returns, intercept returns, and then we go back to 2
		# Steps 2 to 4 loop until the user breaks out.

		self.tuner.begin(None)

		# The user exited the tuning session, so we have handled this call to target.
		# We do not want this particular invocation passed on to target.
		# it has been invoked in a special manner just to start the tuning process.
		return False

	def after(self, *args, **kwargs):
		# nothing going on here...
		return