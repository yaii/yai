class Point():
  def __init__(self,x,y=None):
    if type(x) in [int,float]:
      self.x,self.y=x,y
    else:
      self.x,self.y=x

  def __add__(self,other):
    return Point(self.x+other.x,self.y+other.y)

  def __sub__(self,other):
    return Point(self.x-other.x,self.y-other.y)

  def __div__(self,val):
    return Point(self.x/val, self.y/val)

  def __mul__(self,val):
    return Point(self.x*val, self.y*val)

  def __rmul__(self,val):
    return Point(self.x*val, self.y*val)

  def __getitem__(self, key):
    if( key == 0):
      return self.x
    elif( key == 1):
      return self.y
    else:
      raise Exception("Invalid key to Point")

  def __str__(self):
    return "P("+str(self.x)+", "+str(self.y)+")"

  def __repr__(self):
    return "P("+str(self.x)+", "+str(self.y)+")"

  def __len__(self):
    return 2

  def __abs__(self):
    return abs(self.x+1j*self.y)

  def __eq__(self,other):
    return (self.x == other.x and self.y == other.y)

  def __lt__(self,other):
    return (self.x < other.x and self.y < other.y)

  def __le__(self,other):
    return (self.x <= other.x and self.y <= other.y)

  def __gt__(self,other):
    return (self.x > other.x and self.y > other.y)

  def __ge__(self,other):
    return (self.x >= other.x and self.y >= other.y)

  def __ne__(self,other):
    return not self.__eq__(other)

  def dot(self,other):
    return Point(self.x*other.x,self.y*other.y)

  def inv(self):
    return Point(1.0/self.x,1.0/self.y)

  def rot(self):
    return Point(-self.y,self.x)

  def tuple(self):
    return (self.x,self.y)
  def transform(self,matrix):
    if not matrix:
      return self
    return Point(self.x*matrix[0] + self.y*matrix[2] + matrix[4],
                 self.x*matrix[1] + self.y*matrix[3] + matrix[5])
