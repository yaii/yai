def toggleview(self, button):
  self.xml.viewmode = button.get_active()
  if self.xml.viewmode:
    self.xml.singleoutlayer()
  else:
    self.xml.unlockalllayers()

def run(self,button):
  pass

def setselect(self, inkscape, obj, arg1, arg2):
  #print "args", arg1, arg2
  if arg2 != "modify":
    print "Set selection",arg1, arg2

def select(self, inkscape, obj):
  print "Changed selection"
  self.xml.update()
  print self.xml.desktop
  selection = self.xml.selection
  if selection:
    self.editor.set_text(selection[0].repr.get(self.editor.prop,""))
  else:
    self.editor.set_text('')


if command == "toggleview":
    toggleview(self, button)
elif command == "run":
    run(self, button)
elif command == "changeselection":
    select(self, inkscape, obj)
elif command == "setselection":
    setselect(self, inkscape, obj, arg1, arg2)
