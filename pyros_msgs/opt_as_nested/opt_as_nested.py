from __future__ import absolute_import
from __future__ import print_function

import collections

import genpy
import six
import std_msgs.msg
from pyros_msgs.common import (
    six_long,
    TypeCheckerException,
    typechecker_from_rosfield_type,
    TypeChecker
)

from .ros_mappings import typechecker_from_rosfield_opttype


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
        slotsdict = {
            s: typechecker_from_rosfield_opttype(srt)
            for s, srt in zip(msg_mod.__slots__, msg_mod._slot_types)
            if s not in ['initialized_']
            }

        # TODO : use accepted typeschema to filter args

        # TODO : use type schema method to build this instance

        # We assign slots one by one after verifying and sanitizing the type
        for s, st in slotsdict.items():
            # check all slots values passed in kwds.
            # We DO NOT assign default values here (nested type should manage default values for fields)
            sval = kwds.get(s)
            try:
                if sval is not None:  # we allow any field to be None without typecheck
                    kwds[s] = st(sval)
            except TypeCheckerException as tse:
                # TODO : improve the exception message
                # we convert back to a standard python exception
                raise AttributeError("{sval} does not match the accepted type schema for '{s}' : {st.accepter}".format(**locals()))

        # By now the kwds is filled up with values
        # the parent init will do the usual ROS message setup.
        super(msg_mod, self).__init__(*args, **kwds)

        # We follow the usual ROS generated message behavior and assign default values
        for s, st in [(_slot, typechecker_from_rosfield_type(_slot_type)) for _slot, _slot_type in zip(self.__slots__, self._slot_types)]:
            if getattr(self, s) is None:
                setattr(self, s, st.default())

    # duck punching into genpy generated message classes.
    msg_mod.__init__ = init_punch

    # Registering the list of optional field (required by pyros_schemas)
    msg_mod._opt_slots = opt_slot_list
