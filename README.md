<H1>akbinod.Tuner</H1>
Binod Purushothaman : binod@gatech.edu/ak.binod@gmail.com
<br>Georgia Tech CS-6476: Spring 2021<br>
<H3>Introduction</H3>
If you're studying Computer Vision, or Reinforcement Learning, parameter tuning is probably causing you some angst. Importing this component, and copying 3 lines into your code will get you a pretty decent parameter Tuner.

<br>Here's a 5 minute introduction to the essentials. This function and invocation...

```{python}
def find_circles(image, radius):

    # your implementation

    return results

if __name__ == "__main__":
    find_circles(image, 42)

```

... using TunerUI, become:

```{python}
#new import
import TunedFunction

#new decorator, and `tuner` parameter
@TunedFunction()
def find_circles(image, radius, tuner=None)


#new line of code to display the updated image in TunerUI
    if not tuner is None: tuner.image = updated_image

    return results

```

Your (unchanged) invocation from '__main__' now shows `TunerUI` with a slider ranging from 0 to 42. It calls 'find_circles()' with a new value for 'radius' each time you move the slider. And *that*'s pretty much all you need, to launch a tuning UX with:
<ul>
<li>grid searching through args,</li>
<li>tagging of args,</li>
<li>json serialization of invocation trees with args, results, tags, and exceptions.</li>
</ul>

Try it out on your code next, and If the UX works for you, come back to figure how to set minimums, pick from lists, receive json, etc.

<H2>@TunedFunction() Decorator</H2>
Implict Tuner instantiation. Although you do give up some flexibility, this is the quickest way of getting started with tuning your CV code.
<H3>Usage</H3>

<ul>
<li>Decorate the function you want to tune (referred to as <b>target</b>) with <code>@TunedFunction()</code> . There should be no other decorators on the function.
<li>Begin your tuning session by calling your function. This is the <b>launch call</b>.</li>

- TunedFunction creates an instance of TunerUI (passed to `target` via the `tuner` param) .
- Switch to the Tuner GUI:
	- Adjust the trackbars.
	- Tuner will invoke your function on each change made to a trackbar. These are referred to as <b>tuning calls</b>.
	- Update <code>tuner</code> with the processed image before you return from `target`. This refreshes the display in Tuner's GUI.
	- Remain in the tuning loop until you keyboard exit out of the loop. Please see 'saving' below.
<li>End your tuning session by pressing the escape (or any non function key)</li>
</ul>
</ul>

To restore normal operation of your function, comment out or delete the @TunedFunction() decorator.

<H3>
Tracked Parameters/What is tuned?
</H3>
Positional and keyword parameters (not varargs, or varkwargs) in your function signature are candidates for tuning. If your launch call passes an int, boolean, list or dict to any of these, then that parameter is tuned; the others are passed through to your function unchanged. Images, e.g., can't be tuned - so np.ndarray arguments are passed through to your function unchanged. Tuples of 3 ints also work, and are interpreted in a special way.
<p>

If you want to skip tuning some parameters in your `target's` signature, set default values for them, and drop them from your launch call. A param is not tuned, if an arg is not passed to it from your launch call.

It's the <i>type of the argument</i> passed in your launch call that drives Tuner behavior, not the annotation on the parameters. Each of the following launch calls would have a different effect:

