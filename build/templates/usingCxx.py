import base
import build.buildGraph
import build.processor
import build.transform
import project

import os

class UsingCxx (base.Base):
  def __init__(self, sourceDB, project, usingSIDL, usingC = None):
    base.Base.__init__(self)
    self.sourceDB  = sourceDB
    self.project   = project
    self.usingSIDL = usingSIDL
    self.usingC    = usingC
    if self.usingC is None:
      import build.templates.usingC
      self.usingC = build.templates.usingC.UsingC(self.sourceDB, self.project, self.usingSIDL)
    self.language  = 'Cxx'
    self.setupIncludeDirectories()
    self.setupExtraLibraries()
    return

  def setupIncludeDirectories(self):
    self.includeDirs = []
    return self.includeDirs

  def setupExtraLibraries(self):
    self.extraLibraries = []
    return self.extraLibraries

  def getServerLibrary(self, package):
    '''Server libraries follow the naming scheme: lib<project>-<lang>-<package>-server.a'''
    return project.ProjectPath(os.path.join('lib', 'lib'+self.project.getName()+'-'+self.language.lower()+'-'+package+'-server.a'), self.project.getUrl())

  def getGenericCompileTarget(self, action):
    '''All purposes are in Cxx, so only a Cxx compiler is necessary.'''
    import build.compile.Cxx
    inputTag  = map(lambda a: self.language.lower()+' '+a, action)
    outputTag = self.language.lower()+' '+action[0]+' '+self.language.lower()
    tagger    = build.fileState.GenericTag(self.sourceDB, outputTag, inputTag = inputTag, ext = 'cc', deferredExt = 'hh')
    compiler  = build.compile.Cxx.Compiler(self.sourceDB, self, inputTag = outputTag)
    compiler.includeDirs.extend(self.includeDirs)
    target    = build.buildGraph.BuildGraph()
    target.addVertex(tagger)
    target.addEdges(tagger, outputs = [compiler])
    return (target, compiler)

  def getIORCompileTarget(self, action):
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
    '''All purposes are in Cxx, so only a Cxx compiler is necessary for the skeleton and implementation.'''
    inputTag     = ['server '+package]
    if len(self.usingSIDL.staticPackages):
      inputTag.append('client')
    (target,    compiler)    = self.getGenericCompileTarget(inputTag)
    (iorTarget, iorCompiler) = self.getIORCompileTarget('server '+package)
    compiler.includeDirs.append(self.usingSIDL.getServerRootDir(self.language, package))
    inputTags    = [compiler.output.tag, iorCompiler.output.tag]
    archiveTag   = self.language.lower()+' server library'
    sharedTag    = self.language.lower()+' server shared library'
    library      = self.getServerLibrary(package)
    linker       = build.buildGraph.BuildGraph()
    archiver     = build.processor.Archiver(self.sourceDB, 'ar', inputTags, archiveTag, isSetwise = 1, library = library)
    consolidator = build.transform.Consolidator(inputTags, inputTags[0])
    sharedLinker = build.processor.SharedLinker(self.sourceDB, compiler.processor, inputTags[0], sharedTag, isSetwise = 1, library = library)
    sharedLinker.extraLibraries.extend(self.extraLibraries)
    linker.addVertex(archiver)
    linker.addEdges(consolidator, [archiver])
    linker.addEdges(sharedLinker, [consolidator])
    linker.addEdges(build.transform.Remover(inputTags), [sharedLinker])
    target.appendGraph(iorTarget)
    target.appendGraph(linker)
    return target

  def getClientCompileTarget(self):
    '''All purposes are in Cxx, so only a Cxx compiler is necessary for the stubs and cartilage.'''
    if len(self.usingSIDL.staticPackages):
      return build.buildGraph.BuildGraph()
    (target, compiler) = self.getGenericCompileTarget(['client'])
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
    '''Does nothing right now'''
    return

  def installServer(self, package):
    '''Does nothing right now'''
    return