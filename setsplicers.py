#!/usr/bin/env python
import user

import os
import sys
import re
import cPickle

def setSIDL(splicedimpls,dir,file):
  if file in splicedimpls['.sidl']:
    print 'Replacing sidl file '+os.path.join(dir,file)
    fd = open(os.path.join(dir,file),'w')
    fd.write(splicedimpls['.sidl'][file])
    fd.close()
  else:
    print 'WARNING: Found sidl file that is not in spliced database'
    print os.path.join(dir,file)    
  
def setSplicersDir(splicedimpls,dir,names):

  reg = re.compile('splicer.begin\(([A-Za-z0-9._]*)\)')

  if 'SCCS' in names: del names[names.index('SCCS')]
  if 'BitKeeper' in names: del names[names.index('BitKeeper')]
  if 'docs' in names: del names[names.index('docs')]
  for f in names:
    ext = os.path.splitext(f)[1]
    if ext == '.sidl':
      setSIDL(splicedimpls,dir,f)
      continue
    if not ext in splicedimpls: continue
    if f == '__init__.py': continue
    if not os.path.isfile(os.path.join(dir,f)): continue
    fd = open(os.path.join(dir,f),'r')
    foundreplacement = 0
    text = ''
    line = fd.readline()
    while line:
      text = text+line
      if not line.find('splicer.begin') == -1:
        fl = reg.search(line)
        name = fl.group(1)

        line = fd.readline()
        body = ''
        while line.find('splicer.end') == -1:
          body = body + line
          line = fd.readline()

        # replace body with saved splicer block
        if name in splicedimpls[ext] and not body == splicedimpls[ext][name]:          
          foundreplacement = 1
#          print 'Replacing -------'+name
#          print body
#          print 'with ------------'
#          print splicedimpls[ext][name]
          body = splicedimpls[ext][name]

        text = text+body
        text = text+line
      line = fd.readline()
    fd.close()

    if foundreplacement:
      print 'Replaced blocks in '+os.path.join(dir,f)
      fd = open(os.path.join(dir,f),'w')
      fd.write(body)
      fd.close()

#    print text
  
def setSplicers(directory):

  f    = open('splicerblocks', 'r')
  splicedimpls = cPickle.load(f)
  f.close()

  if not directory: directory = os.getcwd()
  os.path.walk(directory,setSplicersDir,splicedimpls)

    
if __name__ ==  '__main__':
  if len(sys.argv) > 2: sys.exit('Usage: getsplicers.py <directory>')
  sys.argv.append(None)
  setSplicers(sys.argv[1])
