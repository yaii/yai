# Frametable functions

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
  #self.frametable.update()
  self.xml.update()
  entries = [(i, j) for i,basename in enumerate(self.order)
             for j in xrange(self.numframes)
             if name(basename, j) in self.xml.nodes]
  self.cells.entries = set(entries)
  self.cells.queue_draw()

def matchselection(self, totable = True):
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

# All interpolation related

def addsplines(self):
  print "Adding splines"
  #I suppose the source node transform isn't used and can be removed...
  from terptest import PiecewiseLinear
  def addterp(node, allframes, anims, transform = None, alltransf = None, Terp = None):
    """ Add terp for a node stored in anims (because we can't add fields to nodes (and it creates problems with references and pointers anyway)). Possibly recursively. Also changes the id of all affected nodes. """
    basename = pair(node["id"])[0]
    node["id"] = name(basename,"anim")
    anims[node["id"]] = {}
    print node["id"],allframes[0].name()
    if not alltransf:
      alltransf = [None for f in allframes]

    if node.get("style"):
      style = unserattrib(node["style"])
      for attrib in ['fill-opacity', 'stroke-opacity','opacity']:
        if attrib in style:
          data = []
          for i,frame in enumerate(allframes):
            if frame.get("style"):
              fstyle = unserattrib(frame["style"])
            else:
              fstyle = {}
            opacity = float(fstyle.get(attrib,"1"))
            data.append(opacity)
          anims[node["id"]]["style.%s" % attrib] = CubicSpline(data)

    if node.name() == 'svg:path':
      data = []
      for i,frame in enumerate(allframes):
        data.append(SVGPath(frame["d"],transform=alltransf[i]))
      cols = data[0].cols
      anims[node["id"]]["d"] = SVGCurveanim(data, cols=cols, interpolator=Terp)
    elif node.name() == 'svg:image':
      #x,y = node["x"],node["y"]
      data = [P(float(frame["x"]),float(frame["y"])) for frame in allframes]
      print "data", data
      print "transf", transform
      print "alltransf", alltransf
      if alltransf:
        data = [p.transform(gettransform(alltransf[i])) for i,p in enumerate(data)]
      anims[node["id"]]["xy"] = CubicSpline(data)
      #data = [float(frame["y"]) for frame in allframes]
      #anims[node["id"]]["y"] = CubicSpline(data)
      
    elif node.name() == 'svg:g':
      #Need to simultaneously traverse the tree in all frames...
      #childterpnodes = []

      #childterpnodes.append(terpnode(curnode,curallframes))
      while curnode:
        #print "curnode",curnode["id"],curnode,curallframes
        addterp(curnode,curallframes,anims,newtransf, newalltransf, Terp)
        curnode = curnode.next()
        curallframes = [f.next() for f in curallframes]

  xml = self.xml
  entries = list(self.cells.entries)
  entries.sort()
  objs = {}
  order = []
  for row,col in entries:
    basename = self.order[row]
    node = xml.nodes.get(name(basename,col))
    if node:
      if basename not in objs:
        objs[basename] = []
        order.append(basename)
      objs[basename].append(node)
  allrows = sorted(list(set(row for row,col in entries)))
  mins = [min([col for row,col in entries if row==currow])
          for currow in allrows]
  maxs = [max([col for row,col in entries if row==currow])
          for currow in allrows]
  data = {}
  anims = {}
  for basename in order:
    data[basename] = []
    allframes = objs[basename]
    basenode = xml.nodes.get(name(basename,"properties"))
    if not basenode:
      basenode = allframes[0]
    newnode = xml.makecopy(basenode, (basename,"anim"))
    addterp(newnode, allframes, anims)
    #nodes gets new nodes every time because of the way childList works (a new wrapper is used every time)!

  self.anims = anims
  self.animobjs = objs
  self.timetransf = {}

def gentimetransf(self):
  xml = self.xml
  entries = list(self.cells.entries)
  entries.sort()
  allrows = sorted(list(set(row for row,col in entries)))
  cols = [[col for row,col in entries if row==currow] for currow in allrows]
  for row in allrows:
    pass
  """
  for row,col in entries:
    basename = self.order[row]
    node = xml.nodes.get(name(basename,col))
    if node:
      if basename not in objs:
        objs[basename] = []
        cols[basename] = []
        order.append(basename)
        cols.append(col)
      objs[basename].append(node)
      cols[basename].append(col)

    animname = name(basename,"anim")
    if animname in self.anims:
      objs = self.objs[basename]
  """

def anim(self,t=0.3,order=None):
  def setattrib(node, t):
    for attrib in ['fill-opacity', 'stroke-opacity','opacity']:
      if ("style.%s" % attrib) in self.anims[node["id"]]:
        style = unserattrib(node["style"])
        val = str(self.anims[node["id"]]["style.%s" % attrib].getpoint(t))
        style[attrib] = val
        node["style"] = serattrib(style)

    if node.name() == "svg:path":
      #cmds = node.pystore["terp"].getcommands(t)
      timetransf = self.timetransf.get(node["id"])
      if timetransf:
        t = timetransf(t)
      cmds = self.anims[node["id"]]["d"].getcommands(t)
      attribs = commandstodict(cmds)
      #print attribs
      #node = xml.makecopy(basenode, (basename,"anim"))
      node["d"] = attribs["d"]
    elif node.name() == 'svg:image':
      #print self.anims[node["id"]]["xy"].getpoint(t)
      node["x"],node["y"] = map(str,self.anims[node["id"]]["xy"].getpoint(t).tuple())
    elif node.name() == "svg:g":
      timetransf = self.timetransf.get(node["id"])
      if timetransf:
        t = timetransf(t)
      for child in node.childList():
        setattrib(child,t)

  self.xml.update()
  if not order:
    order = self.order
  for basename in order:
    if name(basename,"anim") in self.anims:
      #print "Animating",basename
      newnode = self.xml.nodes[name(basename,"anim")]
      #newnode = self.anims[basename]
      #cmds = self.anims[basename].getcommands(t)
      setattrib(newnode,t)

# Framerow functions

def mark(self):
  if self.selection:
    self.marked = list(self.selection)
    self.marked.sort()
    self.marked.reverse()
  else:
    self.marked = [self.selected]
  print "Marked", self.marked
  self.queue_draw()

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

if command == "mark":
  mark(self)
elif command == "paste":
  paste(self, cut)
elif command == "click":
  click(self, widget, event)
elif command == "update":
  update(self)
elif command == "refresh":
  refresh(self)
elif command == "match":
  matchselection(self, totable)
elif command == "selectlayer":
  selectlayer(self,selrow,selcol)
elif command == "track":
  track(self)
elif command == "singleoutlayer":
  singleoutlayer(self)
elif command == "unlockalllayers":
  unlockalllayers(self)
elif command == "addsplines":
  addsplines(self)
elif command == "anim":
  anim(self,t,order)
