elem = xml.doc.createElement("yai:script")
elem["lang"] = "python"
elem["id"] = "startscript"
elem["code"] = "from xml import *;xml = wrap.frametable"
xml.root.addChild(elem, xml.root.firstChild())
