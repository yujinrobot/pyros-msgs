from __future__ import absolute_import, division, print_function

import pytest
from StringIO import StringIO

try:
    import std_msgs.msg as std_msgs
    import pyros_msgs
    import genpy
except ImportError:
    import pyros_setup
    pyros_setup.configurable_import().configure().activate()
    import std_msgs.msg as std_msgs
    import pyros_msgs
    import genpy

import six

from pyros_msgs.common.typechecker import (
    six_long,
    maybe_list,
    maybe_tuple,
    Sanitizer, Accepter, Array, Any,
    TypeChecker,
    TypeCheckerException,
)

from pyros_msgs.common.ros_mappings import typechecker_from_rosfield_type



from hypothesis import given, example, settings, Verbosity, HealthCheck
import hypothesis.strategies as st


# The main point here is insuring that any sanitized type will safely serialize and deserialize
# And also that any type that doesnt safely serialize / deserialize will not pass hte type checker

rosmsg_slot_types = [
    ('bool', st.booleans()),
    ('int', st.integers()),
    ('float', st.floats()),
    ('string', st.binary()),
    ('time', st.builds(genpy.Time, secs=st.integers(min_value=0), nsecs=st.integers(min_value=0))),  # ROS time
    ('duration', st.builds(genpy.Duration, secs=st.integers(), nsecs=st.integers())),  # ROS duration
]

rosmsg_slot_arraytypes = [
    (s[0] + '[]',  st.lists(elements=s[1]))
    for s in rosmsg_slot_types
]

# TODO : is there a way to generate messages on the fly to test all possible field combinations ?

# For now We use a set of basic messages for testing
std_msgs_types_strat_ok = {
    'std_msgs/Bool': st.builds(std_msgs.Bool, data=st.booleans()),
    'std_msgs/Int8': st.builds(std_msgs.Int8, data=st.integers()),
    'std_msgs/Int16': st.builds(std_msgs.Int16, data=st.integers()),
    'std_msgs/Int32': st.builds(std_msgs.Int32, data=st.integers()),
    'std_msgs/Int64': st.builds(std_msgs.Int64, data=st.integers()),
    'std_msgs/UInt8': st.builds(std_msgs.UInt8, data=st.integers()),
    'std_msgs/UInt16': st.builds(std_msgs.UInt16, data=st.integers()),
    'std_msgs/UInt32': st.builds(std_msgs.UInt32, data=st.integers()),
    'std_msgs/UInt64': st.builds(std_msgs.UInt64, data=st.integers()),
    'std_msgs/Float32': st.builds(std_msgs.Float32, data=st.floats()),
    'std_msgs/Float64': st.builds(std_msgs.Float64, data=st.floats()),
    'std_msgs/String': st.builds(std_msgs.String, data=st.one_of(st.binary(), st.text())),
    'std_msgs/Time': st.builds(std_msgs.Time, data=st.builds(genpy.Time, secs=st.integers(min_value=0), nsecs=st.integers(min_value=0))),
    'std_msgs/Duration': st.builds(std_msgs.Duration, data=st.builds(genpy.Duration, secs=st.integers(), nsecs=st.integers())),
    # TODO : add more. we should test all.
}

std_msgs_types_strat_broken = {
    # everything else...
    'std_msgs/Bool': st.builds(std_msgs.Bool, data=st.one_of(st.integers(), st.floats())),
    'std_msgs/Int8': st.builds(std_msgs.Int8, data=st.one_of(st.booleans(), st.floats())),
    'std_msgs/Int16': st.builds(std_msgs.Int16, data=st.one_of(st.booleans(), st.floats())),
    'std_msgs/Int32': st.builds(std_msgs.Int32, data=st.one_of(st.booleans(), st.floats())),
    'std_msgs/Int64': st.builds(std_msgs.Int64, data=st.one_of(st.booleans(), st.floats())),
    'std_msgs/UInt8': st.builds(std_msgs.UInt8, data=st.one_of(st.booleans(), st.floats())),
    'std_msgs/UInt16': st.builds(std_msgs.UInt16, data=st.one_of(st.booleans(), st.floats())),
    'std_msgs/UInt32': st.builds(std_msgs.UInt32, data=st.one_of(st.booleans(), st.floats())),
    'std_msgs/UInt64': st.builds(std_msgs.UInt64, data=st.one_of(st.booleans(), st.floats())),
    'std_msgs/Float32': st.builds(std_msgs.Float32, data=st.one_of(st.booleans(), st.floats())),
    'std_msgs/Float64': st.builds(std_msgs.Float64, data=st.one_of(st.booleans(), st.floats())),
    # TODO : add more. we should test all
}

pyros_msgs_types_strat_ok = {
    # TODO
}

pyros_msgs_types_strat_broken = {

}

# We need a composite strategy to link slot type and slot value
@st.composite
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def msg_type_and_value(draw, msgs_type_st):
    msg_type = draw(st.sampled_from(msgs_type_st))
    msg_value = draw(msgs_type_st.get(msg_type))
    return msg_type, msg_value


@given(msg_type_and_value(std_msgs_types_strat_ok))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_serialize_deserialize_inverse(msg_type_and_ok_value):
    """"""
    tc = typechecker_from_rosfield_type(msg_type_and_ok_value[0])
    value = tc(msg_type_and_ok_value[1])

    # sending
    buff = StringIO()
    value.serialize(buff)
    serialized = buff.getvalue()
    buff.close()

    # receiving
    received = tc()
    received.deserialized(serialized)

    assert received == value


@given(msg_type_and_value(std_msgs_types_strat_broken))
@settings(verbosity=Verbosity.verbose, timeout=1, suppress_health_check=[HealthCheck.too_slow])
def test_typechecker_typechecker_prevent_broken_values(msg_type_and_bad_value):
    tc = typechecker_from_rosfield_type(msg_type_and_bad_value[0])

    # assert we have a somehow broken value :
    with pytest.raises(Exception) as excinfo:
        value = tc(msg_type_and_bad_value[1])

        # sending
        buff = StringIO()
        value.serialize(buff)
        serialized = buff.getvalue()
        buff.close()

        # receiving
        received = tc()
        received.deserialized(serialized)

    # assert the type checker doesnt accept it
    with pytest.raises(TypeCheckerException) as excinfo:
        _ = tc(msg_type_and_bad_value[1])
    assert 'cannot be accepted' in excinfo.value
