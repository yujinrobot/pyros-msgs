from __future__ import absolute_import
from __future__ import print_function

import collections

import genpy
import six
import std_msgs.msg
from pyros_msgs.common import (
    TypeSchemaException,
    typeschema_from_rostype,
    typeschema_check,
    typeschema_default,
)


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

        # We build our own type schema here from our slots
        # CAREFUL : slot discovery doesnt work well with inheritance -> fine since ROS msgs do not have any inheritance concept.
        ts = {
            slot: typeschema_from_rostype(slot_type)
            for slot, slot_type in zip(self.__slots__, self._slot_types)
        }

        # We assign slots one by one after verifying and sanitizing the type
        for s, st in ts.items():
            # check all slots values passed in kwds.
            # We assign default values here to make sure everything is valid
            sval = kwds.get(s, typeschema_default(st))
            try:
                kwds[s] = typeschema_check(st, sval)
            except TypeSchemaException as tse:
                # TODO : improve the exception message
                # we convert back to a standard python exception
                raise AttributeError("{sval} does not match its accepted type schema for '{s}' : {st[1]}".format(**locals()))

        # By now the kwds is filled up with values
        # the parent init will do the usual ROS message setup.
        super(msg_mod, self).__init__(*args, **kwds)

        # Note here no slot should be set to None.
        # Default values have been forcibly assigned when required.

    # duck punching into genpy generated message classes.
    msg_mod.__init__ = init_punch
    # msg_mod.__get__ = get_punch
    # msg_mod.__set__ = set_punch
    # msg_mod.__delete__ = delete_punch

    # Registering the list of optional field (required by pyros_schemas)
    msg_mod._opt_slots = opt_slot_list
