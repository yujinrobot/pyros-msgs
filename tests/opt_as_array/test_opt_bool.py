from __future__ import absolute_import
from __future__ import print_function

# TODO : property based testing. check hypothesis
# TODO : check all types

try:
    import pyros_msgs.opt_as_array  # This will duck punch the standard message type initialization code.
    from pyros_msgs.msg import test_opt_bool_as_array  # a message type just for testing

except ImportError:
    # Because we need to access Ros message types here (from ROS env or from virtualenv, or from somewhere else)
    import pyros_setup
    # We rely on default configuration to point us ot the proper distro
    pyros_setup.configurable_import().configure().activate()
    import pyros_msgs.opt_as_array
    from pyros_msgs.msg import test_opt_bool_as_array  # a message type just for testing

# patching (need to know the field name)
pyros_msgs.opt_as_array.duck_punch(test_opt_bool_as_array, ['data'])

import nose


def test_init_rosdata():
    msg = test_opt_bool_as_array(data=[True])
    assert msg.data == [True]

    msg = test_opt_bool_as_array(data=[False])
    assert msg.data == [False]

    msg = test_opt_bool_as_array(data=[])
    assert msg.data == []


def test_init_data():
    msg = test_opt_bool_as_array(data=True)
    assert msg.data == [True]

    msg = test_opt_bool_as_array(data=False)
    assert msg.data == [False]


def test_init_raw():
    msg = test_opt_bool_as_array(True)
    assert msg.data == [True]

    msg = test_opt_bool_as_array(False)
    assert msg.data == [False]


def test_init_default():
    msg = test_opt_bool_as_array()
    assert msg.data == []


def test_wrong_init_except():
    with nose.tools.assert_raises(AttributeError) as cm:
        test_opt_bool_as_array(42)
    assert isinstance(cm.exception, AttributeError)
    assert cm.exception.message == "42 does not match its accepted type schema for 'data' : (<type 'bool'>, [<type 'bool'>])"


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)
