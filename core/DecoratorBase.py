import functools
from enum import Enum, auto
import inspect

class OutputTo(Enum):
	Console = auto(),
	Property = auto()

def _wrap(this_decorator):
	functools.wraps(this_decorator.target)
	def call_proxy(*args, **kwargs):
		err = None
		value = None
		cancel = False
		#this = kwargs["this"]
		try:
			#call the before event handler
			cancel = not this_decorator.before(*args, **kwargs)

			if not cancel:
				#invoke the real target
				value = this_decorator.target(*args, **kwargs)
		except Exception as error:
			err = error
		finally:
			# call the after function - regardless of whether
			# the target invocation was cancelled or not.
			this_decorator.after(value)
			#if verbose and not err is None:
			#	logger.exception(err)
			if not err is None:
				raise err
		return value
	return call_proxy

class DecoratorBase():
	def __init__(self, *args, name = "akbinod.DecoratorBase", verbose= True, output_to = OutputTo.Console):
		'''
		Decorates static functions as well as class methods.
		PSA: Derivers should take their entire initialization from
		kwonly args:
			1. Do not take/rely on positional args other than *args
			2. Let this base class handle *args.
			3. Finish your init before calling this, then wait for
				the on_* events.

		__init__ is invoked by py when the decorator is first
		encounterd by py in userland code - not when the cleint/target
		function is invoked. E.g., when you run any function in a file
		in which this (or a derived) decorator appears.
		If the decorator __init__ takes no positional arguments
			1. Py sends in a ref to the target func in args[0]
			2. Py invokes __call__ without a ref to the target func
			but expects to receive a proxy to the target function
		If the decorator __init__ takes positional params:
			1. py sends in the init params to __init__
			2. py sends in a ref to the target func in its first invocation
			of __call__ , and expects the target proxy.

		Once __call__ returns the target proxy, all target function
		invocations are routed to the target proxy. This base class
		controls that proxy, and derivers get 2 events raised by base:
			1. before - before the call is dispatched to the target
			2. after - after the target completes its call

		All of the init, the target determination the invocation of __call__
		etc happens before Py is done looking at all the functions in the
		file. Finally, when the target is invoked, our proxy is already standing
		by to take that call.
		Derivers only need to provide an __ini__ and override the before() method.
		Or the after(). Or both.
		'''

		self.name = name
		self.output_to = output_to
		self.verbose = verbose
		#get things set up
		self.__target = None
		self.__argspec = None
		# Not expecting any positional arguments, but a deriver
		# may pass some in, or Py might.
		if len(args) > 0 and callable(args[0]):
			# py sent us the target function
			# this should kick off a chain of events
			self.target == args[0]

	def __call__( self, func):
		# This should only ever get one call.
		# Once we return the wrapper, subsequent
		# calls will go to the wrapper.
		self.target = func

		# return the proxy function that py should call
		# when the target function is called from userland
		return _wrap(self)


	@property
	def target(self):
		return self.__target

	@target.setter
	def target(self,val):
		# #do not change the target once it has been set
		if not val is None:
			self.__target = val
			self.__argspec = inspect.getfullargspec(val)
			p = functools.partial(val)
			self.ismethod =  inspect.ismethod(p.func)
			# to let derivers do their thing
			self.on_func_set()
		return

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

	def inject_function_method(self, method_name,func, **keywords ):
		f = None
		try:
			f = self.target.__getattribute__(method_name)
			pass
		except:
			#ignore these
			pass
		if f is None:
			self.target.__setattr__(method_name, functools.partialmethod( func, **keywords))

		return

	def inject_object_method(self, objClient, method_name, func, **keywords):
		'''Inserts a method on the client object. Put keyword parameters you want to curry in **keywords '''
		f = None
		try:
			f = objClient.__getattribute__(method_name)
			pass
		except:
			#ignore these
			pass
		if f is None:
			objClient.__setattr__(method_name, functools.partial( func, **keywords))

		return

	def before(self, *args, **kwargs):
		'''Virtual. Called before the target function is called. '''
		if self.verbose and self.output_to == OutputTo.Console:
			print("********")
			print(f"""{self.func_name}""")
			#logging.basicConfig(level=logging.DEBUG)
			#logger = logging.getLogger(func_name)
		return

	def after(self, returned_value):
		'''Virtual. Called after the client function returns. '''
		if self.verbose: print("********")
		return


	def on_func_set(self):
		'''Purely Virtual. Callback for when the function is finalized.
		Keep this empty.
		'''
		return
	@property
	def argspec(self):
		return self.__argspec

	@property
	def func_name(self):
		ret = None
		if not self.__target is None:
			if type(self.__target) is functools.partial:
				ret = self.__target.func.__qualname__
			else:
				ret = self.__target.__qualname__
		return ret
	@property
	def func_name_with_id(self):
		ret = None
		if not self.__target is None:
			ret = repr(self.__target)
		return ret

