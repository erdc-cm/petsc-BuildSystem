#!/usr/bin/env python
import user
import importer
import script
import sourceControl
import install.urlMapping

import os
import urllib

class Bootstrapper(script.Script):
  def __init__(self):
    import sourceControl
    script.Script.__init__(self)
    self.vc = sourceControl.BitKeeper()
    self.mapper = install.urlMapping.UrlMappingNew()
    return

  def setupHelp(self, help):
    import nargs

    help = script.Script.setupHelp(self, help)
    help.addArgument('Bootstrapper', 'baseDirectory', nargs.ArgDir(None, os.getcwd(), 'The root directory for all repositories', isTemporary = 1))
    help.addArgument('Bootstrapper', 'compilerRepository', nargs.Arg(None, 'ftp://ftp.mcs.anl.gov/pub/petsc/ase/Compiler.tgz', 'The repository containing the SIDL compiler', isTemporary = 1))
    return help

  def setup(self):
    script.Script.setup(self)
    self.mapper.setup()
    return

  def getBaseDir(self):
    if not hasattr(self, '_baseDir'):
      return self.argDB['baseDirectory']
    return self._baseDir
  def setBaseDir(self, baseDir):
    self._baseDir = baseDir
    return
  baseDir = property(getBaseDir, setBaseDir, doc = 'The root directory for all repositories')

  def getCompilerRepository(self):
    if not hasattr(self, '_compilerRepository'):
      return self.argDB['compilerRepository']
    return self._compilerRepository
  def setCompilerRepository(self, compilerRepository):
    self._compilerRepository = compilerRepository
    return
  compilerRepository = property(getCompilerRepository, setCompilerRepository, doc = 'The repository containing the SIDL compiler')

  def clone(self, url):
    path = os.path.join(self.baseDir, self.mapper.getRepositoryPath(url))
    dir = os.path.dirname(path)
    if not os.path.isdir(dir):
      os.mkdir(dir)
    self.logPrint('Cloning '+url+' into '+path)
    return self.vc.clone(self.mapper.getMappedUrl(url), path)

  def downloadASE(self):
    '''Clone the Runtime, and PLY repositories. Download the Runtime and Compiler bootstrap tarballs'''
    self.clone('bk://ply.bkbits.net/ply-dev')
    self.clone('bk://ase.bkbits.net/Runtime')
    self.logPrint('Retrieving Compiler')
    url = 'bk://ase.bkbits.net/Compiler'
    dir = os.path.join(self.baseDir, os.path.dirname(self.mapper.getRepositoryPath(url)))
    tarball = os.path.join(dir, self.mapper.getRepositoryName(url)+'.tgz')
    if not os.path.isdir(dir):
      os.makedirs(dir)
    #urllib.urlretrieve(self.mapper.getMappedUrl(url)+'.tgz', tarball)
    urllib.urlretrieve(self.compilerRepository, tarball)
    self.executeShellCommand('cd '+dir+'; tar -xzf '+os.path.basename(tarball))
    os.remove(tarball)
    return

  def downloadBootstrap(self, url):
    self.logPrint('Retrieving bootstrap for '+url)
    dir = os.path.join(self.baseDir, self.mapper.getRepositoryPath(url))
    tarball = os.path.join(dir, self.mapper.getRepositoryName(url)+'_bootstrap.tgz')
    urllib.urlretrieve(self.mapper.getMappedUrl(url+'_bootstrap')+'.tgz', tarball)
    self.executeShellCommand('cd '+dir+'; tar -xzf '+os.path.basename(tarball))
    os.remove(tarball)
    return

  def build(self, path):
    '''Build a project'''
    self.logPrint('Building '+path)
    oldDir = os.getcwd()
    os.chdir(path)
    make = self.getModule(os.path.abspath(path), 'make').Make()
    make.argDB['SCANDAL_DIR'] = os.path.join(self.baseDir, 'ase', 'Compiler', 'driver', 'python')
    make.run()
    os.chdir(oldDir)
    return

  def disableBootstrap(self, url):
    '''Disable the Python bootstrap'''
    self.logPrint('Disabling bootstrap in '+url)
    dir = install.urlMapping.UrlMappingNew.getRepositoryPath(url)
    os.rename(os.path.join(dir, 'client-bootstrap'), os.path.join(dir, 'client-bootstrap-old'))
    return

  def safeRemove(self, f):
    '''If file f exists, remove it and return True, otherwise return False'''
    if os.path.isfile(f):
      self.logPrint('Removing '+f)
      os.remove(f)
      return 1
    elif os.path.isdir(f):
      self.logPrint('Removing '+f)
      import shutil
      shutil.rmtree(f)
      return 1
    return 0

  def run(self):
    [self.safeRemove(f) for f in ['RDict.db', 'RDict.log']]
    self.setup()
    [self.safeRemove(os.path.join(self.baseDir, f)) for f in ['ply', 'ase']]
    self.downloadASE()
    for url in ['bk://ase.bkbits.net/Runtime', 'bk://ase.bkbits.net/Compiler']:
      self.downloadBootstrap(url)
    for url in ['bk://ase.bkbits.net/Runtime', 'bk://ase.bkbits.net/Compiler']:
      self.build(os.path.abspath(install.urlMapping.UrlMappingNew.getRepositoryPath(url)))
      self.disableBootstrap(url)
    return

if __name__ == '__main__':
  Bootstrapper().run()
