class PiecewiseLinear(object):
  def __init__(self, points, zero=0):
    self.points = list(points)
    self.zero = zero

  def getpoint(self,t):
    if t==(len(self.points)-1):
      return self.points[-1]
    i = int(t)
    t = t - i
    val = (1-t)*self.points[i]+t*self.points[i+1]
    return val

  def getpoints(self):
    numsteps = 100
    tlist = [(len(self.points)-1)*t/float(numsteps) for t in xrange(numsteps+1)]
    return [self.getpoint(t) for t in tlist]
