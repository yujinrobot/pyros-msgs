from __future__ import absolute_import
from __future__ import print_function

"""
pyros_msgs.opt_as_array is a module that interprets arrays as optional fields in a message.

This is useful if you have an existing ros message type, and want to allow some field to not have any defined value :
An empty array will represent that

When importing this module, the ros message field default value for array will be changed to an empty array.
"""


from .opt_as_array import duck_punch