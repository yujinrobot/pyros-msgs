from __future__ import absolute_import
from __future__ import print_function

import collections

import genpy
import six
import std_msgs.msg
from pyros_msgs import ros_python_type_mapping, ros_python_default_mapping


def duck_punch(msg_mod, opt_slot_list):
    """
    Duck punch / monkey patch msg_mod, by declaring slots in opt_slot_list as optional slots
    :param msg_mod:
    :param opt_slot_list:
    :return:
    """
    def init_punch(self, *args, **kwds):
        __doc__ = msg_mod.__init__.__doc__
        if args:  # the args for super(msg_mod, self) are fixed to the slots in ros messages
            # so we can change it to kwarg to be more accepting (and more robust for changes)
            kwds.update(zip([s for s in self.__slots__], args))
            args = ()

        def validate_type(slot_value, slot_type):
            """ Validate the type of the value, and modify the slot dict on the fly"""
            # if (  # we get that from genpy.message.check_type()
            #     genpy.base.is_simple(slot_type) or
            #     slot_type == 'string' or
            #     slot_type == 'time' or
            #     slot_type == 'duration' or
            #     isinstance(slot_value, genpy.message.get_message_class(slot_type))
            # ):  # validate the type of the value
            #     # special case for string type(to support unicode kwds)
            #     if slot_type.startswith('string'):
            #         return str(slot_value)
            #     # elif slot_type.startswith('time'):
            #     #     return str(value)
            #     # elif slot_type.startswith('duration'):
            #     #     return str(value)
            #     # elif isinstance(sv, genpy.message.get_message_class(slot_type)):
            #     #     return genpy.message.get_message_class(slot_type)()
            #     else:
            #         return slot_value
            # elif not slot_value and slot_type == 'std_msgs/Empty':  # special empty case
            #     return []  # or None ?
            # else:
            #     raise TypeError("value '{slot_value}' is not of type {slot_type}".format(**locals()))

            if isinstance(slot_value, six.string_types):
                slot_value = str(slot_value)  # forcing str type (converting from unicode if needed)

            # Detecting possible type problems
            if slot_type in ros_python_type_mapping and not isinstance(slot_value, ros_python_type_mapping.get(slot_type)):
                # simple field type
                raise TypeError("value '{slot_value}' is not of type {slot_type}".format(**locals()))

            elif isinstance(slot_value, list) and not isinstance(slot_value, six.string_types):
                # array field type
                if len(slot_value) > 0:
                    # we only take the first element (this is an optional element expressed as array)
                    # and we validate it
                    slot_value = validate_type(slot_value[0], slot_type[:-2])

            elif slot_type not in ros_python_type_mapping:
                # custom field type
                try:
                    msg_class = genpy.message.get_message_class(slot_type)
                except:
                    raise Exception("IMPLEMENT THAT !") # TODO : implement clear error message about custom message not found
                if not isinstance(slot_value, msg_class):
                    raise TypeError("value '{slot_value}' is not of type {slot_type[:-2]}".format(**locals()))

            return slot_value

        def get_default_val_from_type(slot_type):

            if slot_type in ros_python_default_mapping:
                # simple type (check genpy.base.is_simple())
                return ros_python_default_mapping.get(slot_type)
            elif slot_type.endswith('[]'):
                # array type (recurse)
                return get_default_val_from_type(slot_type[:-2])
            elif isinstance(sv, genpy.message.get_message_class(slot_type)):
                # custom type (call __init__())
                return genpy.message.get_message_class(slot_type)()
            else:
                raise TypeError("default value for type {slot_type} is unknown".format(**locals()))

        # Validating arg type (we should be more strict than ROS.)
        for s, st in [(_slot, _slot_type) for _slot, _slot_type in zip(self.__slots__, self._slot_types)]:

            if s in opt_slot_list and st.endswith('[]'):
                if kwds and s in kwds:
                    if not isinstance(kwds.get(s), list):  # make it a list if needed
                        kwds[s] = [kwds.get(s)]
                    try:
                        sv = validate_type(kwds.get(s), st)
                    except TypeError as te:
                        sv = kwds.get(s)
                        raise AttributeError("field {s} has value {sv} which is not of type {st}".format(**locals()))
                else:
                    kwds[s] = []

            else:  # not an optional field
                if kwds:
                    kwds[s] = validate_type(kwds.get(s), st)
                # else it will be set to None by parent class (according to original ROS message behavior)

        # By now the kwds is filled up with values
        # the parent init will do the usual ROS message setup.
        super(msg_mod, self).__init__(*args, **kwds)

        # We follow the usual ROS generated message behavior and assign default values
        for s, st in [(_slot, _slot_type) for _slot, _slot_type in zip(self.__slots__, self._slot_types)]:
            if getattr(self, s) is None:
                setattr(self, s, get_default_val_from_type(s, st))



    # SEEMS WE CANNOT DO THAT => keep everything in an array. makes the null [] case less surprising anyway...
    # def get_punch(self, key):
    #     __doc__ = msg_mod.__get__.__doc__
    #     if key in opt_slot_list:
    #         return getattr(self, key)[0]
    #
    # def set_punch(self, key, value):
    #     __doc__ = msg_mod.__set__.__doc__
    #     if key in opt_slot_list:
    #         getattr(self, key)[0] = value
    #
    # def delete_punch(self, key):
    #     __doc__ = msg_mod.__delete__.__doc__
    #     if key in opt_slot_list:
    #         setattr(self, key, [])

    # duck punching into genpy generated message classes.
    msg_mod.__init__ = init_punch
    # msg_mod.__get__ = get_punch
    # msg_mod.__set__ = set_punch
    # msg_mod.__delete__ = delete_punch
#
# default data values extracted from genpy.generator:default_value()
#

# for msg_int_mod in [
#     std_msgs.msg.int8, opt_int16, opt_int32, opt_int64,
#     opt_uint8, opt_uint16, opt_uint32, opt_uint64,
# ]:
#     duck_punch(msg_int_mod, 0)
#
# for msg_float_mod in [
#     opt_float32, opt_float64,
# ]:
#     duck_punch(msg_float_mod, 0.)
#
# duck_punch(opt_string, '')
# duck_punch(opt_bool, False)
# duck_punch(opt_empty)  # default value should be unused here
#
# duck_punch(opt_time, genpy.Time())
# duck_punch(opt_duration, genpy.Duration())
# duck_punch(opt_header, std_msgs.msg.Header())

# __all__ = [
#     'opt_empty',
#
#     'opt_bool',
#     'opt_int8', 'opt_int16', 'opt_int32', 'opt_int64',
#     'opt_uint8', 'opt_uint16', 'opt_uint32', 'opt_uint64',
#     'opt_float32', 'opt_float64',
#     'opt_string',
#
#     'opt_time',
#     'opt_duration',
#     'opt_header',
# ]