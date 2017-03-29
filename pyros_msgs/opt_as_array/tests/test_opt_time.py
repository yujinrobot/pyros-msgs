from __future__ import absolute_import
from __future__ import print_function

try:
    import rospy
    import pyros_msgs.opt_as_array  # This will duck punch the standard message type initialization code.
    from pyros_msgs.opt_as_array import test_opt_time_as_array  # a message type just for testing
except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import rospy
    import pyros_msgs.opt_as_array  # This will duck punch the standard message type initialization code.
    from pyros_msgs.opt_as_array import test_opt_time_as_array  # a message type just for testing

# patching
pyros_msgs.opt_as_array.duck_punch(test_opt_time_as_array, ['data'])

import nose


def test_init_rosdata():
    t = rospy.Time(secs=21, nsecs=42)
    msg = test_opt_time_as_array(data=[t])
    assert msg.data == [t]


def test_init_data():
    t = rospy.Time(secs=21, nsecs=42)
    msg = test_opt_time_as_array(data=t)
    assert msg.data == [t]


def test_init_raw():
    t = rospy.Time(secs=21, nsecs=42)
    msg = test_opt_time_as_array(t)
    assert msg.data == [t]


def test_init_default():
    msg = test_opt_time_as_array()
    assert msg.data == []


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
