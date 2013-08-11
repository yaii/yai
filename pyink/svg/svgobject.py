import re
from pygame.color import Color
from point import Point as P
import pygame
from copy import copy


def getbezpoint(p,c,t):
  return ((1-t)*(1-t)*(1-t)*p[0] + 3*t*(1-t)*(1-t)*c[0]
          + 3*t*t*(1-t)*c[1] + t*t*t*p[1])

def getbezpoints(points):
  numsteps = 10
  tlist = [t/float(numsteps) for t in xrange(numsteps+1)]
  allpoints = [getbezpoint((points[0],points[3]),(points[1],points[2]),t)
               for t in tlist]
  return allpoints

def getpaths(commands):
  """ Commands to list of list of points (paths, not SVG paths). """
  curpath = []
  allpaths = []
  for element in commands:
    command = element[0]
    if command == "M":
      if curpath:
        allpaths.append(ColoredPath(curpath))
      curpath = []
      curpath.append(element[1])
    elif command == "L":
      curpath.append(element[1])
    elif command == "C":
      curpath.extend(getbezpoints(element[1:]))
    elif command == "Q":
      #dummy for now. Need to actually code for later.
      curpath.append(element[1])
    elif command == "z":
      curpath.append(curpath[0])
    else:
      print command
      #print element
      causeerror
  allpaths.append(ColoredPath(curpath))
  return allpaths

def fastgetcommands(svgpath):
  commands = []
  for element in svgpath:
    command = element[0]
    #print element
    points = [P(map(float,e.split(","))) if "," in e else float(e) for e in element[1:]]
    #if len(points)>1:
    if command in ["C","Q"]:
      commands.append([command,commands[-1][-1]]+points)
    else:
      commands.append([command]+points)
  return commands

def getcommands(svgpath):
  """ SVG path string to commands. """
  commands = []
  for element in svgpath:
    command = element[0]
    if command == "M":
      commands.append(("M",eval("P(%s)"%element[1])))
    elif command == "L":
      commands.append(("L",eval("P(%s)"%element[1])))
    elif command == "C":
      commands.append(["C",commands[-1][-1]]+[eval("P(%s)"%p) for p in element[1:]])
    elif command == "Q":
      commands.append(["Q",commands[-1][-1]]+[eval("P(%s)"%p) for p in element[1:]])
    elif command == "z":
      commands.append("z")
    else:
      #print element
      causeerror
  return commands

def gettransfcommands(transform,commands):
  if not transform:
    return commands[:]
  transfcommands = []
  for command in commands:
    transfcommands.append([command[0]]+map(lambda p:p.transform(transform),command[1:]))
  return transfcommands

def gettransform(transfstring):
  if not transfstring:
    return None
  if type(transfstring) == list:
    return transfstring
  if transfstring.startswith("matrix"):
    matrix = transfstring.split("(",1)[1].rsplit(")",1)[0]
  elif transfstring.startswith("translate"):
    matrix = "1,0,0,1,"+transfstring.split("(",1)[1].rsplit(")",1)[0]
  else:
    #print transfstring
    #causeerror
    matrix = transfstring
  return map(float,matrix.split(","))

def composetransform(t,u):
  if t is None:
    return copy(u)
  if u is None:
    return copy(t)
  #if type(t) == str:
  #  t = gettransform(t)
  #if type(u) == str:
  #  u = gettransform(u)
  return [t[0]*u[0]+t[2]*u[1],t[1]*u[0]+t[3]*u[1],
          t[0]*u[2]+t[2]*u[3],t[1]*u[2]+t[3]*u[3],
          t[0]*u[4]+t[2]*u[5]+t[4],t[1]*u[4]+t[3]*u[5]+t[5]]

def commandsplit(commands):
  """ Split commands by path segments. """
  curpath = []
  allpaths = []
  for element in commands:
    command = element[0]
    if command == "M":
      if curpath:
        allpaths.append(curpath)
      curpath = []
    curpath.append(element)
  allpaths.append(curpath)
  return allpaths

