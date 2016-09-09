from __future__ import absolute_import
from __future__ import print_function

import sys

import marshmallow
import functools

"""
Defining decorators to help with Schema generation for ROS message type <-> pyros dict conversion

"""


# defining a decorate to wrap classes.
# We are doing this because we want to add methods to a class via decorators
def wraps_cls(original_cls):
    def wrapper(wrapper_cls):
        """
        Update wrapper_cls to look like original_cls.
        If this docstring endsup in your decorated class, you should define the __doc__ when declaring that class.
        Like:

        @wraps_cls(cls)
        class Wrapper(cls):
            __doc__ = cls.__doc__
            pass

        Ref : http://bugs.python.org/issue12773
        """
        for attr in functools.WRAPPER_ASSIGNMENTS:
            try:
                value = getattr(original_cls, attr)
            except AttributeError:
                pass
            else:
                try:  # this fails on __doc__ with python 2.7
                    setattr(wrapper_cls, attr, value)
                except AttributeError:
                    if sys.version_info < (3, 2) and attr == '__doc__':  # skipping if doc is not writeable.
                        pass
                    else:
                        raise
        return wrapper_cls
    return wrapper
#
# From: http://stackoverflow.com/questions/28622235/functools-wraps-equivalent-for-class-decorator
#
# Usage:
#
# def some_class_decorator(cls_to_decorate):
#     @wraps_cls(cls_to_decorate)
#     class Wrapper(cls_to_decorate):
#         """Some Wrapper not important doc."""
#         pass
#     return Wrapper
#
#
# @some_class_decorator
# class MainClass:
#     """MainClass important doc."""
#     pass
#
#
# help(MainClass)
#
#


def with_field_validation(field, ros_type):
    """
    Decorator to add schema validation for a Ros Type toa  Schema class
    :param field: the name of the field to validate
    :param ros_type: the ros_type to validate
    :return:
    """
    def class_field_validation_decorator(cls):
        assert isinstance(cls, marshmallow.schema.SchemaMeta)

        @wraps_cls(cls)
        class Wrapper(cls):
            # TODO : closure
            # TODO : proxy ?
            # This wrapper inherits. Maybe a proxy would be better ?
            # We cannot have a doc here, becaus e it is not writeable in python 2.7
            # instead we reuse the one from the wrapped class
            __doc__ = cls.__doc__
            @marshmallow.validates(field)
            def _validate_ros_int_type(self, data, pass_original=True):
                # introspect data
                if not isinstance(data[field], ros_type):
                    raise marshmallow.ValidationError('data[{0}] should be {1}'.format(field, ros_type))

        return Wrapper
    return class_field_validation_decorator


def with_schema_validation(ros_type):
    """
    Decorator to add schema validation for a Ros Type
    :param ros_type: the ros_type to validate
    :return:

    TODO  : doctest
    """
    def _schema_validation_wrapper(f):
        @marshmallow.validates_schema
        def _validate_ros_int_type(self, data, pass_original=True):
            # introspect data
            if not isinstance(data, ros_type):
                raise marshmallow.ValidationError('data should be {0}'.format(ros_type))

        return _validate_ros_int_type
    return _schema_validation_wrapper


def with_factorymethod_on_deserialize(ros_type):
    """
    Decorator to add a factory method for a Ros Type to a schema
    Allos creating a Ros message type on deserialization (load)
    :param ros_type: the ros_type to create
    :return:
    """
    def _factorymethod_wrapper(f):
        @marshmallow.post_load
        def _make_ros_type(self, data):
            data = ros_type(data)
            return data
        return _make_ros_type
    return _factorymethod_wrapper
