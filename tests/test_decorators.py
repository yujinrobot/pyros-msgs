from __future__ import absolute_import
from __future__ import print_function

import collections

import marshmallow
import nose

# "private" decorators
from pyros_msgs import wraps_cls

# public decorators
from pyros_msgs import with_field_validation, with_schema_validation, with_factorymethod_on_deserialize

#


class WrappedCheck(object):
    """ test doc value """
    pass


@wraps_cls(WrappedCheck)
class WrappedCheck(WrappedCheck):
    __doc__ = WrappedCheck.__doc__  # to work with python 2.7 check http://bugs.python.org/issue12773
    # TODO : dynamically define this using functools assignments

    @classmethod
    def get_module(cls):
        return cls.__module__

    @classmethod
    def get_name(cls):
        return cls.__name__

    @classmethod
    def get_doc(cls):
        return cls.__doc__


def test_wrap_cls():
    # TODO : dynamically define this using functools assignments
    # TODO : check these may be trivial... but better be safe
    assert WrappedCheck.__module__ == WrappedCheck.get_module()
    assert WrappedCheck.__doc__ == WrappedCheck.get_doc()
    assert WrappedCheck.__name__ == WrappedCheck.get_name()

    assert WrappedCheck.__module__ == __name__
    assert WrappedCheck.__doc__ == """ test doc value """
    assert WrappedCheck.__name__ == "WrappedCheck"

#


Original = collections.namedtuple("Original", "answer")

@with_field_validation('answer', int)
class SchemaWithFieldValidation(marshmallow.Schema):
    """ doc test """
    answer = marshmallow.fields.Integer()


def test_with_field_validation():

    assert SchemaWithFieldValidation.__module__ == __name__
    assert SchemaWithFieldValidation.__doc__ == """ doc test """
    assert SchemaWithFieldValidation.__name__ == "SchemaWithFieldValidation"

    orignal_ok = Original(answer=42)
    orignal_invalid = Original(answer='fortytwo')
    schema = SchemaWithFieldValidation()

    marshalled = schema.dump(orignal_ok)

    assert len(marshalled.errors) == 0
    assert marshalled.data == {'answer': 42}

    #with nose.assert_raises( ):
    #schema.dump(orignal_invalid)


@with_schema_validation({'answer': 42})
class SchemaWithSchemaValidation(marshmallow.Schema):
    """ doc test """
    answer = marshmallow.fields.Integer()


class AnswerType(object):
    def __init__(self, dict):
        self.answer = dict['answer']

@with_factorymethod_on_deserialize( AnswerType )
class SchemaWithSchemaValidation(marshmallow.Schema):
    """ doc test """
    answer = marshmallow.fields.Integer()




def test_with_schema_validation():
    pass

def test_with_factorymethod_on_deserialize():
    pass


# Just in case we run this directly
if __name__ == '__main__':
    nose.runmodule(__name__)