def commandstodict(commands,col=None,linecol=None):
  #alpha is set in "stroke-opacity"
  def colstr(col):
    return "".join(map(lambda coord:"%0.2x" % coord,col[:3]))
  def pstr(p):
    return str(p[0])+","+str(p[1])
  def elemstr(element):
    if element[0] in ["C","Q"]:
      return " ".join([element[0]]+map(pstr,element[2:]))
    else:
      return " ".join([element[0]]+map(pstr,element[1:]))
  d = {"id":"renderedpath","style":[]}
  d["d"] = " ".join(map(elemstr,commands))
  if col:
    d["style"].append("color:#000000;fill:#"+colstr(col))
  else:
    d["style"].append("fill:none")
  if linecol:
    d["style"].append("stroke:#"+colstr(linecol))
  return d

def dicttosvg(d):
  def keyvalstr(key,val):
    #Bad for duck typing but both string and lists are iterable.
    if type(val) in [list, tuple]:
      return '%s="%s"' % (key, ";".join(val))
    else:
      return '%s="%s"' % (key, val)
  pathelem = "<path\n %s />" % "\n".join(keyvalstr(key,val) for key,val in d.items())
  return pathelem
  #return "%s\n%s\n</svg>" % (header,pathelem)

header = """<?xml version="1.0" encoding="UTF-8" ?>
<svg 
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   version="1.1"
   width="700"
   height="700">
"""
anotherheader = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">

