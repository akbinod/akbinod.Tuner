
<H1>akbinod.Tuner</H1>

<H3>Why bother?</H3>
<p>
If you're studying Computer Vision, hyper-parameter tuning is probably causing you some angst. I wrote this in the middle of PS-3 and 4 in GA Tech's CS-6476 ("yay OMS"). I wish I'd had it before starting. So, here you go - enjoy!

I've included some sample code that shows you how to use Tuner, and a barebones example that illustrates using Tuner to adjust your pre-processing.
</p>

<H3>How does it work?</H3>
Tuner hooks into your code. Here is a quick example.

```{python}

# here's your existing code
def find_circles(image, radius):

    # your implementation

    return results

```
Including Tuner in your workflow, this becomes:
```{python}
#new import
from Tuner import TunedFunction

#new decorator
@TunedFunction()
def find_circles(image, radius, tuner=None)
#new parameter

	#your original implementation

	# three new lines of code before you return
    if not tuner is None:
        tuner.results = results
        tuner.image = result_image

    return results

```
<p>
The mods you need to make:
</p>
<ol>
<li>Modify the tuning <bold>target</bold> (<code>find_circles()</code> in the example above) to accept a parameter <code>tuner=None</code></li>
<li>set <code>tuner.image</code> and <code>tuner.results</code> to show them in the Tuner window.
</ol>
<p>
Kicking off the tuning process in this example, is the following line of code:
</p>

``` {python}
find_circles(image,radius=50)
# OR
find_circles(image, radius=(50,5,10))
```
<i>
And that's pretty much it, really!
</i>
<p>

The first call above creates a trackbar that lets you slide the radius between 0 and 50.
The second call is taken to mean that the trackbar should have <code>max=50, min=5, default = 10</code>. The trackbar is set to <code>default</code> when you first see the GUI.

</p>


<H2>@TunedFunction() Decorator</H2>
Implict Tuner instantiation. Although you do give up some flexibility, and a few features, this is the quickest way of getting started with tuning your CV code.
<H3>Usage</H3>

<ul>
<li>Decorate the function you want to tune (referred to as <b>target</b> or tuned function) with <code>@TunedFunction()</code> . See the quick example above.</li>
<li>Begin your tuning session by calling your function. This is the <b>launch call</b>.</li>

- TunedFunction takes over and creates a Tuner GUI.
- Switch to the Tuner GUI:
	- Adjust the trackbars.
	- Tuner will invoke your function on each change made to a trackbar. These are referred to as <b>tuning calls</b>.
	- Update <code>tuner</code> with results, and the processed image (see example above) before you return from the tuning call.This refreshes the display in Tuner's GUI.
	- Remain in the tuning loop until you keyboard exit out of the loop.
-When you are satisfied with your results, press F3 to save those results. Tuner will save the last used values of the tuned params, as well as whatever you set in tuner.results. Typically, these params would be the various hyper parameter values you need for your project.

<li>End your tuning session by pressing the escape (or any non function key)</li>
</ul>
<p>
To restore normal operation of your function, comment out or delete the @TunedFunction decorator.
</p>
<H3>
What gets tuned?
</H3>
Short answer: some of the parameters to your function. Those that meet the criteria below get tuned, the others are passed through to your function unchanged.
<p>
@TunedFunction works with:
<ul>
<li>positional parameters...</li>
<li>...to which you have sent arguments of specic types (see below)</li>
</ul>

All other arguments (including kwargs) are passed on untouched and those parameters are not tuned. Images are typically passed around as np.ndarray objects, or as strings representing file names; TunedFunction passes these types through untouched.

If you want <code>@TunedFunction</code> to work with a parameter, the argument you pass to it in your launch call must be of one of a specific set. It's the type of the <i>argument</i> passed, not the annotation on the parameter that drives Tuner behavior. Each of the following launch calls would have a different effect:

```
find_circles(image, radius=50)
find_circles(image, radius=["small","medium","large"])
```

</p>
Tuner will work with arguments of the following types:
<ul>
<li>int</li>
    A trackbar will be created in the Tuner GUI with max set to the value passed in by you in the launch call.
<li>tuple</li>
    A trackbar will be created assuming that the tuple holds <code>(max,min,default)</code> Default is the starting value in the GUI; useful when you are done tuning a particular parameter.
<li>boolean</li>
    A trackbar will be created with two settings <code>0, 1 </code> which correspond to <code>False, True</code>. The default value is whatever you have passed in. Tuner will call target with one of <code>False, True</code> depending on trackbar selection.
<li>list</li>
This is a good way to specify non int values of some managable range. Strings, floats, tuples all go in lists.

- A trackbar will be created matching the length of your list of values.
- Changing the trackbar selects the corresponding item from the list.
- The argument passed to target is the list item.

	E.g., when your launch call passes ['dog','cat','donut'] to the <code>radius</code> parameter, Tuner will:

    - create a trackbar with 3 positions.
	- call target passing one of the following ['dog','cat','donut'] to <code>radius</code> - whichever you've selected with the trackbar.

