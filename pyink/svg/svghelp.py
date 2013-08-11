def unserattrib(attrib):
  return dict(subattrib.split(":") for subattrib in attrib.split(";") if subattrib)

def serattrib(d):
  return ";".join(":".join(item) for item in d.items())
