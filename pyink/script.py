order = [c["id"].replace("-properties","") for c in wrap.xml.nodes["layer-properties"].children()]
wrap.frametable.order = order
wrap.animadj.upper = 10

#Frame bound version of interpolate
ent = wrap.frametable.cells.entries
ent2= [(i,j) for i,j in ent if j<3]
objs, order = self.xml.allrows(order, ent2)
self.animator.addanims(['head'], objs)
self.animator.timetransf = self.xml.gettimetransforms(order, ent2)
self.xml.commit("EditPaste", "Add anim")

def customterp(self, layername = 'layer-13'):
  self.frametable.refresh()
  #animorder = [c['id'].rsplit("-")[0] for c in self.xml.nodes[layername].children()]
  #animorder = [s for s in animorder if s.startswith("skcrab") or not s.startswith("sk")]
  #animorder = [s for s in self.frametable.order if s.startswith("skcrab") or not s.startswith("sk")]
  animorder = [s for s in self.frametable.order if not s.startswith("sk")]
  order = self.frametable.order
  entries = self.frametable.cells.entries
  objs, order = self.xml.allrows(order, entries)
  self.animator.addanims(animorder, objs)
  self.animator.timetransf = self.xml.gettimetransforms(order, entries)
  #self.animator.timetransf = self.xml.gettimetransforms(animorder, entries)
  self.xml.commit("EditPaste", "Add anim")

def export(self):

from xreload import xreload
import xml
xreload(xml)

#Update transform based objects
sourcenode = self.xml.nodes["head-0"]
targets = [self.xml.nodes.get("head-%s"%i) for i in xrange(1,13)]
for target in targets:
  if target:
    transform = target["transform"]
    newnode = self.xml.overwrite(target, sourcenode)
    newnode["transform"] = transform
self.update()
self.xml.commit("EditPaste", "Paste by transform")

tt = lambda t: t + (t>9)*min(1,(t-9)) + (t>12)*min(1,(t-12))


#ls -tr rsvg*.png > list.txt
#mencoder mf://@list.txt -mf fps=10:type=png -ovc lavc -lavcopts vcodec=mpeg4:mbd=2:trell -oac copy -o output.avi

wrap.animator.export(14,0,tt)
wrap.animator.export(14,12,tt)

def g(t):
  return min(2,max(0, (t-14.5)*2))
wrap.animator.timetransf['impact-anim'] = g
