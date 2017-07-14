from __future__ import absolute_import, division, print_function

import os
import sys
import site

site.addsitedir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps'))
site.addsitedir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'pydeps'))

import rosimport
rosimport.activate()