<svg width="200px" height="800px" version="1.1"
xmlns="http://www.w3.org/2000/svg">"""
footer = "</svg>"

def exportsvg(objs,filename="/tmpfs/output.svg",t=0,extrad=None):

  #Bad for duck typing.
  if type(objs) not in [tuple,list]:
    objs = [objs]
  f = open(filename,"w")
  f.write(header)
  for obj in objs:
    try:
      commands = obj.getcommands(obj.t)
      commands = gettransfcommands(obj.camera,commands)
    except:
      commands = obj.commands
    d = commandstodict(commands, obj.col,obj.linecol)
    if extrad:
      d.update(extrad)
    svgstr = dicttosvg(d)
    f.write(svgstr)
    f.write("\n")
  f.write(footer)
  f.close()
  #return "%s\n%s\n</svg>" % (header,pathelem)

def exportsvgproperties(objs,soup,filename="/tmpfs/output.svg",t=0):

  f = open(filename,"w")
  f.write(header)
  for part,obj in objs.items():
    try:
      commands = obj.getcommands(obj.t)
      commands = gettransfcommands(obj.camera,commands)
    except:
      commands = obj.commands
    d = commandstodict(commands, obj.col,obj.linecol)
    tag = soup.find(attrs={"id":part+"properties"})
    if tag:
      extrad = copy(tag.attrMap)
      for param in ["d","id"]:
        if param in extrad:
          del extrad[param]
      d.update(extrad)
    d["id"] = part
    svgstr = dicttosvg(d)
    f.write(svgstr)
    f.write("\n")
  f.write(footer)
  f.close()

def exportsvgproperties(objs,order,soup,filename="/tmpfs/output.svg",t=0):
  f = open(filename,"w")
  f.write(header)
  #for part,obj in objs.items():
  for part in order:
    properties = soup.find(attrs={"id":part+"properties"})
    svgstr = objs[part].export(part,properties)#dicttosvg(d)
    f.write(svgstr)
    f.write("\n")
  f.write(footer)
  f.close()

class ColoredPath(list):
  def __init__(self,*args):
    list.__init__(self,*args)
    self.col = None
    self.linecol = Color("white")

def threshold(mask):
  rect = mask.get_bounding_rect()
  #print rect.top,rect.bottom,rect.left,rect.right
  pxarray = pygame.PixelArray(mask)
  #for i,row in enumerate(pxarray):
  #  for j,cell in enumerate(row):
  for j in xrange(rect.top,rect.bottom):
    for i in xrange(rect.left,rect.right):
      if pxarray[i][j]:
        pxarray[i][j] = pygame.Color("white")
  del pxarray
  #del row
  #del cell

#The cols are not so useful except for SVGCurveanim...  so some of cols related code is not needed.
class SVGBasic(object):
  def __init__(self, transform=None, cols=None, scale=1, width=1, clip=None):
    self.scale = scale
    self.width = width
    self.cols = cols
    self.commands = []
    if transform:
      self.transform = gettransform(transform)#map(float,transform.split(","))
    else:
      self.transform = None
    self.clip = None
    #print self.paths
    self.ducks = {}

  def renderpartial(self,surf,path,col,linecol):
    if col:
      if len(path)==2:
        pygame.draw.polygon(surf,col,path+list(reversed(path)))
      else:
        pygame.draw.polygon(surf,col,path)
    if linecol:
      pygame.draw.lines(surf,linecol,False,path,self.width)

  def render(self,surf):
    if self.clip:
      mask = pygame.Surface(surf.get_size(),pygame.SRCALPHA)
      self.clip.render(mask)
      threshold(mask)
      #pygame.draw.polygon(mask,Color("#1c2a66"),[(0,0),(100,100),(100,0)])

      #surf.blit(mask, (0,0))
      #return
      tmpsurf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
      for path in self.paths:
        newpath = map(lambda x:x*self.scale,path)
        self.renderpartial(tmpsurf,newpath,path.col,path.linecol)
      tmpsurf.blit(mask,(0,0), special_flags=pygame.BLEND_RGBA_MULT)
      surf.blit(tmpsurf,(0,0))
      return
    for path in self.paths:
      newpath = map(lambda x:x*self.scale,path)
      self.renderpartial(surf,newpath,path.col,path.linecol)

  def addtransform(self,transform, initial=False):
    """ Compose all command points with a transform. 
    Also composes stored transform (unless initial is True).
    """
    if not initial:
      self.transform = composetransform(transform,self.transform)
    if transform:
      self.commands = gettransfcommands(transform,self.commands)
    self.paths = getpaths(self.commands)

  def addcols(self):
    """ Add stored colours to stored path. """
    if self.cols is None:
      self.cols = [(None,None) for path in self.paths]
      return
    for i,path in enumerate(self.paths):
      col, linecol = self.cols[i]
      if col or linecol:
        path.col = col
        path.linecol = linecol

  def export(self, pathnum = 0, id = "path", tag = None):
    commands = self.commands
    col, linecol = self.cols[pathnum]
    d = commandstodict(commands, col, linecol)
    if tag:
      extrad = copy(tag.attrMap)
      for param in ["d","id"]:
        if param in extrad:
          del extrad[param]
      d.update(extrad)
    d["id"] = id
    return dicttosvg(d)

  def exportall(self, id = "svgobj"):
    #header
    svgstr = """<g
      id="%s">
    """ % id
    for i,path in enumerate(self.paths):
      svgstr += self.export(i,"%s-path-%s" % (id,i))
    #footer
    svgstr += "\n</g>"
    return svgstr

class SVGPath(SVGBasic):
  def __init__(self,pathstring,**kwargs):
    SVGBasic.__init__(self,**kwargs)
    self.svgpath = map(lambda x:x.strip().split(),re.findall("[LCQMlcqmz][^LCQMlcqmz]*",pathstring))
    self.commands = getcommands(self.svgpath)
    self.addtransform(self.transform, initial=True)
    self.addcols()
    #print self.commands

class SVGGroup(SVGBasic):
  def __init__(self,sources,**kwargs):
    SVGBasic.__init__(self,**kwargs)
    self.sources = sources
    self.commands = []
    #[self.paths.extend(source.paths for source in sources)]
    self.cols = []
    for source in sources:
      self.commands.extend(source.commands)
      self.cols.extend(source.cols)
    self.addtransform(self.transform, initial=True)
    self.addcols()

class SVGClone(SVGBasic):
  def __init__(self,source,**kwargs):
    SVGBasic.__init__(self,**kwargs)
    self.source = source
    self.addtransform(self.transform,initial=True)

  def addtransform(self,transform,initial=False):
    if not initial:
      self.transform = composetransform(transform,self.transform)
    if transform:
      self.commands = gettransfcommands(transform,self.source.commands)
    self.paths = getpaths(self.commands)

class SVGGroupClone(SVGBasic):
  """ Copies elements from a different group than its own children. """
  def __init__(self,sourcegroup,**kwargs):
    SVGBasic.__init__(self,**kwargs)
    self.sources = sourcegroup.sources
    self.commands = []
    self.cols = []
    for source in sources:
      self.commands.extend(source.commands)
      self.cols.extend(source.cols)
    self.addtransform(self.transform, initial=True)
    self.addcols()

class CubicSpline(object):
  """ Catmull-Rom cubic spline """
  
  def __init__(self,points=[150, 300, 300, 200],zero=0):
    #self.points = map(P,points)
    self.points = list(points)
    self.zero = zero
    self.updatediffs()

  def updatediffs(self):
    #self.diffs = [P(0,0)]+[self.points[i+1]-self.points[i-1]
    #              for i,p in list(enumerate(self.points))[1:-1]]+[P(0,0)]
    self.diffs = [self.zero]+[self.points[i+1]-self.points[i-1]
                  for i,p in list(enumerate(self.points))[1:-1]]+[self.zero]

  def getpoint(self,t):
    if t>=len(self.points)-1:
      return self.points[-1]
    i = int(t)
    t = t - i
    val = ((2*t**3-3*t*t+1) * self.points[i]
           + (t**3-2*t*t+t) * self.diffs[i]/2.0
           + (-2*t**3+3*t*t) * self.points[i+1]
           + (t**3-t*t) * self.diffs[i+1])/2.0
    return val

  def getpoint(self,t):
    if t==1:
      return self.points[-1]
    t = t * (len(self.points)-1)
    i = int(t)
    t = t - i
    points = [self.points[0]]+self.points+[self.points[-1]]
    #print t,i,len(points)
    val = (t*((2-t)*t - 1)    * points[i]
        + (t*t*(3*t - 5) + 2) * points[i+1]
        + t*((4 - 3*t)*t + 1) * points[i+2]
        + (t-1)*t*t           * points[i+3]) / 2
    return val

  def getpoints(self):
    numsteps = 100
    #tlist = [(len(self.points)-1)*t/float(numsteps) for t in xrange(numsteps+1)]
    tlist = [t/float(numsteps) for t in xrange(numsteps+1)]
    return [self.getpoint(t) for t in tlist]

  def getpoint(self,t):
    if t==(len(self.points)-1):
      return self.points[-1]
    i = int(t)
    t = t - i
    if i>=(len(self.points)-1):
      return self.points[-1]
    points = [self.points[0]]+self.points+[self.points[-1]]
    #print t,i,len(points)
    val = (t*((2-t)*t - 1)    * points[i]
        + (t*t*(3*t - 5) + 2) * points[i+1]
        + t*((4 - 3*t)*t + 1) * points[i+2]
        + (t-1)*t*t           * points[i+3]) / 2
    return val

  def getpoints(self):
    numsteps = 100
    tlist = [(len(self.points)-1)*t/float(numsteps) for t in xrange(numsteps+1)]
    return [self.getpoint(t) for t in tlist]



class CubicSpline(object):
  """ Catmull-Rom cubic spline """
  
  def __init__(self,points=[150, 300, 300, 200],zero=0):
    #self.points = map(P,points)
    self.points = list(points)
    self.zero = zero
    self.updatediffs()
    self.points = [self.points[0]]+self.points+[self.points[-1]]

  def updatediffs(self):
    #self.diffs = [P(0,0)]+[self.points[i+1]-self.points[i-1]
    #              for i,p in list(enumerate(self.points))[1:-1]]+[P(0,0)]
    self.diffs = [self.zero]+[self.points[i+1]-self.points[i-1]
                  for i,p in list(enumerate(self.points))[1:-1]]+[self.zero]


  def getpoint(self,t):
    if t==(len(self.points)-1):
      return self.points[-1]
    i = int(t)
    t = t - i
    if i+3 >= len(self.points):
      return self.points[-1]
    points = self.points
    #print t,i,len(points)
    val = (t*((2-t)*t - 1)    * points[i]
        + (t*t*(3*t - 5) + 2) * points[i+1]
        + t*((4 - 3*t)*t + 1) * points[i+2]
        + (t-1)*t*t           * points[i+3]) / 2
    return val

  def getpointfast(self,i,t,coeff):
    val = (coeff[0] * points[i]
        + coeff[1] * points[i+1]
        + coeff[2] * points[i+2]
        + coeff[3] * points[i+3])
    return val

  def getpoints(self):
    numsteps = 100
    tlist = [(len(self.points)-1)*t/float(numsteps) for t in xrange(numsteps+1)]
    return [self.getpoint(t) for t in tlist]


class SVGCurveanim(SVGBasic):
  def __init__(self,frames,interpolator=None,**kwargs):
    SVGBasic.__init__(self,**kwargs)
    self.frames = frames
    self.commands = []
    self.camera = None
    for i,command in enumerate(frames[0].commands):
      newcmd = [command[0]]
      #print newcmd,command
      #for j in xrange(1,len(command)):
      #  for frame in frames:
      #    print i,j,frame,[x[0] for x in frame.commands],
      #    print map(type,[[frame.commands[i][j]]])
      #  print
      #print map(type,[[frame.commands[i][j] for frame in frames] for j in xrange(1,len(command))])
      if interpolator:
        Terp = interpolator
      else:
        Terp = CubicSpline
      newcmd += [Terp([frame.commands[i][j] for frame in frames], zero=P(0,0)) for j in xrange(1,len(command))]
      """
      for j,point in command:
        if j > 0:
          newcmd.append(CubicSpline(frame.commands[i][j] for frame in frames))
      """
      self.commands.append(newcmd)
    self._t = 0
    #print getpaths(self.getcommands(self.t))

  def gett(self):
    return self._t

  def sett(self,t):
    self._t = t

  t = property(gett, sett)

  def getcommands(self,t):
    commandt = []
    #print t
    for command in self.commands:
      commandt.append([command[0]]+map(lambda c:c.getpoint(t),command[1:]))
    return commandt

  def render(self,surf):
    commands = self.getcommands(self.t)
    commands = gettransfcommands(self.camera,commands)
    self.paths = getpaths(commands)
    self.addcols()
    SVGBasic.render(self,surf)

  def export(self,part,propertiestag = None):
    commands = self.getcommands(self.t)
    commands = gettransfcommands(self.camera,commands)
    tag = propertiestag
    #tag = soup.find(attrs={"id":part+"properties"})
    extrad = {}
    if tag:
      extrad = copy(tag.attrMap)
      for param in ["d","id","style"]:
        if param in extrad:
          del extrad[param]
    splitcmds = commandsplit(commands)
    svgstr = """<g
     inkscape:label="%s"
     id="%s"
     inkscape:groupmode="layer">
     """ % (part,part)
    for i,cmds in enumerate(splitcmds):
      d = commandstodict(cmds,self.cols[i][0],self.cols[i][1])
      d.update(extrad)
      if "id" in d:
        del d["id"]
      svgstr += dicttosvg(d)+"\n"
      #svgstr = dicttosvg(d)
    svgstr += "</g>\n"
    return svgstr
