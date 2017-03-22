from __future__ import absolute_import, division, print_function

from pyros_msgs.msg import (
    # no slot
    # None

    # data slot
    opt_bool,
    opt_int8, opt_int16, opt_int32, opt_int64,
    opt_uint8, opt_uint16, opt_uint32, opt_uint64,
    opt_float32, opt_float64,
    opt_string,

    opt_time,
    opt_duration,
    opt_header,

    # multiple slots
    # None
)


try:
    import genpy
except ImportError:
    import pyros_setup
    pyros_setup.configurable_import().configure().activate()
    import genpy

from pyros_msgs.common import (
    TypeCheckerException,
    typechecker_from_rosfield_type,
    TypeChecker,
)

from .ros_mappings import typechecker_from_rosfield_opttype

from pyros_msgs.common import six, six_long
import pyros_msgs.common.ros_mappings


# # We patch our Ros mappings with our optional nested types
# pyros_msgs.common.ros_mappings.rosfield_schematype_mapping.update({
#     # Optional nested field extension (This is handled by the nested modified constructor)
#     'pyros_msgs/opt_bool': TypeChecker(
#         lambda v=None: opt_bool() if v is None else opt_bool(data=v), # if isinstance(v, bool) else v,  # CAREFUL with default value and copying (ref counted) another opt_bool
#         (bool,)
#     ),
#     # 'pyros_msgs/opt_int8': (int, int),
#     # 'pyros_msgs/opt_int16': (int, int),
#     # 'pyros_msgs/opt_int32': (int, int),
#     # 'pyros_msgs/opt_int64': (six_long, (int, six_long)),
#     # 'pyros_msgs/opt_uint8': (int, int),
#     # 'pyros_msgs/opt_uint16': (int, int),
#     # 'pyros_msgs/opt_uint32': (int, int),
#     # 'pyros_msgs/opt_uint64': (six_long, (int, six_long)),
#     # 'pyros_msgs/opt_float32': (float, float),
#     # 'pyros_msgs/opt_float64': (float, float),
#     # # CAREFUL between ROS who wants byte string, and python3 where everything is unicode...
#     # 'pyros_msgs/opt_string': (six.binary_type, (six.binary_type, six.text_type)),
#     # # for time and duration we want to extract the slots
#     # # we want genpy to get the list of slots (rospy.Time doesnt have it)
#     # 'pyros_msgs/opt_time': ({'_sanitized': genpy.Time, 'secs': (int, int), 'nsecs': (int, int)}, genpy.Time),
#     # 'pyros_msgs/opt_duration': ({'_sanitized': genpy.Duration, 'secs': (int, int), 'nsecs': (int, int)}, genpy.Duration),
# })

# TODO add a way to generate a value that can be None, or the generated type
# TODO it means we need to change typeschema from a tuple (generated (1), accepted(n)) to a better structure (namedtuple ?)


def duck_punch(msg_mod):
    def init_punch(self, *args, **kwds):
        __doc__ = msg_mod.__init__.__doc__
        # excepting when passing initialized_. it is meant to be an internal field.
        if 'initialized_' in kwds.keys():
            raise AttributeError("The field 'initialized_' is an internal field of {0} and should not be set by the user.".format(msg_mod._type))
        if args:  # the args for super(msg_mod, self) are fixed to the slots in ros messages
            # so we can change it to kwarg to be more accepting (and more robust for changes)
            kwds.update(zip([s for s in self.__slots__ if s != 'initialized_'], args))
            args = ()

        kwds['initialized_'] = True if 'data' in kwds else False
        # TODO : use typeschemas predicate to link initialized_ value and data value

        # We build our own type schema here from our slots
        # CAREFUL : slot discovery doesnt work well with inheritance -> fine since ROS msgs do not have any inheritance concept.
        slotsdict = {
            s: typechecker_from_rosfield_type(srt)
            for s, srt in zip(msg_mod.__slots__, msg_mod._slot_types)
            if s not in ['initialized_']
            }

        # TODO : use accepted typeschema to filter args

        # TODO : use type schema method to build this instance

        # We assign slots one by one after verifying and sanitizing the type
        for s, st in slotsdict.items():
            # check all slots values passed in kwds.
            # We assign default values here to make sure everything is valid
            sval = kwds.get(s, st.default())
            try:
                kwds[s] = st(sval)
            except TypeCheckerException as tse:
                # TODO : improve the exception message
                # we convert back to a standard python exception
                raise AttributeError(
                    "{sval} does not match the accepted type schema for '{s}' : {st.accepter}".format(**locals()))

        # ROS messages accept either args or kwargs, not both
        super(msg_mod, self).__init__(**kwds)

    # duck punching into genpy generated message classes, to set initialized_ field properly
    msg_mod.__init__ = init_punch

    # CHANGE : Not allowing to set default value (it forces us to depend on a fixed structure with 'data' slot)
    #
    # # adding settable default value behavior (doesnt matter for empty type though)
    # msg_mod._default_value = typechecker_from_rosfield_type(msg_mod._slot_types[msg_mod.__slots__.index('data')]).default()
    #
    # def reset_default(cls, new_default_value=None):
    #     cls._default_value = new_default_value or typechecker_from_rosfield_type(msg_mod._slot_types[msg_mod.__slots__.index('data')]).default()
    #
    # msg_mod.reset_default = classmethod(reset_default)


#
# default data values extracted from genpy.generator:default_value()
#

# TODO : get rid of these. We shouldnt make these message any special.
# Our logic of adding _initialized_optional field should make any message type optional in any nesting message type.
for msg_int_mod in [
    opt_int8, opt_int16, opt_int32, opt_int64,
    opt_uint8, opt_uint16, opt_uint32, opt_uint64,
]:
    duck_punch(msg_int_mod)

for msg_float_mod in [
    opt_float32, opt_float64,
]:
    duck_punch(msg_float_mod)

duck_punch(opt_string)
duck_punch(opt_bool)

duck_punch(opt_time)
duck_punch(opt_duration)

#duck_punch(opt_header, std_msgs.msg.Header())