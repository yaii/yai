from xml import XML, name, pair
import pygtk
import gtk
import gtk.gdk
from literaleval import literal_eval

FRAMEWIDTH = 10
FRAMEHEIGHT = 24

def vadd(a,b):
  return map(sum,zip(a,b))

class Frametable:
  def __init__(self, numframes, xml):
    #Tracked item names
    self.xml = xml
    self.xml.numcols = numframes
    self.order = []
    #if self.xml.startscript:
    #  self.order = literal_eval(self.xml.startscript["order"])
    self.cells = None
    self.marked = []
    self.numframes = numframes
    #self.generate()

  def generate(self):
    """ Generate all UI elements. """
    print "Generating UI"

    scrolledwin = gtk.ScrolledWindow()
    self.scrollwin= scrolledwin
    scrolledwin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scrolledwin.set_size_request(300, 150)
    vbox = gtk.VBox()
    self.labels = vbox
    
    self.cells = CellGrid((len(self.order),self.numframes), self)
    self.addlabels()

    hbox = gtk.HBox()
    hbox.pack_start(vbox, expand=False, fill=True)

    innervbox = gtk.VBox()
    innerhbox = gtk.HBox()
    for i in xrange(self.numframes):
      label = gtk.Label(str(i%10))
      label.set_size_request(FRAMEWIDTH, FRAMEHEIGHT)
      innerhbox.pack_start(label, False)
    innervbox.pack_start(innerhbox, False)
    innervbox.pack_start(self.cells)
    hbox.pack_start(innervbox, False)

    scrolledwin.add_with_viewport(hbox)
    scrolledwin.show()
    vbox.show_all()
    hbox.show_all()
    self.update()
    return scrolledwin

  def addlabels(self):
    for name in ["Layers"] + self.order:
      hbox = gtk.HBox()
      label = gtk.Label(name)
      label.set_size_request(100,FRAMEHEIGHT)
      hbox.pack_start(label, False)
      btn = gtk.ToggleButton()
      btn.set_size_request(24,FRAMEHEIGHT)
      btn.connect('clicked', self.togglevisible, name)
      image = gtk.Image()
      image.set_from_file('/tmpfs/pyink/icons/object-visible.png')
      btn.add(image)
      hbox.pack_start(btn, False)

      btn = gtk.ToggleButton()
      btn.set_size_request(24,FRAMEHEIGHT)
      btn.connect('clicked', self.togglelock, name)
      image = gtk.Image()
      image.set_from_file('/tmpfs/pyink/icons/object-unlocked.png')
      btn.add(image)
      hbox.pack_start(btn, False)

      #self.labels.pack_start(btn, False)
      #self.labels.pack_start(label, False)
      self.labels.pack_start(hbox, False)

  def togglevisible(self, button, name):
    self.xml.togglevisible(name, button.get_active())

  def togglelock(self, button, name):
    self.xml.togglelock(name, button.get_active())

  def track(self):
    """ Track the current selection. """
    xml = self.xml
    if xml.selection:
      for node in xml.selection:
        if "-" not in node.repr["id"]:
          print "Changing name of %s to %s" % (node.repr["id"], node.repr["id"] + "-0")
          node.repr["id"] += "-0"
        print "Tracking %s" % pair(node.repr["id"])
        name,layer = pair(node.repr["id"])
        if name not in self.order:
          self.order.append(name)
          self.refresh()
          #Seems to cause missing parent crash. Not sure why yet.
          self.xml.updateroot(self.order)
        else:
          self.update()

  def refresh(self):
    for child in self.labels.get_children():
      self.labels.remove(child)
    self.addlabels()
    self.labels.show_all()
    self.cells.numrows = len(self.order)
    self.cells.resize()

  def paste(self, cut = False):
    if not self.cells.selected:
      print "No cell selected so no place to paste!"
      return
    xml = self.xml
    marked = self.cells.marked
    if len(marked) > 1:
      top,left = marked[0]

    sourcenames = [(self.order[row], col) for row,col in marked]
    sourcenodes = [xml.nodes.get(name(nodename)) for nodename in sourcenames]

    print "Selection",marked,self.order[0]

    if len(self.cells.selection) == 0:
      targets = [self.cells.selected]
    else:
      targets = self.cells.selection

    # Do not overwrite cells
    written = set()
    for target in targets:
      targetrow, targetcol = target
      if len(marked) > 1:
        newnames = [( self.order[row], targetcol + (col-left) )
                    for row,col in marked]
        #Don't overwrite any previous written cells in this run
        if any(newname in written for newname in newnames):
          continue
      else:
        newnames = [(self.order[targetrow], targetcol)]
      for node,newname in reversed(zip(sourcenodes, newnames)):
        print "Pasting",node,newname
        if xml.makecopy(node, newname):
          written.add(newname)
    if cut:
      for node in sourcenodes:
        if node and node.parent():
          node.parent().removeChild(node)
      self.cells.marked = set()
    self.update()
    self.cells.queue_draw()
    self.xml.commit("EditPaste", "Paste cells")
    #self.xml.desktop.doc().done("EditPaste", "Paste cells")

  def update(self):
    self.xml.update()
    entries = [(i, j) for i,basename in enumerate(self.order)
               for j in xrange(self.numframes)
               if name(basename, j) in self.xml.nodes]
    self.cells.entries = set(entries)
    self.cells.queue_draw()

  def matchselection(self, totable = True):
    """ Sync table and inkscape selections. """
    xml = self.xml
    self.update()
    if not totable: #from table to inkscape
      #Maybe we shouldn't touch untracked nodes
      xml.selector.clear()
      for rowcol in self.cells.selection:
        if rowcol in self.cells.entries:
          row,col = rowcol
          node = xml.nodes[name(self.order[row],col)]
          xml.selector.add(node.spitem)
    else: #to table from inkscape
      print xml.selection
      for row,col in self.cells.entries:
        node = xml.nodes.get(name(self.order[row], col))
        if node:
          if type(node) == list:
            #Uh oh.
            node = node[0]
          if node.spitem in xml.selection:
            self.cells.select((row,col))
          else:
            self.cells.unselect((row,col))