```{language=python}
#image is passed through, radius is tuned - min 0, max 50
find_circles(image, radius=50)
#same as above
find_circles( image, 50 )
#radius is tuned with values ranging between 20, and 50
find_circles( image, (50,20) )
#radius is tuned and the slider selects among [10, 50, 90]
find_circles(image, [10,50,90])
#radius is tuned and target receives one of [10, 50, 90]
#The difference is that Tuner GUI dispalys "small", "med", "large"
j = {"small":10, "med":50, "large":90}
find_circles( image, radius=j )

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

### TunerUI Menu
<ul>
<li>F1 : runs a grid search on the parameters
<li>F2 : saves the image
<li>F3 : saves your Invocation Tree (see bleow)
<li>F8 - F10 : tags and saves your Invocation Tree (see below).
</ul>
#### Saving Invocation Trees
The basic idea behind Tuner is:
<ol>
<li>...hook up Tuner and invoke your function to tune it</li>
<li>...save your observations (tags) along with theta</li>
<li>...and finally, come back and analyse the Invocation Tree saved to your output file to narrow in on your ideal theta</li>
</ol>

Saving behavior is determined principally by a couple of statics in TunerConfig.
<p><b>TunerConfig.output_dir</b>: by default this is set to `./wip` Change this before you use the other functions of Tuner.</p>
<p><b>TunerConfig.save_style</b>: This should be set to some valid combination of the flags found in `constants.SaveStyles`. The default is to overwrite the contents of the output file on each run, and to only save when explicitly asked to. </p>
<p>The following are always tracked, although only saved to file under certain circumstances:
<ul>
<li><b>args</b>: The set of args to an invocation.</li>
<li><b>results</b>: This could be explicitly set by your code like so <code>tuner.results=...</code>. If you do not set this value, tuner captures the values returned by <code>target</code> and saves them as long as they are json serializable</li>
<li><b>errored</b>: Whether an error took place during <code>target</code> invocation.</li>
<li><b>error</b>: These are execution errors encountered during <code>target</code> invocation. BTW, the most recent call is first in this formatted list, not last as you would expect from typical python output.</li>
<li><b> [insert your tag here] </b>: A complete list of all the custom tags with the value set to false, unless you explicitly tag the invocation</li>
</ul>
These tracked values are pushed into the output file when:
<ul>
<li>You explicitly save  - F3.</li>
<li>You tag an invocation.</li>
<li>An error was encountered during the invocation .</li>
</ul>
The name of the output file begins with the function being tuned; and within the file, this is approximately the tree structure:
<ul>
<li>The title of the image from your carousel (see explicit instantiation below), defaulting to 'frame' </li>
<ul>
<li>The invocation key (what you see is the md5 hash of theta)</li>
<ul>
<li>args (contains each element of theta)</li>
<li>results (contains the saved or captured results of <code>target</code>)</li>
<li>each of the custom tags that you apply via the Tuner GUI</li>
</ul>
</ul>
</ul>
</ul>

#### Tagging Theta
The purpose of tuning is to find args that work for the task at hand. It might be a somewhat lengthy process, and this feature lets you tag some theta with a word that you can search for in the output file. I like using 'avoid', 'exact' and 'close', the defaults you see in the UI. You could customize this. Modify constants.py and update the `Tags` enum. Code comments there will explain your options. Pick a scheme that works for you, and stick with it. I'd recommend something like jsonpath to search the saved invocation tree.


#### Grid Search
This runs through a cartesian product of the parameter values you have set up. `target` is invoked with each theta, and Tuner waits indefinitely for your input before it proceeds to the next theta. Typically, you would tag each invocation while Tuner waits for input, or simply "press any key" your way through the cart (cartesian product).

With explicit instantion, you can set how long Tuner waits, whether the op is headless etc.

<b>Here's another good stopping point. Read on for more fine grained control.</b>
<H2>TunerUI Class</H2>

Most of the basics have been detailed above.

With explicit instantiation, you give up the convenience of automatic trackbar GUI configuration, and having arguments curried into your function. but there are added features you can access. If you like the UX of `@TunedFunction`, see the benefits section down below to determine if it's worth it to wade through the rest of this.

Instead of TunedFunction, you import TunerUI and TunerConfig. TunerUI is the facade you work with. You could ignore TunerConfig if the default settings work for you.

The basic pattern is about the same:
1. import TunerUI.
2. accept a `tuner` param with the default value of None...
2. ...do your thing...
3. set `tuner.image` to the processed image before you return...
4. optionally - set `tuner.results` to something that is json serializable before you return

Which is basically what you can do with <code>@TunedFunction</code> already, and with less code to boot. The difference lies in a few workflow features that you gain.

<ol>
<li>Instantiate tuner, choosing between one and two functions to watch. </li>
<ul>
<li>There's only one set of trackbars, but you could have two distinct functions called by Tuner - main and downstream. </li>
<li>When <code>downstream</code> accesses <code>tuner.image</code>, it too gets a fresh copy the current image being processed. To get the image processed by <code>main</code>, access <code>tuner.main_image</code>.</li>
<li><code>tuner.image</code> and <code>tuner.results</code> set from <code>main</code> are displayed in the main window (the one with the trackbars).</li>
<li><code>tuner.image</code> and <code>tuner.results</code> set in <code>downstream</code> are displayed in a second window which does not have trackbars. Usually, the downstream image obscures the main one; you'll need to move it out of the way.</li>
<li>Tuner will save images separately on F2, but will combine the results of both, along with args (tuned parameters) and writes it to one json file when you press F3. Remember to keep your results compatible with json serialization.</li>
</ul>
<li>Make calls to <code>tuner.track()</code>, <code>track_boolean()</code>, <code>track_list()</code> or <code>track_dict()</code> to define tracked/tuned parameters</li>
<li>Make a call to tuner.begin(). You do not use a launch call, like you did with <code>TunedFunction()</code>. This launches tuner, and then each change to a slider results in a tuning call to <code>target</code>.
<ul>
<li>Tuner curries args for formal parameters which match by name to a <code>tracked parameter</code></li>
<li>All tracked parameters are also accessible off <code>tuner</code>. E.g., <code>tuner.my_favorite_setting</code>. This enables you to tune variables that are not part of the formal arguments to your function. Wondering if you should set <code>reshape=True</code> in a call to <code>cv2.resize()</code>, just add a tracked parameter for that (without adding a parameter to your function), and access it off <code>tuner</code>. The idea is to keep your function signature the same as what the auto-grader would expect - minimizing those 1:00am exceptions that fill one with such bonhomie. These args are also accesible as a set via tuner.args</li>
<li><code>tuner.begin()</code> accepts a carousel argument. A carousel is a list of images that you want tuner to deal with as a set. </li>
<ul>
<li>You typically want to do this to find parameters that will work across all images in the set.</li>
<li>Use the helper call <code>tuner.carousel_from_images()</code> to set up a carousel. This takes 2 lists.
<ul>
<li>The first is the list of parameters to <code>target</code> that take images. <code>target</code> might work with multiple images, and this list is where you specify the names of those parameters.</li>
<li> The second is a list of paths to image files. If <code>target</code> works with 2 images, then each element of this second list must be a tuple of two image paths. If it works with three images, then each element must be a tuple of three image paths, et cetera. </li>
<ul>
</ul>
</ul>
</ul>
</ul>
</ol>

You cannot mix Tuner with partials and decorators (things blow up unperdictably) - just the func please.

Besides the above, it's all pretty much the same. You do have access to a few additional methods, and the docstrings should explain those. Some of the gains are:
<ul>
<li>Being able to tune hyper-parameters without having them be parameters to your function. This keeps your signatures what your auto-grader expects, which is always pleasant when you have just one auto grader submission left until 3:00am :)</li>
<li>Process a carousel of images, remembering settings between images.</li>
<li>Insert a thumbnail into the main image (set <code>tuner.thumbnail</code> from within your target function). This is useful, e.g., when you are matching templates. You could do this with <code>@TunedFunction</code> as well.</li>
<li>View the results of two processes in side by side windows. A few use cases for side-by-side comparison of images:
<ul>
<li>your pre-processing output in main; and traffic sign identification output in downstream;</li>
<li>Template Matching output in one vs. Harris Corners output in the other;</li>
<li>what your noble code found, vs. what the built in CV functions found (I find this view particularly revealing; also, character building).</li>
</ul>
<li>Controlling aspects of <code>tuner.grid_search()</code>. Please see the dostrings for more information. </li>
<li>You get to control whether the GUI returns list items vs list indices; keys vs dict objects etc. </li>
<li>Finally, as anyone who has written a Decorator know, things can get squirrelly when exceptions take place within a partial... you could avoid that whole mess with explicit instantiation of Tuner.</li>
</ul>

The accompanying sample files illustrate some uses. Play around, and let me know if you think of ways to improve this.
</p>

### OpenCV GUI
Your experience of this GUI is going to be determined by the version of various components - OpenCV, and the Qt backend. Tuner does take advantage of a couple of the features of the Qt backend, but those are guarded in `try` blocks, so you shouldn't bomb.
If you're in CS-6476, you've installed <code>opencv-contrib-python</code>. If not, might I suggest...

If you don't see the status bar in Tuner GUI, you are missing <code>opencv-contrib-python</code>
If you don't see the overlay after each trackbar change, you are missing <code>Qt backend</code>

### Important Safety Tip
I've debugged this thing extensively, but I haven't had the time to bullet proof it. It will behave if your arguments are well behaved; but caveat emptor...

### Licensing
It's only licensed the way it is to prevent commercial trolling. For all other purposes...

```Fork it, make something beautiful.```