I'm putting this out there because someone suggested it and mostly to gauge (lack of) interest and possibly open up discussion if there's any to be had.

I've made some modifications to Inkscape for my own use. Current final results here:

* http://gfycat.com/CarefulImpishDuck
* http://gfycat.com/WiltedSardonicAsiantrumpet
* http://gfycat.com/WillingWiltedFrog

While we are here though, I may as well ask this.

I'd like to make this publicly available (open source) eventually. A small portion could really benefit from being in the Inkscape trunk (if its kept up to date with rewrites within) as an extension of sort. I have no idea what policies there are and so no real handle on how likely this is, which is why I'm asking.

Another reason I'm asking now is to get an idea of how much time I should spent cleaning up and packaging this thing and how much should be spent making it useful for myself.

What I'm making available here is a bit cleaned up but still not all that pretty so brace your eyes!

# What is this? #

Some Inkscape Python binding, a GTK IPython console and a sample UI for making animation.

# Credits #

Before going any further though, I should say that most of this code is _not_ mine and mostly what I've done is just connect them together.

## MadButterfly ##

Most of this is based on [MadButterfly](http://madbutterfly.sourceforge.net/) by ThinkerLi (and others?), or at least the `pybind` portion of it. Or maybe that's the project you want instead of this one. While writing this, I found the author has [Youtube channel](https://www.youtube.com/watch?v=M9RutrTWaHY) with some demos of that. Here's [some instructions useful links](https://www.assembla.com/spaces/MadButterfly/wiki/Scribboo) for MadButterfly.

I was not able to find activity on this project post-2011.

## IPython console ##

The GTK IPython console is modified from Eitan Isaacson's work. (This part is optional.)

## xreload.py ##

It also includes a modified version of `xreload.py` which is stuck in [sandbox](http://svn.python.org/projects/sandbox/trunk/xreload/xreload.py) forever. (This part is optional.)

# Dependencies #

Inkscape's dependencies plus

* Python 2.x (including header files) Versions 2.5 to 2.7 work, I haven't tried others.
* PyGTK (pretty huge, may eventually not be needed)
* Cython (to build and may not be needed even for that if a pre-compiled `.cpp` file is distributed) Version at least 0.17 I think but I've been using 0.22 lately

Also needs IPython 0.8 (currently bundled with) for the ipython console.

# Compiling and running #

Compile Inkscape

    ./autogen.sh  # Needed because the included files are no good.
    mkdir build
    cd build
    ../configure --with-python
    make

or however you do that usually. :)

Add path to `pyink` python module

    export PYTHONPATH=/path/to/pyink

and run the compiled `inkscape`.

For the sample animation UI, in preferences change paths to use absolute and repeated coordinates!

How the extra parts work depends on which version of pyink is used (see the pyink related repos).

# Inner workings #

A Cython binding for some of Inkscape's C functions so that Python can call them (post compilation). Then at start up, it looks for the `pyink` python module (name hard coded for now), imports it and calls `pyink.pyink_start()`.

From there some signals are connected for when the desktop becomes active. When it does, a wrapper is created from the desktop and the real fun starts. The XML document is connected and read, extra UIs are added.

# Potential uses #

Prototyping, animation, as an editor for other things not vector graphics.

# Sample UI: Animation #

To document.

# Caveats #

There are definitely known bugs.

## Entry point ##

There's an obvious entry point in `inkscape.cpp`

    Inkscape::PyBind::init();

(and `pybind.h` include) but its probably movable elsewhere.

## Cython ##

Most of the bindings are written in Cython, which means if something internal changes that affects these bindings, someone who knows Cython (a mix of C and Python) needs to make the right changes.

## Style ##

I've left most of ThinkerLi's original comments and some code in there but some code has weird style because of it, like C style comments instead of python triple quote...

## GObjects ##

Most calls to `gobj_api.newgobj` will crash. It just so happens the `pyink.py` module I'm using won't.

## UI exposure ##

Because there's an interpreter some functions are not available through some UI element (yet) and need to be called directly (such as `wrap.load` and `wrap.frametable.load`).

Some things that should be automatic are not (because they may still be buggy) such as calling `wrap.xml.update()` after some operations.

## Helper functions ##

There are some helper functions in `simple-node.cpp` that could obviously be moved to the Cython part instead.
