if True:
    entries = list(entries)
    entries.sort()
    objs = {}
    objsorder = []
    print entries
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
    #return objs, order
