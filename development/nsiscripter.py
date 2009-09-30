#!/usr/bin/python

import os
import os.path
import sys

if not os.path.isdir('horizons'):
    print "This program expects to be invoked from the Unknown Horizons root directory"
    sys.exit(-1)

installed_files = []
installed_dirs  = []

inst = []
remf = []
remd = []

for root, dirs, files in os.walk('.'):
    if True and '.svn' in dirs:
        dirs.remove('.svn')
    if not len(files) == 0:
        rootp = root[2:]
        if rootp[:4] == 'fife':
            files = filter(lambda s: s.split('.')[-1] in ('dll', 'py', 'png'), files)
            if not len(files):
                continue
        inst.append( ('  SetOutPath "$INSTDIR/%s"' % rootp).replace('/', '\\'))
        installed_dirs.append(rootp)
        for j in files:
            inst.append( ('  File "Unknown Horizons/%s/%s"' % (rootp, j)).replace('/', '\\'))
            installed_files.append('%s/%s' % (rootp, j))
            if j[-3:] == '.py':
                installed_files.append('%s.pyc' % ('%s/%s' % (rootp, j))[:-3])

for f in installed_files:
    remf.append( ('  Delete "$INSTDIR/%s"' % f).replace('/', '\\'))

for d in installed_dirs:
      remd.append( ('  RMDir "$INSTDIR/%s"' % d).replace('/', '\\'))

file('install.nsi', 'w').write(file('development/nsi.template', 'r').read() % ( '\n'.join(inst), '\n'.join(remf), '\n'.join(remd)))