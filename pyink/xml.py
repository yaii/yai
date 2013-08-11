import re
from svg.svghelp import unserattrib, serattrib

def pair(nodename):
  return nodename.rsplit("-",1)

def name(rowname, framenum=None):
  #First argument is a list
  if framenum is None:
    rowname, framenum = rowname
  return rowname+"-"+str(framenum)

class XML:
  """ Extract useful fields from various places. 
      Interfaces with the XML tree directly.
      Including layers selection and manipulation."""
  def __init__(self, desktop):
    self.desktop = desktop
    self.viewmode = False
    self.sellayer = None
    self.update()

  def update(self):
    #Document has been destroyed...
    if not self.desktop:
      print "Desktop lost by xml."
      return
    self.doc = self.desktop.doc().rdoc
    self.selection = self.desktop.selection.list()
    self.selector = self.desktop.selection
    self.root = self.desktop.doc().root().repr
    self.nodes = self.updatenodes()
    self.startscript = self.nodes.get("startscript")

  def saveopt(self, optname, optvalue):
    self.nodes["startscript"][optname] = str(optvalue)

  def getopt(self, optname):
    if optname not in self.nodes["startscript"].keys():
      return None
    return self.nodes["startscript"][optname]

  def updateroot(self, order):
    oldelem = self.nodes.get("startscript")
    if not oldelem:
      elem = self.doc.createElement("yai:script")
      #Bad heuristic to tell if this node already exists.
      self.root["xmlns:yai"] = "http://yai.heroku.com"
    else:
      elem = oldelem
    elem["code"] = "from xml import *;self = wrap.frametable"
    elem["order"] = str(order)
    defaultvals = {"lang":"python",
                   "id":"startscript",
                   "layerview":"False",     #Should read button state from yai instead
                   "animlayer":"False",     #Should read button state from yai instead
                   "opacity-dist":"2.0",
                   "export-infile":"/tmpfs/drawing.svg",
                   "export-outfile":"/tmpfs/anim/frames",
                   "export-zoom":"0.2"}
    for key,val in defaultvals.items():
      if key not in elem.keys():
        elem[key] = val
    if not oldelem:
      self.root.addChild(elem, self.root.firstChild())

  def layers(self):
    layers = []
    for child in self.root.childlist():
      if child.get("inkscape:groupmode") == "layer":
        layers.append(child)
    return layers

  def newlayer(self, id, label):
    print "Creating layer %s" % id
    targetlayer = self.doc.createElement('svg:g')
    targetlayer['id'] = id
    targetlayer['inkscape:label'] = label
    targetlayer["inkscape:groupmode"] = "layer"
    return targetlayer

  def updatenodes(self, node=None):
    if not node:
      node = self.root
    seen = [node]
    nodes = {}
    nodeindex = 0
    while nodeindex < len(seen):
      node = seen[nodeindex]
      nodeid = node.get('id')
      if nodeid is not None:
        nodes[nodeid] = node
        seen.extend(node.childList())
      nodeindex += 1
    return nodes

  def makecopy(self, sourcenode, targetname, createlayer = True):
    if not sourcenode:
      print "No source node!"
      return None

    print "Targetname", targetname
    newnode = sourcenode.duplicate(sourcenode.document())
    newnode["id"] = name(targetname)
    layername = ("layer", targetname[1])
    targetlayer = self.nodes.get(name(layername))
    if not targetlayer:
      if not createlayer:
        return None
      targetlayer = self.newlayer(name(layername), 'Layer '+str(targetname[1]))
      print "Created target layer: %s" % targetlayer["id"]
      self.root.appendChild(targetlayer)
      #Bad hack, should really just be tracking additions...
      self.nodes.update(self.updatenodes(targetlayer))
    oldnode = self.nodes.get(newnode["id"])
    if oldnode:
      oldnode.parent().removeChild(oldnode)
    #Should preserve order
    targetlayer.appendChild(newnode)    
    return newnode

  def unlockalllayers(self):
    #May wish to skip animation layers though...
    for layer in self.layers():
      layer['style'] = ''
      del layer['sodipodi:insensitive']

  def unlockalllayers(self):
    self.update()
    for col in xrange(self.numcols):
      layer = self.nodes.get(name("layer",col))
      if layer:
        layer['style'] = ''
        del layer['sodipodi:insensitive']
    #self.commitgroup("UnhideLayer", "Anim layers visibility", "Unlock all layers")
    self.commitgroup("Anim layers visibility", "org.ekips.filter.test", "Unlock all layers")


  def singleoutlayer(self,layername = None):
    self.update()
    if not layername:
      sellayer = self.sellayer
    else:
      sellayer = self.nodes.get(layername)
    if sellayer is None:
      print "Could not find layer %s" % layername
      return
    sellayer['style'] = ''
    if sellayer.get('sodipodi:insensitive'):
      del sellayer['sodipodi:insensitive']
    selcol = int(pair(sellayer["id"])[1])
    for col in xrange(self.numcols):
      layer = self.nodes.get(name("layer",col))
      if layer and layer != sellayer:
        opacity = max(0, 1 - abs(col-selcol) / float(self.nodes["startscript"].get("opacity-dist",1.0)))
        #print "opacity",opacity
        layer['style'] = 'display:inline;opacity:%s' % opacity
        layer['sodipodi:insensitive'] = 'true'
    #self.commitgroup("HideLayer", "Anim layers visibility", "Single-out layer")
    self.commitgroup("Anim layers visibility", "org.ekips.filter.test", "Single-out layer")

  def togglevisible(self, prefix, visible = True):
    print "Setting visibility for", prefix, "to", visible
    nodes = [node for key,node in self.nodes.items() if pair(key)[0] == prefix]
    if not visible:
      for node in nodes:
        #Should preserve everything else except opacity and display...
        node["style"] = "display:none"
    else:
      for node in nodes:
        #Should preserve everything else except opacity and display...
        node["style"] = ""

  def hide(self, node, visible = True):
    if not visible:
      node["style"] = "display:none"
    else:
      node["style"] = ""

  def togglelock(self, prefix, lock = True):
    print "Setting lock for", prefix, "to", lock
    nodes = [node for key,node in self.nodes.items() if pair(key)[0] == prefix]
    if lock:
      for node in nodes:
        #Should preserve everything else except opacity and display...
        node["sodipodi:insensitive"] = "true"
    else:
      for node in nodes:
        #Should preserve everything else except opacity and display...
        del node["sodipodi:insensitive"]

  def rename(self, prefix, newprefix):
    print "Renaming ", prefix, "to", newprefix
    for key,node in self.nodes.items():
      basename, layer = pair(key)
      if basename == prefix:
        node["id"] = name(newprefix, layer)
        
  def selectlayer(self,selrow,selcol,createlayer=True):
    self.sellayer = self.nodes.get(name("layer",selcol))
    if self.sellayer is None:
      print "Could not find layer %s" % selcol
      if createlayer:
        self.sellayer = self.newlayer(name("layer",selcol), "Layer %s"%selcol)
        self.root.appendChild(self.sellayer)
      else:
        return
    self.desktop.setCurrentLayer(self.sellayer.spitem)
    if self.nodes["startscript"]["layerview"]:
      self.singleoutlayer()

  def allrows(self, order, entries):
    entries = list(entries)
    entries.sort()
    objs = {}
    objsorder = []
    for row,col in entries:
      basename = order[row]
      node = self.nodes.get(name(basename,col))
      if node:
        if basename not in objs:
          objs[basename] = []
          objsorder.append(basename)
        objs[basename].append(node)
    allrows = sorted(list(set(row for row,col in entries)))
    mins = [min([col for row,col in entries if row==currow])
            for currow in allrows]
    maxs = [max([col for row,col in entries if row==currow])
            for currow in allrows]
    return objs, order

  def gettimetransforms(self, order, entries):
    allrows = sorted(list(set(row for row,col in entries)))
    entriesbyrow = dict([(currow,[col for row,col in entries if row==currow]) for currow in allrows])

    from bisect import bisect_left
    def tt(times):
      def f(t):
        index = bisect_left(times,t)
        if index <= 0:
          return 0
        elif index >= len(times):
          return len(times)-1
        else:
          t = (t - times[index-1])/float(times[index] - times[index-1])
          return (index-1) + t
      return f

    timetransf = {}
    for row in allrows:
      entriesbyrow[row].sort()
      basename = order[row]
      timetransf[name(basename,"anim")] = tt(entriesbyrow[row])
    #maxt = max(entry[1] for entry in entries)
    return timetransf

  def commit(self, verb, message):
    self.desktop.doc().done(verb, message)

  def commitgroup(self, groupkey, verb, message):
    self.desktop.doc().maybe_undo(groupkey, verb, message)

  # Maybe we could use the mysterious mergeFrom function? Although in those cases labels have to be exactly matching...
  def overwrite(self, oldnode, node):
    #oldnode = self.nodes[nodename]
    if node.parent():
      node = node.duplicate(node.document())
    #print "overwriting",oldnode["id"],"with",node["id"]
    node["id"] = oldnode["id"]
    oldnode["id"] = oldnode["id"]+"-old"
    parent = oldnode.parent()
    parent.addChild(node,oldnode)
    parent.removeChild(oldnode)
    self.nodes[node["id"]] = node
    #self.update()
    return node

  def refreshclip(self):
    def refreshone(node):
      if "clip-path" in node.keys():
        clipname = node["clip-path"]
        del node["clip-path"]
        node["clip-path"] = clipname
        #clipname = node.parent()["clip-path"]
        #del node.parent()["clip-path"]
        #node.parent()["clip-path"] = clipname
    self.applytoall(refreshone)


  #This doesn't work because it will still add ids for nodes whose key values cannot be found (where as we just want to use the existing ordering in the tree).
  """
  def overwrite(self, oldnode, node):
    oldnode.mergeFrom(node, "nonexistentkey")
  """

  def applytoall(self, func, subtreeroot = None):
    allnodes = self.updatenodes(subtreeroot)
    for node in allnodes.values():
      func(node)

  #This version allows newly created nodes to be traversed too.
  def applytoall(self, func, subtreeroot = None):
    node = subtreeroot
    if not node:
      node = self.root
    seen = [node]
    nodes = {}
    nodeindex = 0
    while nodeindex < len(seen):
      node = seen[nodeindex]
      nodeid = node.get('id')
      if nodeid is not None:
        func(node)
        seen.extend(node.childList())
      nodeindex += 1

  #It seems like we can almost do this without using defs. But inkscape gets confused.
  def unbddfynode(self, node):
    if "clip-path" in node.keys():
      print node["clip-path"]
      clippathname = re.findall(r'url\(#(.*)\)',node["clip-path"])[0]
      clippath = self.nodes[clippathname]
      duplicate = clippath.duplicate(clippath.document())
      duplicate["id"] = node["id"] + "-clip"
      duplicate["defnode"] = clippathname
      #Remove old duplicate
      olddup = self.nodes.get(duplicate["id"])
      if olddup:
        if olddup.parent():
          olddup.parent().removeChild(olddup)
      node.appendChild(duplicate)
    elif node.name() == "svg:clipPath":
      print "clipPath", node["id"]
      dupchild = node.children()[0]
      if dupchild and dupchild.name() == "svg:use":
        print "dup-child",dupchild["id"]
        sourcename = dupchild["xlink:href"][1:]
        source = self.nodes[sourcename]
        node.appendChild(source.duplicate(source.document()))
        node.removeChild(dupchild)
    elif False and node.name() == "svg:use":
      sourcename = node["xlink:href"][1:]
      source = self.nodes[sourcename]
      node.parent().appendChild(source.duplicate(source.document()))
      node.parent().removeChild(node)

    elif False and node.get("style"):
      print node["style"]
      style = unserattrib(node["style"])
      for attrib in ["fill","stroke"]:
        val = style.get(attrib,"")
        urls = re.findall(r'url\(#(.*)\)',val)
        if urls:
          gradname = urls[0] #re.findall(r'url\(#(.*)\)', style["stroke"])[0]
          gradient = self.nodes[gradname]
          duplicate = gradient.duplicate(gradient.document())
          duplicate["id"] = "%s-%sgradient" % (node["id"], attrib)
          duplicate["defnode"] = gradname
          olddup = self.nodes.get(duplicate["id"])
          if olddup:
            olddup.parent().removeChild(olddup)
          node.appendChild(duplicate)
    #Maybe not absolutely necessary for the moment...
    """
    elif node.get("xlink:href"):
      gradname = node.get("xlink:href")[1:]
      gradient = self.nodes[gradname]
      duplicate = gradient.duplicate(gradient.document())
      duplicate["id"] = "%s-xlink" % node["id"]
      duplicate["defnode"] = gradname
      olddup = self.nodes.get(duplicate["id"])
      if olddup:
        olddup.parent().removeChild(olddup)
      node.appendChild(duplicate)
    """
  def bddtotree(self):
    """ Adds child clipPath and gradient to nodes that don't have them."""
    self.applytoall(self.unbddfynode)
    self.update()

  def updatedef(self,node):
    if node.get("defnode"):
      dup = node.duplicate(node.document())
      del dup["defnode"]
      self.overwrite(self.nodes[node["defnode"]], dup)

  def treetodefs(self):
    """ Use artificially created tree nodes to update the defs. """
    self.applytoall(self.updatedef)
    self.update()

