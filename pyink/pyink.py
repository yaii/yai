import pybInkscape
import pygtk
import gtk
import os
from yai import Wrapper

alldesktops = []
wrappers = []

def act_desktop(inkscape, ptr):
  """ Handler for desktop activation events."""
  # Get Python wrapper of SPDesktop passed by ptr.
  desktop = pybInkscape.GPointer_2_PYSPDesktop(ptr)
  # In think there may be a problem with testing equality here...
  print "A desktop has connected: %s" % desktop
  print "All known desktops: %s" % alldesktops

  top = desktop.getToplevel()
  if not top:
    print "But there were no active top window."
    #For some reason getToplevel doesn't work properly on Windows.
    if os.name != "nt":
      return
  if desktop in alldesktops:
    print "But that desktop is already initialized."
    index = alldesktops.index(desktop)
    wrapper = wrappers[index]
    wrapper.xml.desktop = desktop
    return

  alldesktops.append(desktop)

  wrapper = Wrapper(desktop,top,inkscape)
  wrapper.show()
  wrapper.alldesktops = alldesktops
  wrappers.append(wrapper)

def deact_desktop(inkscape, ptr):
  print "Deactivating desktop!"
  desktop = pybInkscape.GPointer_2_PYSPDesktop(ptr)
  index = alldesktops.index(desktop)
  print "Number %s" % index
  wrapper = wrappers[index]
  wrapper.xml.desktop = None

def pyink_start():
  print "Starting pyink and waiting for active desktop to connect"
  pybInkscape.inkscape.connect('activate_desktop', act_desktop)
  pybInkscape.inkscape.connect('deactivate_desktop', deact_desktop)