<br>Trivially, <code>[(3,3), (5,5), (7,7)]</code> is a list you might use for tuning the <code>ksize</code> parameter of  <code>cv2.GaussianBlur()</code>
<li>dict or json object</li>
    Very similar to list above. obj[key] is returned in the arg to target.

Consider the json below. Passing that to a parameter would create a trackbar that flits amongst "gs", "gs_med" and "gs_heavy". When `target` is invoked in a tuning call, the argument passed in is the json corresponding to the selected key.

```
	preprocessing_defs = {
	"gs" :{
        "img_mode": "grayscale"
        , "blur":{
				"apply": false
        		, "ksize": (3, 3)
				, "sigmaX": 1
				}
        , "edge": {
				"detect" : false
        		, "threshold1": 100
				, "threshold2": 75
				, "apertureSize": 3
				}
    }
    ,"gs_med":{
        "img_mode": "grayscale"
        , "blur":{
				"apply": false
        		, "ksize": (5, 5)
				, "sigmaX": 2
				}
        , "edge": {
				"detect" : false
        		, "threshold1": 150
				, "threshold2": 100
				, "apertureSize": 5
				}
    }
    ,"gs_heavy":{
        "img_mode": "grayscale"
        , "blur":{
				"apply": true
        		, "ksize": (7, 7)
				, "sigmaX": 4
				}
        , "edge": {
				"detect" : true
        		, "threshold1": 150
				, "threshold2": 100
				, "apertureSize": 5
				}
    }
}
```

</ul>

<H2>The Tuner Class</H2>

Most of the basics have been detailed above. With explicit instantiation, you give up the convenience of automatic trackbar GUI configuration, but there are added features you can access. If you like the UX of `@TunedFunction`, see the benefits section down below to determine if it's worth it to wade through the rest of this.
The basic pattern is about the same:
1. accept a `tuner` param...
2. new: get the image you should work on from `tuner.image`...
3. set `tuner.image` and `tuner.results` before you return...

Which is basically what you can do with <code>@TunedFunction</code> already, and with much less code to boot. The difference lies in a few workflow features (which admittedly have been developed for an audience of one - me!)


A significant change is that Tuner will not be currying parameters during these tuning calls, and you need to access all tuned parameters off <code>tuner</code>. You can either look in the <code>tuner.args</code> dict, or just directly reference the tuner attribute, e.g,, <code>tuner.radius</code> to continue with the first example. Incidentally, these attributes are readonly from code; they can only be changed by the trackbars.

One of the following must apply to target (main and downstream):
<ol>
<li>Target's signature only accepts Tuner (no bueno).</li>
<li>Target's signature has defaults for all parameters (easiest).</li>
<li>Target is a functools.partial with all arguments besides <code>tuner</code> curried in (most flexible).</li>
</ol>

The workflow basically looks like this:
<ol>
<li>Instantiate tuner.Choose between one and two functions to track. </li>

-There's only one set of trackbars, but you could have two distinct functions called by Tuner - main and downstream.
		-<code>tuner.image</code> (and results) set in cb_main are displayed in the main window.
		-<code>tuner.image</code> (and retults) set in cb_downstream are displayed in a second window which does not have trackbars.
-<code>Tuner</code> will track the images set by each of these separately. It combines the <code>.results</code> of both, along with args (tuned parameters) and dumps the whole lot to a json file when you press F3.
-Each function is called with a fresh copy of the current image. See below for more on images passed in to process.
<li>Add hyper-parameters to tune via the <code>tuner.track_*</code>  set of calls. Since these are not curried into target, they can be anything you want to tune - without reference to a function parameter.</li>
<li>Launch the tuning loop by calling <code>tuner.begin()</code>. Pass in:</li>

	- None: when you do not plan to use the image Tuner holds for you
	- A single image: typically when you are still just getting started with your code, and working one image at a time.
	- A list of file names: typically, when you have a set of test images you want to put through target. Tuner will cycle through all the images until you exit. Esc cancels the stack, any other key will advance the carousel.

</ol>
<p>
Besides the above, it's all pretty much the same. You do have access to a few additional methods, and the docstrings should explain those. Some of the gains are:
<ul>
<li>Being able to tune hyper-parameters without having them be parameters to your function. This keeps your signatures what your auto-grader expects, which is always pleasant when you have just one auto grader submission left until 3:00am :)</li>
<li>Process a stack of images, remembering settings between images.</li>
<li>View the results of two processes in side by side windows. A few use cases for side-by-side comparison of images:

- your pre-processing output in main; and traffic sign identification output in downstream;
- Template Matching output in one vs. Harris Corners output in the other;
- what your noble code found, vs. what the built in CV functions found (I find this view particularly revealing; also, character building).

</li>
<li>Access to features of Tuner like <code>tuner.review()</code> etc. Please see the dostrings for more information.</li>
</ul>


The accompanying sample files illustrate some uses. Play around, and let me know if you think of ways to improve this.
</p>