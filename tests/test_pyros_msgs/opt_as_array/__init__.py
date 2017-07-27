from __future__ import absolute_import, division, print_function

import os
import sys
import site

added_site_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'rosdeps')
print("Adding site directory {0} to access genmsg, genpy and, std_msgs".format(added_site_dir))
site.addsitedir(added_site_dir)

# Using genpy directly if ROS has been setup (while using from ROS pkg)
import genpy, genmsg

print(sys.path)

import rosimport
rosimport.activate()
