import fileset
import build.transform

import os

class FileChanged (build.transform.Transform):
  '''Detects whether files have changed using checksums'''
  def __init__(self, sourceDB, inputTag = None, changedTag = 'changed', unchangedTag = 'unchanged'):
    build.transform.Transform.__init__(self)
    self.sourceDB      = sourceDB
    self.inputTag      = inputTag
    self.useUpdateFlag = 0
    self.changed       = fileset.FileSet(tag = changedTag)
    self.unchanged     = fileset.FileSet(tag = unchangedTag)
    self.output.children.append(self.changed)
    self.output.children.append(self.unchanged)
    return

  def compare(self, source, sourceEntry):
    '''Return True if the checksum for "source" has changed since "sourceEntry" was recorded'''
    if sourceEntry[4] and self.useUpdateFlag:
      self.debugPrint('Update flag indicates '+source+' did not change', 3, 'sourceDB')
    else:
      self.debugPrint('Checking for '+source+' in the source database', 3, 'sourceDB')
      checksum = self.sourceDB.getChecksum(source)
      if not sourceEntry[0] == checksum:
        self.debugPrint(source+' has changed relative to the source database: '+str(sourceEntry[0])+' <> '+str(checksum), 3, 'sourceDB')
        return 1
    return 0

  def hasChanged(self, source):
    '''Returns True if "source" has changed since it was last updates in the source database'''
    try:
      if not os.path.exists(source):
        self.debugPrint(source+' does not exist', 3, 'sourceDB')
      else:
        if not self.compare(source, self.sourceDB[source]):
          for dep in self.sourceDB[source][3]:
            try:
              if self.compare(dep, self.sourceDB[dep]):
                return 1
            except KeyError: pass
          return 0
    except KeyError:
      self.debugPrint(source+' does not exist in source database', 3, 'sourceDB')
    return 1

  def handleFile(self, f, tag):
    '''Place the file into either the "changed" or "unchanged" output set
       - If inputTag was specified, only handle files with this tag'''
    if self.inputTag is None or tag == self.inputTag:
      if self.hasChanged(f):
        self.changed.append(f)
      else:
        self.unchanged.append(f)
        self.sourceDB.setUpdateFlag(f)
      return self.output
    return build.transform.Transform.handleFile(self, f, tag)

class GenericTag (FileChanged):
  '''Uses input tag, extension and directory checks to group files which need further processing'''
  def __init__(self, sourceDB, outputTag, inputTag = None, ext = '', deferredExt = None, root = None):
    FileChanged.__init__(self, sourceDB, inputTag, outputTag, 'old '+outputTag)
    self.ext   = ext
    if isinstance(self.ext, list):
      self.ext = map(lambda x: '.'+x, self.ext)
    elif isinstance(self.ext, str):
      self.ext = ['.'+self.ext]
    self.deferredExt   = deferredExt
    if isinstance(self.deferredExt, list):
      self.deferredExt = map(lambda x: '.'+x, self.deferredExt)
    elif isinstance(self.deferredExt, str):
      self.deferredExt = ['.'+self.deferredExt]
    self.root   = root
    if not self.root is None:
      self.root = os.path.normpath(self.root)
    self.deferredUpdates = build.fileset.FileSet(tag = 'update '+outputTag)
    self.output.children.append(self.deferredUpdates)
    return

  def __str__(self):
    return 'Tag transform for extension '+str(self.ext)+' to tag '+self.changed.tag

  def handleFile(self, f, tag):
    '''- If the file is not in the specified root directory, use the default handler
       - If the file is in the extension list, call the parent method
       - If the file is in the deferred extension list and has changed, put it in the update set'''
    (base, ext) = os.path.splitext(f)
    if not self.root or self.root+os.sep == os.path.commonprefix([os.path.normpath(base), self.root+os.sep]):
      if self.ext is None or ext in self.ext:
        return FileChanged.handleFile(self, f, tag)
      elif not self.deferredExt is None and ext in self.deferredExt:
        if self.hasChanged(f):
          self.deferredUpdates.append(f)
          return self.output
    return build.transform.Transform.handleFile(self, f, tag)

  def handleFileSet(self, set):
    '''Check root directory if given, and then execute the default set handlung method'''
    if self.root and not os.path.isdir(self.root):
      raise RuntimeError('Invalid root directory for tagging operation: '+self.root)
    return FileChanged.handleFileSet(self, set)

class Update (build.transform.Transform):
  '''Update nodes process files whose update in the source database was delayed'''
  def __init__(self, sourceDB, tags = None):
    build.transform.Transform.__init__(self)
    self.sourceDB = sourceDB
    if tags is None:
      self.tags   = []
    else:
      self.tags   = tags
    if self.tags and not isinstance(self.tags, list):
      self.tags = [self.tags]
    self.tags   = map(lambda tag: 'update '+tag, self.tags)
    return

  def __str__(self):
    return 'Update transform for '+str(self.tags)

  def handleFile(self, f, tag):
    '''If the file tag starts with "update", then update it in the source database'''
    if (self.tags and tag in self.tags) or (tag and tag[:6] == 'update'):
      self.sourceDB.updateSource(f)
    else:
      build.transform.Transform.handleFile(self, f, tag)
    return self.output
