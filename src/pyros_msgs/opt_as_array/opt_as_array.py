from __future__ import absolute_import
from __future__ import print_function

import collections

import genpy
import six
import std_msgs.msg


def duck_punch(msg_mod, opt_slot_list):
    """
    Duck punch / monkey patch msg_mod, by declaring slots in opt_slot_list as optional slots
    :param msg_mod:
    :param opt_slot_list:
    :return:
    """
    def init_punch(self, *args, **kwds):
        __doc__ = msg_mod.__init__.__doc__
        if args or kwds:
            if args:  # the args for super(msg_mod, self) are fixed to the slots in ros messages
                # so we can change it to kwarg to be more accepting (and more robust for changes)
                kwds.update(zip([s for s in self.__slots__], args))
                args = ()

            # validating arg type (we should be more strict than ROS.)
            # this will be used to accept data from outside.
            # We need to take care of validating it as much as possible.
            for s, st in [(_slot, _slot_type)
                          for _slot, _slot_type in zip(self.__slots__, self._slot_types)
                          if _slot in opt_slot_list]:
                if st.endswith('[]'):
                    sv = kwds.get(s)
                    # if we have a list (and not a string)
                    skip_type_validation = False
                    if not isinstance(sv, six.string_types) and isinstance(sv, list):
                        if sv:
                            sv = sv[0]  # we only take the first element (this is an optional element expressed as array)
                        else:
                            kwds[s] = []  # if sv is empty we need to assign this directly
                            skip_type_validation = True
                    if not skip_type_validation and (
                                # we get that from genpy.message.check_type()
                                genpy.base.is_simple(st[:-2]) or
                                st[:-2] == 'string' or
                                st[:-2] == 'time' or
                                st[:-2] == 'duration' or
                                isinstance(sv, genpy.message.get_message_class(st[:-2]))
                    ):  # validate the type of the value
                        value = sv
                        # special case for string type(to support unicode kwds)
                        if st.startswith('string'):
                            value = str(value)
                        if value is not None:
                            kwds[s] = [value]
                    # otherwise we skip it.  # TODO : except ?

            super(msg_mod, self).__init__(*args, **kwds)
            # message fields cannot be None, assign default values for those that are
            if 'data' in self.__slots__ and self.data is None:
                self.data = []
        else:
            if 'data' in self.__slots__:
                self.data = []

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