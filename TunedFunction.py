
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
		# below, until the user exits.

		if self.partial is None:
			# stuff not fully set up yet, but
			# creating a tb triggered a setting
			# of a value which triggered this.
			return

		# At this point, self,partial has:
		# 	'self' bound,
		# 	original kwargs bound
		# 	positional parameters that Tuner can't handle shunted into kwargs
		# now invoke it with the args set by the tuner.
		kargs = tuner.args
		ret = self.partial(**kargs,tuner=tuner)
		return

	def before(self, *args, **kwargs):
		"""Event handler."""
		if self.tuner is None:
			# Each call at this level is a new call to tune.
			# Tuner calls Intercept - not this function.
			# Create the tuner and shunt the curried args into
			# kwargs

			# this gets just the positional parameters
			params = self.argspec.args
			is_method = self.hacky_is_self(args[0])
			self.tuner = Tuner.from_call(is_method, args,kwargs, params,self.intercept)

			# The tuner has set up 'args' with default values at this point
			# Check whether we have any args to track
			# binod - reevauate - for now, just let the call through
			if len(self.tuner.args) == 0 : return True

			# Create a partial of Intercept.
			# Note, doing a partial on a method also curries
			# the self along with it.
			# Tuner cannot manage certain kinds of params. Those
			# have been shunted over to kwargs. Curry these kwargs.
			self.partial = functools.partial(self.target, **kwargs)



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

		return True
	def hacky_is_self(self, arg):
		ret = False
		try:
			qn = self.func_name
			cn = qn[:qn.index('.')]
			atn = str(type(arg))
			ret = atn.endswith("." + cn + "'>")
		except:
			# so janky - just swallow the exception
			pass
		return ret
	def after(self, *args, **kwargs):
		# nothing going on here...
		return