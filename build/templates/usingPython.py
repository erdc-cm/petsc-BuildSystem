import base
import build.buildGraph
import build.processor
import build.transform
import project

import os

class UsingPython (base.Base):
  def __init__(self, sourceDB, project, usingSIDL, usingC = None):
    base.Base.__init__(self)
    self.sourceDB  = sourceDB
    self.project   = project
    self.usingSIDL = usingSIDL
    self.usingC    = usingC
    if self.usingC is None:
      import build.templates.usingC
      self.usingC = build.templates.usingC.UsingC(self.sourceDB, self.project, self.usingSIDL)
    self.language = 'Python'
    self.setupIncludeDirectories()
    self.setupExtraLibraries()
    return

  def setupArgDB(self, argDB, clArgs):
    import nargs

    argDB.setType('PYTHON_INCLUDE', nargs.ArgDir(None, None, 'The directory containing Python.h', 1))
    argDB.setType('PYTHON_LIB',     nargs.ArgLibrary(None, None, 'The library containing PyInitialize()', 1))
    return base.Base.setupArgDB(self, argDB, clArgs)

  def setupIncludeDirectories(self):
    try:
      if not 'PYTHON_INCLUDE' in self.argDB:
        import distutils.sysconfig
        self.argDB['PYTHON_INCLUDE'] = distutils.sysconfig.get_python_inc()
    except: pass
    self.includeDirs = self.argDB['PYTHON_INCLUDE']
    if not isinstance(self.includeDirs, list):
      self.includeDirs = [self.includeDirs]
    return self.includeDirs

  def setupExtraLibraries(self):
    import distutils.sysconfig
    if not 'PYTHON_LIB' in self.argDB:
      SO = distutils.sysconfig.get_config_var('SO')
      try:
        # Look for the shared library
        lib = os.path.join(distutils.sysconfig.get_config_var('LIBPL'), distutils.sysconfig.get_config_var('LDLIBRARY'))
        # if .so was not built then need to strip .a off of end
        if lib[-2:] == '.a': lib = lib[0:-2]
        # may be stuff after .so like .0, so cannot use splitext()
        lib = lib.split(SO)[0]+SO
        self.argDB['PYTHON_LIB'] = lib
      except TypeError:
        try:
          # Try the archive instead
          lib = lib.split(SO)[0]+'.a'
          self.argDB['PYTHON_LIB'] = lib
        except: pass
      except: pass

    self.extraLibraries = [self.argDB['PYTHON_LIB']]
    if not distutils.sysconfig.get_config_var('LIBS') is None:
      for lib in distutils.sysconfig.get_config_var('LIBS').split():
        # Change -l<lib> to lib<lib>.so
        self.extraLibraries.append('lib'+lib[2:]+'.so')
    return self.extraLibraries

  def getServerLibrary(self, package):
    '''Server libraries follow the naming scheme: lib<project>-<lang>-<package>-server.a'''
    return project.ProjectPath(os.path.join('lib', 'lib'+self.project.getName()+'-'+self.language.lower()+'-'+package+'-server.a'), self.project.getUrl())

  def getGenericCompileTarget(self, action):
    '''Python code does not need compilation, so only a C compiler is necessary.'''
    import build.compile.C
    outputTag = self.language.lower()+' '+action+' '+self.usingC.language.lower()
    tagger    = build.fileState.GenericTag(self.sourceDB, outputTag, inputTag = self.language.lower()+' '+action, ext = 'c', deferredExt = 'h')
    compiler  = build.compile.C.Compiler(self.sourceDB, self.usingC, inputTag = outputTag)
    compiler.includeDirs.extend(self.includeDirs)
    target    = build.buildGraph.BuildGraph()
    target.addVertex(tagger)
    target.addEdges(tagger, outputs = [compiler])
    return (target, compiler)

  def getServerCompileTarget(self, package):
    '''Python code does not need compilation, so only a C compiler is necessary for the skeleton.'''
    (target, compiler) = self.getGenericCompileTarget('server '+package)
    archiveTag   = self.language.lower()+' server library'
    sharedTag    = self.language.lower()+' server shared library'
    library      = self.getServerLibrary(package)
    linker       = build.buildGraph.BuildGraph()
    archiver     = build.processor.Archiver(self.sourceDB, 'ar', compiler.output.tag, archiveTag, isSetwise = 1, library = library)
    sharedLinker = build.processor.SharedLinker(self.sourceDB, compiler.processor, compiler.output.tag, sharedTag, isSetwise = 1, library = library)
    sharedLinker.extraLibraries.extend(self.extraLibraries)
    linker.addVertex(archiver)
    linker.addEdges(sharedLinker, [archiver])
    linker.addEdges(build.transform.Remover(compiler.output.tag), [sharedLinker])
    target.appendGraph(linker)
    return target

  def getClientCompileTarget(self):
    '''Python code does not need compilation, so only a C compiler is necessary for the cartilage.'''
    (target, compiler) = self.getGenericCompileTarget('client')
    archiveTag = self.language.lower()+' client library'
    sharedTag  = self.language.lower()+' client shared library'
    linker     = build.buildGraph.BuildGraph()
    archiver     = build.processor.Archiver(self.sourceDB, 'ar', compiler.output.tag, archiveTag)
    sharedLinker = build.processor.SharedLinker(self.sourceDB, compiler.processor, compiler.output.tag, sharedTag)
    sharedLinker.extraLibraries.extend(self.extraLibraries)
    linker.addVertex(archiver)
    linker.addEdges(sharedLinker, [archiver])
    linker.addEdges(build.transform.Remover(compiler.output.tag), [sharedLinker])
    target.appendGraph(linker)
    return target

  def installClient(self):
    '''Add Python paths for clients to the project'''
    return self.project.appendPythonPath(os.path.join(self.project.getRoot(), self.usingSIDL.getClientRootDir(self.language)))

  def installServer(self, package):
    '''Add Python paths for servers to the project'''
    return self.project.appendPythonPath(os.path.join(self.project.getRoot(), self.usingSIDL.getServerRootDir(self.language, package)))