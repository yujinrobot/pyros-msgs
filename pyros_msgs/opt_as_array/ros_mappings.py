from __future__ import absolute_import, division, print_function, unicode_literals


"""
This module defines ros mappings and  strategies for testing (covering ros use case only).
It can be read as a specification of the current package.
"""


import six

from pyros_msgs.typecheck import (
    six_long,
    Accepter, Sanitizer, Array, Any, MinMax, CodePoint,
    TypeChecker,
    typechecker_from_rosfield_type
)


def typechecker_from_rosfield_opttype(slot_type):
    """
    Retrieves an actual type tuple based on the ros type string
    :param slot_type: the ros type string
    :return: the corresponding typeschema
    Reference :
    >>> typechecker_from_rosfield_type('bool')
    (Sanitizer to <class 'bool'>, Accepter from <class 'bool'>)
    >>> typechecker_from_rosfield_type('bool[]')
    (Array of Sanitizer to <class 'bool'>, Array of Accepter from <class 'bool'>)

    >>> typechecker_from_rosfield_type('int64[]')
    (Array of Sanitizer to <class 'int'>, Array of MinMax [-9223372036854775808..9223372036854775807] of Any of {<class 'int'>, <class 'int'>})

    >>> typechecker_from_rosfield_type('string[]')
    (Array of Sanitizer to <class 'bytes'>, Array of Any of {CodePoint [0..127] of Accepter from <class 'str'>, Accepter from <class 'bytes'>})

    >>> typechecker_from_rosfield_type('time')  #doctest: +ELLIPSIS
    (Sanitizer to <function <lambda> at 0x...>, Accepter from {'secs': (Sanitizer to <class 'int'>, MinMax [0..4294967295] of Accepter from <class 'int'>), 'nsecs': (Sanitizer to <class 'int'>, MinMax [0..4294967295] of Accepter from <class 'int'>)})
    >>> typechecker_from_rosfield_type('duration[]')  #doctest: +ELLIPSIS
    (Array of Sanitizer to <function <lambda> at 0x...>, Array of Accepter from {'secs': (Sanitizer to <class 'int'>, MinMax [-2147483648..2147483647] of Accepter from <class 'int'>), 'nsecs': (Sanitizer to <class 'int'>, MinMax [-2147483648..2147483647] of Accepter from <class 'int'>)})
    """
    # we cannot avoid having this here since we can add '[]' to a custom message type
    if isinstance(slot_type, six.string_types) and slot_type.endswith('[]'):
        # we need to recurse...
        typechecker = typechecker_from_rosfield_type(slot_type[:-2])
        return TypeChecker(
            Array(typechecker.sanitizer),
            Any(
                Array(typechecker.accepter),  # value should be in array
                Accepter(None)  # value can be none since it is optional
            )
        )
    else:  # otherwise it doesnt match our special case : use base function
        return typechecker_from_rosfield_type(slot_type)




# TODO : common message types :
# - std_msgs/Header
# -


if __name__ == '__main__':  # run doctests
    import doctest
    from pyros_msgs.typecheck._utils import Py32DoctestChecker
    doctest.DocTestSuite(__name__, checker=Py32DoctestChecker())
