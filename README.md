
<H1>akbinod.Tuner</H1>
Binod Purushothaman : binod@gatech.edu
<br>Georgia Tech CS-6476: Spring 2021
<H3>Why bother?</H3>
Because 6 ines of code will get you a pretty decent hyper-parameter Tuner.
<br></br>
If you're studying Computer Vision, hyper-parameter tuning is probably causing you some angst. I wrote this while in the middle of PS-3 and 4 ("yay OMS"). I've included some sample code that shows you how to use Tuner, and a barebones example that illustrates using Tuner to adjust your pre-processing. Please do look at the section on required pip installs towards the end of this document.

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
import TunedFunction

#new decorator
@TunedFunction()
def find_circles(image, radius, tuner=None)
#new parameter

	#your original implementation

	# new lines of code before you return
    if not tuner is None:
        tuner.results = results
        tuner.image = result_image

    return results

```
<p>
The changes you need to make:
</p>
<ol>
<li>Modify the tuning <b>target</b> (<code>find_circles()</code> in the example above) to accept a new parameter <code>tuner=None</code></li>
<li>set <code>tuner.image</code> and <code>tuner.results</code> to show them in the Tuner GUI.
</ol>
<p>
Kicking off the tuning process in this example, is the following line of code:
</p>

``` {python}
find_circles(image, 50)
# OR (there's more of an explanation below)
find_circles(image, (50,5,10))
```

The first call above creates a trackbar that lets you slide the radius between 0 and 50.
The second call is taken to mean that the trackbar should have <code>max=50, min=5, default = 10</code>. The trackbar is set to <code>default</code> when you first see the GUI.

<b>And that's pretty much it! This is all you need to know to get up and running; and this is all you need if you're happy receiving ints as args. Read on if you would like to receive json, etc.
</b>
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
-When you are satisfied with your results, press F3 to save those results. Tuner will save the last used values of the tuned params, as well as whatever you set in tuner.results. Typically, these params would be the various hyper parameter values you need for your project. Your results need to be json friendly, so don't pass in np.ndarrays, and other values that the json module will not handle.

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
@TunedFunction works with the following subset of target's parameters:
<ul>
<li>Positional arguments...</li>
<ul>
<li>If your launch call looks like draw_circle(50) then radius is tuned.
<li>If your launch call looks like draw_circle(radius=50), then radius is NOT tuned.
This is by design; it gives you a way of excluding a parameter from tuning.
</ul>

<li>Positional arguments...to which your launch call sends arguments of the following types:</li>
-int, boolean, list, and dict. Tuples of 3 ints also work, and are interpreted in a special way.
</ul>

All other arguments (including kwargs) are passed on untouched and those parameters are not tuned. Images are typically passed around as np.ndarray objects, or as strings representing file names; TunedFunction passes these types through untouched.

It's the type of the <i>argument</i> passed in your launch call that drives Tuner behavior, not the annotation on the parameters. Each of the following launch calls would have a different effect:

```{language=python}
#no tuning - target just receives 50 since radius is now a kwarg
find_circles(image, radius=50)
#radius is tuned with values ranging from 0 to 50
find_circles(image, 50)
#radius is tuned with values ranging between 20, and 50
find_circles(image, (50,20)
#radius is tuned and target receives one of [10, 50, 90]
find_circles(image, [10,50,90])
#radius is tuned and target receives one of [10, 50, 90]
#The difference is that Tuner GUI dispalys "small", "med", "large"
j = {"small":10, "med":50, "large":90}
find_circles(image, j)

```
</p>
When an argument in the launch call is:
<ul>
<li>int</li>
    The trackbar's max is set to the int value passed in.
<li>tuple</li>
    The trackbar's <code>(max,min,default)</code> are taken from the tuple.
<li>boolean</li>
    The trackbar will have two settings <code>0, 1 </code> which correspond to <code>False, True</code>. The default value is whatever you have passed in. Tuner will call target with one of <code>False, True</code> depending on trackbar selection.
<li>list</li>
This is a good way to specify non int values of some managable range. Strings, floats, tuples all go in lists.

- The trackbar will have as many ticks as there are items in the list.
- Changing the trackbar selects the corresponding item from the list.
- The argument passed to target is the list item.
	E.g., when your launch call passes ['dog','cat','donut'] to the <code>radius</code> parameter, Tuner will:
    - create a trackbar with 3 positions.
	- call target passing one of the following ['dog','cat','donut'] to <code>radius</code> - whichever you've selected with the trackbar.

<br>Trivially, <code>[(3,3), (5,5), (7,7)]</code> is a list you might use for tuning the <code>ksize</code> parameter of  <code>cv2.GaussianBlur()</code>
<li>dict or json object</li>
    Very similar to list above. obj[key] is returned in the arg to target.

Consider the json below. Passing that to a parameter would create a trackbar that switches amongst "gs", "gs_blur" and "gs_blur_edge". When `target` is invoked in a tuning call, the argument passed in is the json corresponding to the selected key.

```
	preprocessing_defs = {
	"gs" :{
        "img_mode": "grayscale"
        , "blur":{"apply": false}
        , "edge": {"detect" : false}
    }
    ,"gs_blur":{
        "img_mode": "grayscale"
        , "blur":{"apply": true, "ksize": (5, 5), "sigmaX": 2}
        , "edge": {"detect" : false}
	}
   , "gs_blur_edge": {
        "img_mode": "grayscale"
        , "blur":{"apply": true, "ksize": (5, 5), "sigmaX": 2}
        , "edge": {"detect" : true, "threshold1": 150, "threshold2": 100, "apertureSize": 5}
	}

```
</ul>
<b>Here's another good stopping point. Read on for more fine grained control.</b>
<H2>The Tuner Class</H2>

Most of the basics have been detailed above. With explicit instantiation, you give up the convenience of automatic trackbar GUI configuration, and having arguments curried into your function. but there are added features you can access. If you like the UX of `@TunedFunction`, see the benefits section down below to determine if it's worth it to wade through the rest of this.
The basic pattern is about the same:
1. accept a `tuner` param...
2. new: get the image you should work on from `tuner.image`. You get a fresh copy of the image to work on each time you read this.
3. update `tuner.image` and `tuner.results` with the processed image before you return...

Which is basically what you can do with <code>@TunedFunction</code> already, and with much less code to boot. The difference lies in a few workflow features (which admittedly have been developed for an audience of one - me!)

A significant change is that Tuner will not be currying parameters during these tuning calls, and you need to access all tuned parameters off <code>tuner</code>. You can either look in the <code>tuner.args</code> dict, or just directly reference the tuner attribute, e.g,, <code>tuner.radius</code> to continue with the first example. Incidentally, these attributes are readonly from code; they can only be changed by the trackbars.

One of the following must apply to target (main and downstream):
<ol>
<li>Target's signature only accepts Tuner (no bueno, from the auto grader perspective).</li>
<li>Target's signature has defaults for all parameters (easiest, and plays well with the auto grader).</li>
<li>Target is a functools.partial with all arguments besides <code>tuner</code> curried in (most flexible, but also <b>work</b>).</li>
</ol>

The workflow basically looks like this:
<ol>
<li>Instantiate tuner.Choose between one and two functions to watch. </li>
-There's only one set of trackbars, but you could have two distinct functions called by Tuner - main and downstream. When <code>downstream</code> accesses <code>tuner.image</code>, it too gets a fresh copy the current image being processed. To get the image processed by <code>main</code>, access <code>tuner.main_image</code>.

- tuner.image and tuner.results set from cb_main are displayed in the main window.
- tuner.image and tuner.results set in <code>downstream</code> are displayed in a second window which does not have trackbars. Usually, the downstream image obscures the main one; you'll need to move it out of the way.
- Tuner will save them separately on F2.
- It combines the results of both, along with args (tuned parameters) and writes it to one json file when you press F3. Remember to keep your results compatible with json serialization.

<li>Add hyper-parameters to tune via the <code>tuner.track_*</code>  set of calls. Since these are not curried into target, they can be anything you want to tune - without reference to function parameters.</li>
<li>Launch the tuning loop by calling <code>tuner.begin()</code>. Pass in:</li>
<ul>
<li>None: when you do not plan to use the image Tuner holds for you
<li>A single image: typically when you are just getting started with your code, and working one image at a time.
<li>A list of file names: typically, when you have a set of test images you want to put through target. Tuner will cycle through all the images until you exit. Esc cancels the stack, any other key will advance the carousel.
</ul>
</ol>
<p>
Besides the above, it's all pretty much the same. You do have access to a few additional methods, and the docstrings should explain those. Some of the gains are:
<ul>
<li>Being able to tune hyper-parameters without having them be parameters to your function. This keeps your signatures what your auto-grader expects, which is always pleasant when you have just one auto grader submission left until 3:00am :)</li>
<li>Process a stack of images, remembering settings between images.</li>
<li>Insert a thumbnail into the main image (set <code>tuner.thumbnail</code> from within your target function). This is useful, e.g., when you are matching templates. You could do this with <code>@TunedFunction</code>, but then it isn't 6 lines of code anymore, is it...</li>
<li>View the results of two processes in side by side windows. A few use cases for side-by-side comparison of images:
<ul>
<li>your pre-processing output in main; and traffic sign identification output in downstream;</li>
<li>Template Matching output in one vs. Harris Corners output in the other;</li>
<li>what your noble code found, vs. what the built in CV functions found (I find this view particularly revealing; also, character building).</li>
</ul>
<li>Access to features of Tuner like <code>tuner.review()</code> etc. Please see the dostrings for more information. A couple of the more interesting static methods are <code>tuner_from_json()</code> and <code>minimal_preprocessor()</code>. Some day, I'll get around to implementing <code>grid_search()</code> </li>
<li>Finally, as anyone who has written a Decorator know, things can get squirrelly when exceptions take place... you could avoid that whole mess with explicit instantiation of Tuner.</li>
</ul>

The accompanying sample files illustrate some uses. Play around, and let me know if you think of ways to improve this.
</p>

### OpenCV GUI
Your experience of this GUI is going to be determined by the version of various components - OpenCV, and the Qt backend. Tuner does take advantage of a couple of the features of the Qt backend, but those are guarded in `try` blocks, so you shouldn't bomb.
If you're in CS-6476, you've installed <code>opencv-contrib-python</code>. If not, might I suggest...

If you don't see the status bar in Tuner GUI, you are missing <code>opencv-contrib-python</code>
If you don't see the overlay after each trackbar change, you are missing <code>Qt backend</code>

### Important Safety Tip
I've debugged this thing extensively, but I haven't had the time to bullet proof it. It will behave if your arguments are well behaved; but if you try to serialize an np.ndarray it'll blow up - gloriously.

### Licensing
It's only licensed the way it is to prevent commercial trolling. For all other purposes...

```Fork it, make something beautiful.```