class CellGrid(gtk.DrawingArea):
  """ A representation of current frames and selections. """
  def __init__(self, dimensions, container = None):
    gtk.DrawingArea.__init__(self)
    self.numrows, self.numcols = dimensions
    self.container = container
    print "Creating table of size %s x %s" % dimensions
    #Single cell special selection
    self.selected = None
    #Separate multi-cell selection
    self.selection = set()
    self.nonempty = set()
    self.entries = set()
    self.marked = []
    self.hover = None

    self.connect('expose-event', self.expose)
    self.connect("configure_event", self.config)
    self.connect('motion-notify-event', self.mousemove)
    self.connect('button-press-event', self.click)
    #Needs to be wrapped in an event box
    #self.connect('leave-notify-event', self.mousemove)
    #self.connect('focus-out-event', self.mousemove)
    self.set_size_request(self.numcols * FRAMEWIDTH, self.numrows * FRAMEHEIGHT)
    print self.numcols * FRAMEWIDTH, self.numrows * FRAMEHEIGHT

  def resize(self):
    self.numrows = len(self.container.order)
    self.set_size_request(self.numcols * FRAMEWIDTH, self.numrows * FRAMEHEIGHT)

  def click(self, widget, event):
    self.container.matchselection(totable = True)
    mods = event.state.value_names
    #Should replace self.rows by an dictionary with reverse lookup.
    #invmap = dict((v,k) for k, v in self.rows.items())
    colnum = int(event.x / FRAMEWIDTH)
    rownum = int(event.y / FRAMEHEIGHT)
    if 0 <= rownum < self.numrows and 0 <= colnum < self.numcols:
      ij = (rownum, colnum)
    else:
      ij = None

    print rownum,colnum
    if ij is not None:
      if "GDK_CONTROL_MASK" in mods:
        self.toggle(ij)
        self.queue_draw()
      elif "GDK_SHIFT_MASK" in mods:
        if self.selected != ij:
          if self.selected is not None:
            oldrow,oldcol = self.selected
            rowrange = xrange(min(oldrow,rownum), max(oldrow,rownum)+1)
            colrange = xrange(min(oldcol,colnum), max(oldcol,colnum)+1)
            for newrow in rowrange:
              for newcol in colrange:
                print "Selecting %s,%s" % (newrow, newcol)
                self.select((newrow,newcol))
                self.drawcell(newrow,newcol)
      if "GDK_SHIFT_MASK" not in mods:
        if self.selected != ij:
          self.selectcell(ij)
          self.selected = ij
          self.container.xml.selectlayer(*ij)

      #print mods, ("GDK_SHIFT_MASK" not in mods), ("GDK_CONTROL_MASK" in mods)
      if "GDK_SHIFT_MASK" not in mods and "GDK_CONTROL_MASK" not in mods:
        #Clear selection
        print "Clearing selection"
        self.selection = set()
        self.selection.add(ij)
        self.queue_draw()
      self.container.matchselection(totable = False)
    print event,colnum

  def mousemove(self, widget, event):
    #print "mousemove",event.type
    if event.type == gtk.gdk.LEAVE_NOTIFY:
      self.hover = None
    else:
      self.hover = (int(event.y / FRAMEHEIGHT), int(event.x / FRAMEWIDTH))
    if self.hover[1] >= self.numcols or self.hover[0] >= self.numrows:
      self.hover = None
    self.queue_draw()

  def config(self, widget, event):
    #print "config called"
    self.gc = gtk.gdk.GC(self.window)
    emask = self.window.get_events()
    emask = emask | gtk.gdk.BUTTON_PRESS_MASK | \
        gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.FOCUS_CHANGE_MASK
    self.window.set_events(emask)

    return True
  
  def expose(self, area, event):
    #x , y, width, height = event.area
    self.draw()

  def mark(self):
    if self.selection:
      self.marked = list(self.selection)
      self.marked.sort()
      self.marked.reverse()
    else:
      self.marked = [self.selected]
    print "Marked", self.marked
    self.queue_draw()

  def setcol(self, colname):
    col = gtk.gdk.color_parse(colname)
    self.gc.set_rgb_fg_color(col)
    
  def selectcell(self,i):
    self.selected = i
    self.queue_draw()

  def toggle(self,i):
    if i in self.selection:
      self.selection.remove(i)
    else:
      self.selection.add(i)

  def select(self,i):
    self.selection.add(i)

  def unselect(self,i):
    if i in self.selection:
      self.selection.remove(i)

  def drawrect(self, xy, wh, filled = False, colname = None):
    if colname:
      self.setcol(colname)
    self.window.draw_rectangle(self.gc, filled, xy[0], xy[1], wh[0], wh[1])

  def drawcell(self,*ij):
    #Using row major ordering...
    xy = (FRAMEWIDTH*ij[1],FRAMEHEIGHT*ij[0])
    wh = (FRAMEWIDTH,FRAMEHEIGHT-1)
    if ij in self.marked:
      self.drawrect(xy, wh, True, "#dd00dd")
    elif ij in self.selection:
      self.drawrect(xy, wh, True, "#00dddd")
    else:
      self.drawrect(xy, wh, True, "white")

    if ij in self.entries:
      self.drawrect(vadd(xy,(3,6)), vadd(wh,(-5,-7)), True, "black")
    self.drawrect(xy, wh, False, "#aaaaaa")

    if self.hover == ij:
      self.drawrect(vadd(xy,(2,1)), vadd(wh,(-4,-3)), False, "#a0a0a0")
      
    if self.selected == ij:
      self.drawrect(vadd(xy,(2,1)), vadd(wh,(-4,-3)), False, "#ee2222")

  def draw(self):
    self.gc.set_line_attributes(1, gtk.gdk.LINE_SOLID,
                                gtk.gdk.CAP_BUTT, gtk.gdk.JOIN_MITER)
    for i in xrange(self.numrows):
      for j in xrange(self.numcols):
        self.drawcell(i,j)

if __name__ == '__main__':
  window = gtk.Window(gtk.WINDOW_TOPLEVEL)
  window.connect("destroy", lambda w: gtk.main_quit())

  grid = CellGrid((2,40))
  #grid.set_size_request(300, 20)

  #grid.select(3)
  #grid.select(5)
  #grid.unselect(6)

  table = Frametable(40)
  win = table.generate()
  table.cells.entries = set([(0,0),(0,1)])
  #table.cells.draw()

  box = gtk.VBox(False, 0)

  #box.pack_start(grid, False)
  #box.pack_start(table.scrollwin, False)
  box.pack_start(win, False)
  window.add(box)
  grid.show()
  box.show()
  window.show()
  gtk.main()
