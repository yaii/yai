from xml import XML, name, pair
from svg.svgobject import *
from svg.svghelp import unserattrib, serattrib
import gtk

class Animator:
  def __init__(self, xml):
    self.props = {}       # Interpolated properties.
    self.ttransf = {}     # Time transforms for individual objects
    self.xml = xml
    self._t = 0
    self.order = None

  def addterp(self, node, allframes, anims, transform = None, alltransf = None, Terp = None):
    """ Add terp for a node stored in anims (because we can't add fields to nodes (and it creates problems with references and pointers anyway)). Possibly recursively. Also changes the id of all affected nodes. """
    basename = pair(node["id"])[0]
    node["id"] = name(basename,"anim")
    anims[node["id"]] = {}
    print node["id"]#,allframes[0].name()
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
    newtransf = gettransform(node.get("transform",None))
    #print "new transform!",newtransf,transform,composetransform(newtransf,transform)
    newtransf = composetransform(transform,newtransf)
    if node.get("transform"):
      del node["transform"]

    #Should probably delete the existing transform if there is one.


    #print "allframes",allframes
    for i,f in enumerate(allframes):
      try:
        f.get("transform")
      except:
        print i,f
    newalltransf = [composetransform(alltransf[i],
                                     gettransform(f.get("transform",None)))
                    for i,f in enumerate(allframes)]


    if "clip-path" in node.keys():
      #Duplicate the defs clip-path node first (this is actually just a dummy)
      #Then add a clippath child node to the -anim copy of the clip-path bearing node.
      #Now every time this clippath child is updated, the defs duplicate is updated accordingly.

      #Duplicate defs
      clippathname = re.findall(r'url\(#(.*)\)',node["clip-path"])[0]
      clippath = self.xml.nodes[clippathname]
      # Not sure why we are duplicating the first child here...
      # I think it is because the first child should always be the clippath
      duplicate = node.firstChild().duplicate(node.document())
      duplicate["id"] = clippath["id"] + "-anim"
      olddup = self.xml.nodes.get(duplicate["id"])
      if olddup:
        #print "id:",olddup["id"]
        #print "clip:",clippath["id"]
        #clippath.parent().removeChild(olddup)
        if olddup.parent():
          olddup.parent().removeChild(olddup)
      print "clip-path",clippath["id"]
      print "clip-path parent",clippath.parent()["id"]
      clippath.parent().addChild(duplicate, clippath)
      #newid = node.firstChild()["id"]
      #duplicate = clippath.duplicate(clippath.document())
      #duplicate["id"] = duplicate["id"] + suffix
      #newid = self.xml.dupclip(node,"-anim")
      #print "Newid",newid

      #?? No child actually added
      #Currently, the clip-path children have to be added manually to each frame first before interpolating
      node["clip-path"] = "url(#%s)" % duplicate["id"]

      for child in node.children():
        if "defnode" in child.keys() and child["defnode"] == clippathname:
          child["defnode"] = duplicate["id"]
      #This should be sufficient but Inkscape doesn't render properly when interpolating.
      #Change path to an svg:use...
      

    if node.name() == 'svg:path':
      data = []
      #print "newalltransf",newalltransf
      for i,frame in enumerate(allframes):
        #data.append(SVGPath(frame["d"],transform=alltransf[i]))
        #print "frame[d]",i,frame["d"]
        data.append(SVGPath(frame["d"],transform=newalltransf[i]))
      cols = data[0].cols
      #if node.get("transform"):
      #  del node["transform"]
      anims[node["id"]]["d"] = SVGCurveanim(data, cols=cols, interpolator=Terp)
      #anims[node["id"]]["d"] = SVGCurveanim(data, cols=cols)
      #Temporarily disable clip-paths
      #if False and "clip-path" in node.keys():

    if "clip-path" in node.keys():
      #xml = self.xml
      #clippath = xml.makeclip(node,"-anim")
      #duplicate = clippath.duplicate(clippath.document())
      #duplicate["id"] = duplicate["id"] + "-copy"
      #node.appendChild(duplicate)
      curnode = node.firstChild()
      curallframes = [f.firstChild() for f in allframes]

      #childterpnodes.append(terpnode(curnode,curallframes))
      while curnode:
        #print "curnode",curnode["id"],curnode,curallframes
        self.addterp(curnode,curallframes,anims,newtransf, newalltransf, Terp)
        curnode = curnode.next()
        curallframes = [f.next() for f in curallframes]

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

    elif node.name() in ['svg:g', "svg:clipPath", 'svg:use', 'svg:defs']:
      #Need to simultaneously traverse the tree in all frames...
      #childterpnodes = []

      curnode = node.firstChild()
      curallframes = [f.firstChild() for f in allframes]

      #childterpnodes.append(terpnode(curnode,curallframes))
      while curnode:
        #print "curnode",curnode["id"],curnode,curallframes
        self.addterp(curnode,curallframes,anims,newtransf, newalltransf, Terp)
        curnode = curnode.next()
        curallframes = [f.next() for f in curallframes]

  def addanims(self, order, objs):
    print "Adding animation objects"
    #I suppose the source node transform isn't used and can be removed...
    from terptest import PiecewiseLinear

    xml = self.xml
    #objs, order = xml.allrows()
    data = {}
    props = {}
    for basename in order:
      if basename not in objs: continue
      data[basename] = []
      allframes = objs[basename]
      basenode = xml.nodes.get(name(basename,"properties"))
      if not basenode:
        basenode = allframes[0]
      newnode = xml.makecopy(basenode, (basename,"anim"))
      self.addterp(newnode, allframes, props)
      #xml.update()
      #nodes gets new nodes every time because of the way childList works (a new wrapper is used every time)!

    self.props = props
    self.animobjs = objs
    self.timetransf = {}
    self.order = order

  def setattrib(self, node, t):
    timetransf = self.timetransf.get(node["id"])
    if timetransf:
      t = timetransf(t)

    if node["id"] in self.props:
      for attrib in ['fill-opacity', 'stroke-opacity','opacity']:
        if ("style.%s" % attrib) in self.props[node["id"]]:
          style = unserattrib(node["style"])
          val = str(self.props[node["id"]]["style.%s" % attrib].getpoint(t))
          style[attrib] = val
          node["style"] = serattrib(style)

    if node.name() in ["svg:g","svg:clipPath", 'svg:use'] or "clip-path" in node.keys():
      for child in node.childList():
        self.setattrib(child,t)

    if node.name() == "svg:path":
      #cmds = node.pystore["terp"].getcommands(t)
      cmds = self.props[node["id"]]["d"].getcommands(t)
      attribs = commandstodict(cmds)
      #print attribs
      #node = xml.makecopy(basenode, (basename,"anim"))
      node["d"] = attribs["d"]
      if "clip-path" in node.keys():
        #print node["clip-path"]
        #self.xml.replaceclip(node, node.firstChild())
        pass
    elif node.name() == 'svg:clipPath':
      if "defnode" in node.keys():
        duplicate = node.duplicate(node.document())
        oldclip = self.xml.nodes[node["defnode"]]
        self.xml.overwrite(oldclip, duplicate)
      #self.xml.dupclip(node)
      #self.xml.replaceclip(node.parent(), node)
    elif node.name() == 'svg:image':
      #print self.props[node["id"]]["xy"].getpoint(t)
      node["x"],node["y"] = map(str,self.props[node["id"]]["xy"].getpoint(t).tuple())
    elif node.name() == "svg:g":
      if "yai:choice" in node.keys():
        childindex = int(node["yai:choice"])
        for index,child in enumerate(node.childList()):
          self.xml.hide(child, index == childindex)

  def run(self, maxt, firstt = 0, gtimetransf = None):
    #self.gtimetransf = gtimetransf
    #self.maxt = maxt
    if not gtimetransf:
      gtimetransf = lambda t: t

    self.dummyt = firstt
    def step(self):
      self.dummyt += 0.1
      #print "Setting ", self.dummyt, self._t
      if self.dummyt < maxt:        
        self.anim(gtimetransf(self.dummyt))
        gtk.timeout_add(100,step,self)
    gtk.timeout_add(100,step,self)

  def export(self, maxt, firstt = 0, increment = 0.1, gtimetransf = None):
    import os, pybInkscape
    #self.gtimetransf = gtimetransf
    #self.maxt = maxt
    if not gtimetransf:
      gtimetransf = lambda t: t

    inname = self.xml.getopt("export-infile")
    outname = self.xml.getopt("export-outfile")
    zoom = float(self.xml.getopt("export-zoom"))
    fv = pybInkscape.verb_getbyid('FileSave')
    savefile = fv.get_action(self.xml.desktop)
    self.dummyt = firstt
    while self.dummyt < maxt:
      self.anim(gtimetransf(self.dummyt))
      savefile.perform()
      print "rsvg -x %s -y %s %s %s-%s.png" % (zoom,zoom,inname,outname,self.dummyt)
      os.system("rsvg -x %s -y %s %s %s-%05d.png" % (zoom,zoom,inname,outname,self.dummyt*1000))
      #self.dummyt += 0.01
      self.dummyt += increment

  def anim(self,t):
    self.sett(t,self.order)

  def sett(self,t,order):
    xml = self.xml
    xml.update()
    self._t = t
    for basename in order:
      if name(basename,"anim") in self.props:
        #print "Animating",basename
        newnode = xml.nodes[name(basename,"anim")]
        self.setattrib(newnode,t)
    #xml.commit("org.ekips.filter.test","Interpolate")
    #Still not sure why this is needed
    self.xml.refreshclip()

    xml.commitgroup("org.ekips.filter.test", "org.ekips.filter.test", "Interpolate")
