from __future__ import absolute_import
from __future__ import print_function

import sys

try:
    import genpy
    from pyros_msgs.opt_as_nested import opt_bool  # This will duck punch the generated message type.

except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import genpy
    from pyros_msgs.opt_as_nested import opt_bool  # This will duck punch the generated message type.

import nose


def test_init_data():
    msg = opt_bool(data=True)
    assert msg.initialized_ is True
    assert msg.data is True

    msg = opt_bool(data=False)
    assert msg.initialized_ is True
    assert msg.data is False


def test_init_default():
    msg = opt_bool()
    assert msg.initialized_ is False
    assert msg.data is False  # default value from genpy


def test_force_init_excepts():
    with nose.tools.assert_raises(AttributeError) as cm:
        opt_bool(initialized_=True)
    assert cm.exception.message == "The field 'initialized_' is an internal field of pyros_msgs/opt_bool and should not be set by the user."

# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
