from .DecoratorBase import DecoratorBase, OutputTo

class DecoratorSample(DecoratorBase):
	def __init__(self, *args, **kwargs):
		'''
		This is a sample "do-nothing" decorator. Use it as a template to roll your own.
		'''
		# call super() after you done with your own init
		super().__init__(*args, name = "akbinod.DecoratorSample"
								, verbose=False
								, output_to=OutputTo.Console)

		return

	def on_func_set(self):
		#Event: when your target function is finalized
		return

	def before(self, *args, **kwargs):
		# Event: when the target function is invoked by userland code,
		# and just before we invoke it. Return false to cancel target
		# invocation.
		# args, kwargs are those being passed to target.

		return

	def after(self, *args, **kwargs):
		# Event: when the target function is invoked by userland code,
		# and just after it exits, but before we return control to user code.
		# args, kwargs are those being passed to target.

		return
