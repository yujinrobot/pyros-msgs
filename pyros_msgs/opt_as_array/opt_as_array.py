from __future__ import absolute_import, division, print_function

from pyros_msgs.common import (
    maybe_list,
    TypeCheckerException,
    typechecker_from_rosfield_type,
    TypeChecker,
)

from .ros_mappings import typechecker_from_rosfield_opttype
from contracts import contract


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
            kwds.update(zip(self.__slots__, args))
            args = ()

        # We build our own type schema here from our slots
        # CAREFUL : slot discovery doesnt work well with inheritance -> fine since ROS msgs do not have any inheritance concept.
        slotsdict = {
            s: typechecker_from_rosfield_opttype(srt) if s in self._opt_slots else typechecker_from_rosfield_type(srt)
            for s, srt in zip(msg_mod.__slots__, msg_mod._slot_types)
        }

        # assert isinstance(rostype, genpy.Message) # TODO : not working ??

        # TODO : use accepted typeschema to filter args

        # TODO : use type schema method to build this instance

        # We assign slots one by one after verifying and sanitizing the type
        for s, st in slotsdict.items():
            # check all slots values passed in kwds.
            # We assign default values here to make sure everything is valid
            sval = kwds.get(s, st.default())
            try:
                # implicit conversion for optional slots #TODO : verify if we do need it or not
                if s in self._opt_slots:
                    sval = maybe_list(sval)
                kwds[s] = st(sval)  # type checking val
            except TypeCheckerException as tse:
                # TODO : improve the exception message
                # we convert back to a standard python exception
                raise AttributeError("{sval} does not match the accepted type schema for '{s}' : {st.accepter}".format(**locals()))

        # By now the kwds is filled up with values
        # the parent init will do the usual ROS message setup.
        super(msg_mod, self).__init__(*args, **kwds)

        # Note here no slot should be set to None.
        # Default values have been forcibly assigned when required.

    # duck punching into genpy generated message classes.
    # adding contract to verify arguments
    args_contract = "tuple(" +
    kwargs_contract = "dict("
    msg_mod.__init__ = contract(init_punch, args="tuple()", kwargs="")
    # msg_mod.__get__ = get_punch
    # msg_mod.__set__ = set_punch
    # msg_mod.__delete__ = delete_punch

    # Registering the list of optional field (required by pyros_schemas)
    msg_mod._opt_slots = opt_slot_list
