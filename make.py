#!/usr/bin/env python
import user
import build.buildGraph
import build.framework
import project

import os

class PetscMake(build.framework.Framework):
  def __init__(self, clArgs = None, argDB = None):
    build.framework.Framework.__init__(self, project.Project('bs', 'bk://sidl.bkbits.net/BuildSystem', self.getRoot()), clArgs, argDB)
    return

  def t_configure(self):
    self.configureHeader = os.path.join(self.project.getRoot(), self.sidlTemplate.usingSIDL.getClientRootDir('Python', 'sidl'), 'cygwinpath_Module.h')
    return build.framework.Framework.t_configure(self)

  def setupSIDL(self):
    import build.fileset
    self.filesets['sidl'] = build.fileset.FileSet()
    return

  def setupSource(self):
    import build.fileset
    url                     = self.project.getUrl()
    pythonRoot              = self.sidlTemplate.usingSIDL.getClientRootDir('Python')
    self.filesets['python'] = build.fileset.RootedFileSet(url, [os.path.join(pythonRoot, 'cygwinpath_Module.c')], tag = 'python client')
    self.filesets['sidl'].children.append(self.filesets['python'])
    return

  def setupProject(self):
    self.setupSIDL()
    return

  def setupBuild(self):
    self.setupSource()
    self.sidlTemplate.addClient('Python')
    return

if __name__ ==  '__main__':
  import sys
  pm = PetscMake(sys.argv[1:])
  pm.main()
