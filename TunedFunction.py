
import functools
import inspect
import numpy as np
from core.DecoratorBase import *
from TunerUI import TunerUI
from ThetaUI import ThetaUI

class TunedFunction(DecoratorBase):
	def __init__(self, *args, **kwargs):
		'''
		This is the Decorator version of Tuner. Please see the readme for general use guidance.
		'''
		self.tuner = None
		self.inits = kwargs
		super().__init__(*args, name = "ak.binod.TunedFunction", verbose=True, output_to=OutputTo.Console)

		return

	def on_func_set(self):
		if not inspect.isfunction(self.target):
			raise ValueError("{self.name} can only work with static functions and regular class functions. Not Descriptors, Generators etc.")
		return

	def before(self, *args, **kwargs):
		"""
		Event handler. The very first call is from userland,
		and we use that to set up the tuner.
		Each subsequent call is a new call to tune, and we
		let those through as is.
		"""
		if self.tuner is None:
			# First time through: create and kick off the tuner
			# these are params to not mess with - just pass them in unchanged to the target function
			pinned_params = {} if "pinned" not in self.inits else self.inits["pinned"]
			# self.tuner = TunerUI(self.target,pinned_params=pinned_params)
			self.tuner = TunerUI(self.target,pinned_params=pinned_params)

			is_method = self.hacky_is_self(args[0]) if len(args) > 0 else False
			self.tuner.build_from_call(is_method, self.inits, args, kwargs)

			# Call the begin() method to start up the tuner gui
			# Tuner will take care of the args
			# 1. we call tuner.begin()
			# 2. tuner calls target on every arg change
			# 3. target returns, and then we go back to 2
			# Steps 2 to 3 loop until the user breaks out.
			self.tuner.begin()


			# The user exited the tuning session, so we have handled
			# this call to target. We do not want this particular
			# invocation passed on to target, since it was the
			# set up call invoked in a special manner just to start
			# the tuning process.
			return False

		return True

	def after(self, *args, **kwargs):
		# nothing going on here...
		return