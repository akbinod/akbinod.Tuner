<H1>akbinod.Tuner</H1>
Binod Purushothaman : binod@gatech.edu/ak.binod@gmail.com
<br>Georgia Tech CS-6476: Spring 2022<br>

![ThetaUI](./images/tuner_example_2.png "tuning my Particle Filter")

<H3>Introduction</H3>
If you're studying Computer Vision, or Reinforcement Learning, parameter tuning is probably causing you some angst. Importing this component, and copying 3 lines into your code will get you a pretty decent parameter Tuner.


<br>Here's a 5 minute introduction to the essentials. This function (the code for this example is in `example.py`) and invocation...

```{python}
def find_circle(image, radius):

    # your implementation

    return results

if __name__ == "__main__":
    find_circle(image, 42)

```

... hooked up to Tuner, become:

```{python}
#new import
import TunedFunction

#new decorator, and a 'tuner' param
@TunedFunction()
def find_circle(image, radius, tuner=None)


#new line of code to display an updated image in ThetaUI
    if not tuner is None: tuner.image = updated_image

    return results

```

Your (unchanged) invocation from '__main__' now shows <code>ThetaUI</code> : ~~an openCV window with a trackbar~~ a python tkinter GUI with a spinbox called 'radius' which ranges from 0 to 42.
- the window title shows the name of your tuned function,
- various parts of the status bar tell you:
	- the image title (when you pass in a file name),
    - the frame number (when you pass in a carousel of images)
    - code timing in h,m,s and process time
	- whether the image displayed was sampled/interpolated,
	- whether there were exceptions during execution (click when red to view exceptiosn).
- the menus let you traverse the carousel, start a grid search, save results and images etc.
- on the left, the tree shows you json representing what your results/return vlaues, your args (theta) and exceptions.

Each time you change a parameter, <code>ThetaUI</code> calls your code <code>find_circle()</code> with a new value for 'radius'. Here's ThetaUI when the trackbar is set to 39.

![ThetaUI](./images/tuner_example_1.png "ThetaUI")

<br>And *that* folks, is pretty much it. Here's a good stopping point; try this out on your CV code.

At this point, you are using a python execution harness; one that's easy to use and not disruptive to your code. You also get to skip learning about the openCV HighGUI and trackbars APIs, and focus instead on the joys of particle filtering. There's more to <code>ThetaUI</code>, like:
<ul>
<li>it runs a systematic <a href='#gridsearch'>grid search</a> over the space of your args (exhausts the search space),</li>
<li><a href='#tag'> tagging</a> args (note when theta is cold/warm/on-the-money),</li>
<li>json <a href='#serialize'>serialization</a> of invocation trees </li>
</ul>

<br>So... read on...

<H2>@TunedFunction() Decorator</H2>
Although you do give up some flexibility, compared to explicitly instantiating and configuring Tuner, just decorating your function is the quickest way of getting started.
<H3>Usage</H3>

<ol>
<li>Decorate the function you want to tune (referred to as <b>target</b>) with <code>@TunedFunction()</code>, and add a 'tuner' param to its signature. (Note: there should be no other decorator on <code>target</code>.)
<li>Begin tuning by calling <code>target</code>. <code>@TunedFunction</code> creates an instance of ThetaUI (passed to <code>target</code> via the <code>tuner</code> param). You are now in the tuning loop:</li>
<ul>
<li>Switch to the Tuner GUI and adjust the trackbars.</li>
<li>Tuner will invoke your function on each change made to a trackbar.</li>
<li>Set <code>tuner.image</code> to the processed image from within <code>target</code>. This refreshes the display in Tuner's GUI.</li>
</ul>
<li>End your tuning session by pressing the Esc (or any non function key)</li>
</ol>


To restore normal operation of your function, comment out or delete the @TunedFunction() decorator.

<H3>
Tracked/Pinned Parameters, or What is tuned?
</H3>
Positional and keyword parameters (not varargs, or varkwargs) in your function signature are candidates for tuning. If your launch call passes an int, boolean, list or dict to any of these, then that parameter is tuned; the others are passed through to your function unchanged (I.E. they are automatically "pinned"). Images, e.g., can't be tuned - so np.ndarray arguments are passed through to your function unchanged. Tuples of 3 ints also work, and are interpreted in a special way.
<p>

If you want to skip tuning (aka "pin") some parameters in your <code>target</code>'s signature, you have the following options, choose what works best for your workflow:
<li>Set a default value for the parameter you want to pin and drop the argument from your launch call. A param is not tuned, if an arg is not passed to it from your launch call. </li>
<li>When the argument passed to the target function is of a type that Tuner does not hendle, the value is passed to target unchanged (pinned).</li>
<br>
It's the <i>type of the argument</i> passed in your launch call that drives Tuner behavior, not the annotation on the parameters.

