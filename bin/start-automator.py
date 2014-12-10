import os
import sys
from astral import Astral

basedir = os.path.normpath("%s/.." % (os.path.dirname(os.path.abspath(__file__))))

print sys.path

sys.path.reverse()
sys.path.append("%s/prg" % basedir)
sys.path.append("%s/lib" % basedir)
sys.path.reverse()

if 'PIDFILE' in os.environ:
  with open(os.environ['PIDFILE'], 'w') as f:
     f.write(str(os.getpid()))
import automate
