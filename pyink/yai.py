import gtk
import frametable, animator
from ipyconsole import IPythonView
from xml import XML
from literaleval import literal_eval
import pybInkscape

class Wrapper:
  def __init__(self, desktop, window, inkscape):
    self.xml = XML(desktop)
    self.window = window
    self.top = None
    root = desktop.doc().root().repr
    #print "Desktop root",root
    #ns = "http://yai.heroku.com/"
    #self.xml.root.setAttribute("xmlns:yai", ns)
    #print "Set namespace!"

    inkscape.connect('change_selection', self.changesel)
    inkscape.connect('set_selection', self.setsel,"set")
    inkscape.connect('modify_selection', self.setsel,"modify")

  def show(self):
    if self.top == None:
      self.top = gtk.VBox(False, 0)
      if not self.window:
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.show()
        print "Created a new top window since no top window was found", self.window
        toplevel = self.window
        toplevel.add(self.top)
      else:
        toplevel = self.window #self.xml.desktop.getToplevel()
        toplevel.child.child.pack_end(self.top, expand=False)
    else:
      self.top.remove(self.outerbox)

    vbox = gtk.VBox(False, 0)
    self.outerbox = vbox
    self.top.pack_start(vbox, expand=False)

    #ScrollWindow containing the IPython console
    scrolledwin = gtk.ScrolledWindow()
    scrolledwin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    self.ipv = IPythonView(user_global_ns = {"wrap":self})
    scrolledwin.add_with_viewport(self.ipv)
    scrolledwin.set_size_request(-1,300)
    self.ipv.connect('size-allocate', self.changedv)
    vbox.pack_start(scrolledwin, expand=False)

    self.frametable = frametable.Frametable(40, self.xml)
    ui = self.frametable.generate()
    vbox.pack_start(ui, expand=False)

    hbox=gtk.HBox(False, 0)
    self.editor = gtk.Entry()
    self.editor.prop = "id"
    self.editor.connect('activate', self.pressbutton, "Set")
    self.addbuttons(hbox)
    self.buttonbox = hbox
    vbox.pack_start(hbox, expand=False)
    
    #Second row (buttons)
    self.console = gtk.Entry()
    self.console.connect('activate', self.eval)
    vbox.pack_start(self.console, expand=False)

    hbox = gtk.HBox(False, 0)
    adj = gtk.Adjustment(lower=0,upper=3)
    btn = gtk.Button("Interpolate")
    btn.connect('clicked', self.pressbutton, "Interpolate")
    hbox.pack_start(btn, expand=False, fill=False)
    hscroll = gtk.HScale(adj)
    hscroll.set_digits(2)
    spinbutton = gtk.SpinButton(adj, digits = 2)
    hbox.pack_start(hscroll)    
    hbox.pack_start(spinbutton, expand=False)

    def valadj(adj):
      self.animator.anim(adj.get_value())
    adj.connect("value-changed",valadj)
    self.animadj = adj
    self.animscroll = hscroll

    vbox.pack_start(hbox)

    self.top.show_all()

    self.animator = animator.Animator(self.xml)

    return False

  def changedv(self, widget, event, data=None ):
    """ Callback. Scrolled in console."""
    adj = widget.parent.get_vadjustment()
    adj.set_value(adj.upper - adj.page_size)

  def addbutton(self, name, func):
    """ Add new button `name` executing the function `func`. """
    btn = gtk.Button(name)
    btn.connect('clicked', func)
    self.buttonbox.pack_start(btn, expand=False, fill=False)
    btn.show()

  def addbuttons(self, hbox):
    """ Add default buttons."""
    buttons = ["Mark", "Paste", "PasteCut", "Refresh", "Run",
               "Track", "Reload code", "Set"]
    for name in buttons:
      btn = gtk.Button(name)
      btn.connect('clicked', self.pressbutton, name)
      hbox.pack_start(btn, expand=False, fill=False)

    hbox.pack_start(self.editor,expand=False,fill=False)

    self.buttons = {}
    btn = gtk.ToggleButton("Layerview")
    btn.connect('clicked', self.togglelayerview)
    self.buttons["Layerview"] = btn
    hbox.pack_start(btn, expand=False, fill=False)
    #btn.set_active(True)
    btn = gtk.ToggleButton("Anim layer")
    btn.connect('clicked', self.toggleanimlayer)
    self.buttons["Anim layer"] = btn
    hbox.pack_start(btn, expand=False, fill=False)

  def changesel(self,inkscape,obj):
    print "Changed selection"
    self.xml.update()
    print self.xml.desktop
    selection = self.xml.selection
    if selection:
      self.editor.set_text(selection[0].repr.get(self.editor.prop,""))
    else:
      self.editor.set_text('')

  def togglelayerview(self, button = None):
    viewmode = self.buttons["Layerview"].get_active()
    self.xml.saveopt("layerview", viewmode)
    if viewmode:
      self.xml.singleoutlayer()
    else:
      self.xml.unlockalllayers()

  def toggleanimlayer(self, button = None):
    visible = self.buttons["Anim layer"].get_active()
    self.xml.saveopt("animlayer", visible)
    animlayer = self.xml.nodes.get("layer-anim")
    print "Toggling animlayer visibility"
    if not animlayer: return
    if visible:
      animlayer['style'] = 'display:inline;opacity:1'
    else:
      animlayer['style'] = 'display:none'

  #Unused for the moment.
  def setsel(self,inkscape,obj,arg1,arg2):
    if arg2 != "modify":
      print "Set selection",arg1, arg2

  def pressbutton(self, button, event):
    self.xml.update()
    if event == "Mark":
      self.frametable.cells.mark()
    elif event == "Paste":
      self.frametable.paste()
    elif event == "PasteCut":
      self.frametable.paste(cut = True)
    elif event == "Refresh":
      self.frametable.refresh()
      self.frametable.update()
    elif event == "Track":
      self.frametable.track()
    elif event == "Run":
      self.animator.run()
    elif event == "Reload code":
      import xreload
      import yai, xml
      xreload.xreload(frametable)
      xreload.xreload(animator)
      xreload.xreload(yai)
      xreload.xreload(xml)
    elif event == "Set":
      self.xml.update()
      obj = self.xml.selection[0]
      obj.repr[self.editor.prop] = self.editor.get_text()
      self.frametable.update()
    elif event == "Interpolate":
      #self.frametable.addsplines()
      order = self.frametable.order
      entries = self.frametable.cells.entries
      objs, order = self.xml.allrows(order, entries)
      self.animator.addanims(order, objs)
      self.animator.timetransf = self.xml.gettimetransforms(order, entries)
      #Needs a custom verb here...
      self.xml.commit("EditPaste", "Add anim")
      #self.xml.desktop.doc().done("EditPaste", "Add anim")

  def eval(self, widget):
    cmd = self.console.get_text()
    self.xml.update()
    print "Executing %s" % cmd
    exec cmd

  def load(self):
    fv = pybInkscape.verb_getbyid('FileOpen')
    loadfile = fv.get_action(self.xml.desktop)
    loadfile.perform()
    def loadopt(key, default = "None"):
      return literal_eval(self.xml.startscript.get(key,default))
    self.xml.update()
    self.frametable.order = loadopt("order","[]")
    self.frametable.cells.selected = loadopt("cells-selected")
    self.frametable.cells.selection = set(loadopt("cells-selection","[]"))
    self.buttons["Layerview"].set_active(loadopt("layerview", "False"))
    self.buttons["Anim layer"].set_active(loadopt("animlayer", "False"))
    self.togglelayerview()
    self.toggleanimlayer()
    self.frametable.refresh()
    self.frametable.update()

  #Need to somehow auto-save on file save
  def save(self):
    self.xml.saveopt("cells-selected",self.frametable.cells.selected)
    self.xml.saveopt("cells-selection",list(self.frametable.cells.selection))
    viewmode = self.buttons["Layerview"].get_active()
    self.xml.saveopt("layerview", viewmode)
    visible = self.buttons["Anim layer"].get_active()
    self.xml.saveopt("animlayer", visible)
    self.xml.updateroot(self.frametable.order)
    #self.xml.startscript["order"] = str(self.order)
    fv = pybInkscape.verb_getbyid('FileSave')
    savefile = fv.get_action(self.xml.desktop)
    savefile.perform()
