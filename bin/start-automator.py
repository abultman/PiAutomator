#!/usr/bin/python
import os
import sys

basedir = os.path.normpath("%s/.." % (os.path.dirname(os.path.abspath(__file__))))

sys.path.reverse()
sys.path.append("%s/prg" % basedir)
sys.path.append("%s/lib" % basedir)
sys.path.reverse()

import automate