```{language=python}
#image is passed through, radius is tuned - min 0, max 50
find_circle(image, radius=50)
#same as above
find_circle( image, 50 )
#radius is tuned with values ranging between 20, and 50
find_circle( image, (50,20) )
#radius is tuned and the slider selects among [10, 50, 90]
find_circle(image, [10,50,90])
#radius is tuned and target receives one of [10, 50, 90]
#The difference is that Tuner GUI dispalys "small", "med", "large"
j = {"small":10, "med":50, "large":90}
find_circle( image, radius=j )

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
This is a good way to specify non int values of some managable length. Strings, floats, tuples all go in lists.

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

### ThetaUI Menu
<ul>
<li>F1 : runs a <a href='#gridsearch'>grid search</a></li>
<li>F2 : saves the image</li>
<li>F3 : <a href='#serialize'>saves</a> your Invocation Tree</li>
<li>F8 - F10 : <a href='#tag'>tags</a> and saves your Invocation Tree (see below).</li>
</ul>
<H4 id='serialize'>Saving Invocation Trees</H4>
The basic idea behind Tuner is:
<ol>
<li>...hook up Tuner and invoke your function to tune it</li>
<li>...save your observations (tags) along with theta</li>
<li>...and finally, come back and analyse the Invocation Tree saved to your output file to narrow in on your ideal theta</li>
</ol>

Saving behavior is determined principally by a couple of statics in TunerConfig.
<p><b>TunerConfig.output_dir</b>: by default this is set to `./wip` Change this before you use the other functions of Tuner.</p>
<p><b>TunerConfig.save_style</b>: This should be set to some valid combination of the flags found in `constants.SaveStyles`. The default is to overwrite the contents of the output file on each run, and to only save when explicitly asked to. </p>
<p>The following are always tracked, although only <a href='serialized'> serialized</a> to file under certain circumstances:
<ul>
<li><b>args</b>: The set of args to an invocation.</li>
<li><b>results</b>: This could be explicitly set by your code like so <code>tuner.results=...</code>. If you do not set this value, tuner captures the values returned by <code>target</code> and saves them as long as they are json serializable</li>
<li><b>errored</b>: Whether an error took place during <code>target</code> invocation.</li>
<li><b>error</b>: These are execution errors encountered during <code>target</code> invocation. BTW, the most recent call is first in this formatted list, not last as you would expect from typical python output.</li>
<li><b> [insert your tag here] </b>: A complete list of all the custom tags with the value set to false, unless you explicitly tag the invocation, in which case the particular tag(s) are set to <code>True</code>.</li>
</ul>
<a id='serialized'> An invocation is serialized to the output file when:
<ul>
<li>You explicitly save  - F3.</li>
<li>You tag an invocation.</li>
<li>An exception was encountered during the invocation.</li>
</ul>
The name of the output file begins with the function being tuned; and within the file, this is approximately the tree structure:
<ul>
<li>The title of the image from your carousel (see explicit instantiation below), defaulting to 'frame' </li>
<ul>
<li>The invocation key (what you see is the md5 hash of theta)</li>
<ul>
<li>args (contains each element of theta)</li>
<li>results (contains the saved or captured results of <code>target</code>)</li>
<li>the custom tags that you set up in Tuner GUI, defaulting to False</li>
<li>errored</li>
<li>errors (contains your execution exceptions)</li>
</ul>
</ul>
</ul>
</ul>

<H4 id='tag'>Tagging Theta</H4>
The purpose of tuning is to find args that work for the task at hand. It might be a somewhat lengthy process, and this feature lets you tag some theta with a word that you can search for in the output file. I like using 'avoid', 'exact' and 'close', the defaults you see in the UI. You could customize this. Modify constants.py and update the `Tags` enum. Code comments there will explain your options. Pick a scheme that works for you, and stick with it. I'd recommend something like glom or jsonpath-ng to search the saved invocation tree.


<H4 id='gridsearch'>Grid Search</H4>
If you are not a "parameter whisperer", you're going to turn to brute force tuning at some point; I did. So, with 3 params, each of which could take 5 values, you're likely to be annoyed by the process, and more likely to make a costly mistake. The worst of tuning, for me, is the prospect of missing the "right set of args", thanks to NOT clicking through the various settings methodically. Fortunately, there's code for that.

<br>This feature runs through a cartesian product of the parameter values you have set up. <code>target</code> is invoked with each theta, and Tuner waits indefinitely for your input before it proceeds to the next theta.

Here's my workflow:
<ol>
<li>I start with a small range of inputs, and let Tuner search through that space.</li>
<li>When Tuner waits for input, I tag the current set of args (e.g., 'avoid' or 'close'); or just 'press any key'. I can also hit Esc to cancel the grid search.</li>
<li>After I've run through the cart (cartesian product of all arguments), I query the (json) output file to find my theta, or something close.</li>
</ol>
With explicit instantiation (i.e., using ThetaUI rather than @TunedFunction), I can set how long Tuner waits, etc. I typically first run through the search space with a 40ms delay to determine if I'm "in the ball-park". If it looks like the answer or something close to it is in there, I then run through it again with a full second delay, and tag what I find interesting. If I don't find anything close in my first attempt, I open up the search space some (expand the range of values for the args).

This is about as much code as I can give you without running afoul of the GA Tech Honor Code. We can spitball some ideas to help you get more value out of the data that's captured if you follow the "Search-Inspect-Tag" workflow I've outlined above.
<ol>
<li>If you find a number of 'close' thetas, build a histogram of the various args to EACH param, using only thetas that are 'close'. That should highlight a useful arg to that param :)</li>
<li>Implement a Kalman Filter to help you narrow the grid search.</li>
</ol>

<b>Here's another good stopping point. Read on for more fine grained control.</b>
<H2>ThetaUI Class/Explicit Instantiation</H2>

With explicit instantiation, you give up the convenience of automatic trackbar GUI configuration, but gain more control over features. If you like the UX of <code>@TunedFunction</code>, see the <a href='#explicit'>benefits </a> section below to determine if it's worth it to wade through the rest of this.

Instead of TunedFunction, you import ThetaUI and TunerConfig. ThetaUI is the facade you work with. You could ignore TunerConfig if the default settings (e.g. when and where to save) work for you.

Workflow:

<ol>
<li>import ThetaUI</li>
<li>Instantiate tuner, choosing between one and <a href='#downstream'> two </a>functions to watch : <code>main</code> and <code>downstream</code>. </li>
<ul>
<li>Each func must accept a <code>tuner</code> param with the default value of None...</li>
</ul>
<li>Make calls to <code>tuner.track()</code>, <code>track_boolean()</code>, <code>track_list()</code> or <code>track_dict()</code> to define tracked/tuned parameters to <code>main</code></li>
<li>Make a call to <code>tuner.begin()</code>, or to <code>tuner.grid_search()</code>. Each of these calls accepts a <a href='carousel'>carousel</a>. You do not use a launch call, as you did with <code>TunedFunction()</code>.
<ul>
<li>This launches tuner, and then, as usual, each change to a trackbar results in a tuning call to <code>target</code>. </li>
<li>Tuner passes args to formal parameters which match by name to a tracked parameter.</li>
<li>All tracked parameters are also accessible off <code>tuner</code>. E.g., <code>tuner.radius</code>. This enables you to tune variables that are not part of the formal arguments to your function. Wondering if you should set <code>reshape=True</code> in a call to <code>cv2.resize()</code>? Well, just add a tracked parameter for that (without adding a parameter to your function), and access its value off <code>tuner</code>. The idea is to keep your function signature the same as what the auto-grader would expect - minimizing those 1:00am exceptions that fill one with such bonhomie. These args are also accesible as a dict via tuner.args</li>
</ul>
<li>set <code>tuner.image</code> to the processed image before you return...</li>
<li>optionally - set <code>tuner.results</code> to something that is json serializable before you return.</li>
</ol>
<br>You cannot mix Tuner with partials and decorators (things blow up unperdictably) - just the func please.
<H4 id='downstream'>Watching Downstream Functions</H4>
You could have two distinct functions called by Tuner - <code>main</code> (called first) and <code>downstream</code> (called after <code>main</code>).
<ul>
<li>There's only one set of trackbars - these appear on <code>main</code>'s window.</li>
<li>Args (other than tuner) are not curried into <code>downstream</code>, so set defaults.</li>
<li>When <code>downstream</code> accesses <code>tuner.image</code>, it gets a fresh copy of the current image being processed. To get the image processed by <code>main</code>, access <code>tuner.main_image</code>.</li>
<li><code>tuner.image</code> and <code>tuner.results</code> set from <code>main</code> are displayed in the main window (the one with the trackbars).</li>
<li><code>tuner.image</code> and <code>tuner.results</code> set in <code>downstream</code> are displayed in the <code>downstream</code> window which does not have trackbars. Usually, the downstream image obscures the main one on first show; you'll need to move it out of the way.</li>
<li>Tuner will save images separately on F2, but will combine the results of both, along with args (tuned parameters) and writes it to one json file when you press F3. Remember to keep your results compatible with json serialization.</li>
</ul>
<H4 id='carousel'>Carousels</H4>
A carousel is a group of images that you want tuner to deal with as a set. You typically want to do this to find parameters that work well across all images in the set. You are setting up a list of images (full path names) and specifying the parameters they need to be passed to.
<ul>
<li>Use the helper call <code>tuner.carousel_from_images()</code> to set up a carousel. This takes 2 lists.
<ul>
<li>The first is the list of names of parameters in <code>target</code> that take images. <code>target</code> might work with multiple images, and this list is where you specify the name of each parameter that expects an image.</li>
<li> The second is a list of image files (full path name). Each element of this list should be a tuple of file names.</li>
<ul>
<li>If <code>target</code> works with 2 images, then each element of this second list must be a tuple of two image paths.</li>
<li>If it works with three images, then each element must be a tuple of three image paths, et cetera. </li>
</ul>
</ul>
<li>When <code>Tuner</code> is aware of image files, it uses the file name in <code>ThetaUI</code>'s window title, (instead of just 'frame').</li>
<li>You can specify openCV imread codes to be used when reading files.</li>
<li>A video file can be used as a frame generator [untested as of April 2021]</li>
</ul>

<H4 id='explicit'>Why bother with explicit instantiation</H4>
<ul>
<li>Being able to tune hyper-parameters, or other control variables, without having them be parameters to your function. This keeps your signature what your auto-grader expects. Once ascertained, you should remove these from <code>Tuner</code></li>
<li>Process a <a href=#carousel>carousel of images</a>, remembering settings between images.</li>
<li>Insert a thumbnail into the main image (set <code>tuner.thumbnail</code> before you set <code>tuner.image</code>. This is useful, e.g., when you are matching templates. You could do this with <code>@TunedFunction()</code> as well.</li>
<li>View the results of <a href='#downstream'>two processes </a> in side by side windows. A few use cases for side-by-side comparison of images:
<ul>
<li>Show your pre-processing output in <code>main</code>; and traffic sign identification output in <code>downstream</code>.</li>
<li><code>match_template()</code> output in one vs. <code>harris_corners()</code> output in the other.</li>
<li>What your noble code found, vs. what the built in CV functions found (I find this view particularly revealing, also, character building).</li>
</ul>
<li>Controlling aspects of <a href='#gridsearch'><code>tuner.grid_search()</code></a>. Please see the docstrings for more information. </li>
<li>You get to control whether the GUI returns list items vs list indices; keys vs dict objects etc. </li>
<li>You get to create tuners by spec'ing them in json.</li>
<li>Finally, as anyone who has written a Decorator knows, things can get squirrelly when exceptions take place within a partial... you could avoid that whole mess with explicit instantiation of ThetaUI.</li>
</ul>

Apart from the few differences above, <code>ThetaUI</code> and <code>TunedFunction()</code> will give you pretty much the same UX. If none of the above are dealbreakers for you, stick with the decorator.

</p>

### OpenCV GUI
Your experience of this GUI is going to be determined by the version of various components - OpenCV, and the Qt backend. Tuner does take advantage of a couple of the features of the Qt backend, but those are guarded in <code>try</code> blocks, so you shouldn't bomb.
If you're in CS-6476, you've installed <code>opencv-contrib-python</code>. If not, might I suggest...

If you don't see the status bar in Tuner GUI, you are missing <code>opencv-contrib-python</code>
If you don't see the overlay menu, you are missing <code>Qt backend</code>

### Important Safety Tips
The accompanying <code>example.py</code> illustrates some uses. Refer to the docstrings for ThetaUI's interface for details. Play around, and let me know if you think of ways to improve this.

I've debugged this thing extensively, but I haven't had the time to bullet proof it. It will behave if your arguments are well behaved; but caveat emptor...

Arguments curried into your functions follow usual call semantics, so modifying those args will have the usual side effects. Accessing tuner.image always gives you a fresh copy of the image - but this is the exception.
<br>(tldr: work on a copy of the `image` parameter - not directly on it, or else side effects will accumulate...)

Don't forget to remove the @TunedFunction() decorator; the auto-grader won't much care for it :)

### Licensing
It's only licensed the way it is to prevent commercial trolling. For all other purposes...

```Fork it, make something beautiful.```