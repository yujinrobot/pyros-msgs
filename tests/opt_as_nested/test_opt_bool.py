from __future__ import absolute_import, division, print_function

# TODO : property based testing. check hypothesis
# TODO : check all types

import sys

try:
    import genpy
    import pyros_msgs
    from pyros_msgs.opt_as_nested import opt_bool, test_opt_bool_as_nested  # This will duck punch the generated message type.

except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import genpy
    import pyros_msgs.opt_as_nested  # This will duck punch the standard message type initialization code.
    from pyros_msgs.msg import opt_bool, test_opt_bool_as_nested  # a message type just for testing

import nose

# patching  # TODO : move that into the type, we dont need to know the field name here...
pyros_msgs.opt_as_nested.duck_punch(test_opt_bool_as_nested, ['data'])


def test_init_data():
    # Same with an actual message containing this field
    optmsg = test_opt_bool_as_nested(data=True)
    assert optmsg.data == opt_bool(True)

    optmsg = test_opt_bool_as_nested(data=False)
    assert optmsg.data == opt_bool(False)


def test_init_raw():
    # Same with an actual message containing this field
    optmsg = test_opt_bool_as_nested(True)
    assert optmsg.data == opt_bool(True)

    optmsg = test_opt_bool_as_nested(False)
    assert optmsg.data == opt_bool(False)


def test_init_default():
    # Same with an actual message containing this field
    optmsg = test_opt_bool_as_nested()
    assert optmsg.data == opt_bool()
    assert optmsg.data != opt_bool(True)
    assert optmsg.data != opt_bool(False)


def test_init_excepts():
    with nose.tools.assert_raises(AttributeError) as cm:
        test_opt_bool_as_nested(data=42)
    assert isinstance(cm.exception, AttributeError)
    assert cm.exception.message == "42 does not match the accepted type schema for 'data' : (<type 'bool'>,)"


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
