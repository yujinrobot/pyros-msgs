from __future__ import absolute_import
from __future__ import print_function

try:
    import genpy
    import pyros_msgs.opt_as_nested
except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import genpy
    import pyros_msgs.opt_as_nested

import nose


def test_init_data_internal():
    msg = pyros_msgs.opt_as_nested.opt_int64(data=42)
    assert msg.initialized_ is True
    assert msg.data == 42


def test_init_default_internal():
    msg = pyros_msgs.opt_as_nested.opt_int64()
    assert msg.initialized_ is False
    assert msg.data == 0  # default value

# DROPPED FEATURE
# def test_reset_default_internal():
#     pyros_msgs.opt_as_nested.opt_int64.reset_default(23)
#     msg = pyros_msgs.opt_as_nested.opt_int64()
#     assert msg.initialized_ is False
#     assert msg.data == 23
#     pyros_msgs.opt_as_nested.opt_int64.reset_default()
#     msg = pyros_msgs.opt_as_nested.opt_int64()
#     assert msg.initialized_ is False
#     assert msg.data == 0  # default value


def test_force_init_excepts_internal():
    with nose.tools.assert_raises(AttributeError) as cm:
        pyros_msgs.opt_as_nested.opt_int64(initialized_=True)
    assert cm.exception.message == "The field 'initialized_' is an internal field of pyros_msgs/opt_int64 and should not be set by the user."


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
