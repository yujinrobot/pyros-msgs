from __future__ import absolute_import, division, print_function
"""
Testing executing rosmsg_generator directly (like setup.py would)
"""

import os
import sys
import runpy
import logging.config

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
})

# Since test frameworks (like pytest) play with the import machinery, we cannot use it here...
import unittest

# Ref : http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path

import importlib

# Importing importer module
from pyros_msgs.importer import rosmsg_finder

# importlib
# https://pymotw.com/3/importlib/index.html
# https://pymotw.com/2/importlib/index.html

# if sys.version_info > (3, 4):
#     import importlib.util
#     # REF : https://docs.python.org/3.6/library/importlib.html#approximating-importlib-import-module
#     # Useful to display details when debugging...
#     def import_module(name, package=None):
#         """An approximate implementation of import."""
#         absolute_name = importlib.util.resolve_name(name, package)
#         try:
#             return sys.modules[absolute_name]
#         except KeyError:
#             pass
#
#         path = None
#         if '.' in absolute_name:
#             parent_name, _, child_name = absolute_name.rpartition('.')
#             parent_module = import_module(parent_name)
#             path = parent_module.spec.submodule_search_locations  # this currently breaks (probably because of pytest custom importer ? )
#         for finder in sys.meta_path:
#             spec = finder.find_spec(absolute_name, path)
#             if spec is not None:
#                 break
#         else:
#             raise ImportError('No module named {absolute_name!r}'.format(**locals()))
#         module = importlib.util.module_from_spec(spec)
#         spec.loader.exec_module(module)
#         sys.modules[absolute_name] = module
#         if path is not None:
#             setattr(parent_module, child_name, module)
#         return module


# if sys.version_info > (3, 4):
#     import importlib.util
#
#     # Adapted from : https://docs.python.org/3.6/library/importlib.html#approximating-importlib-import-module
#     # Useful to debug details...
#     def import_module(name, package=None):
#         # using find_spec to use our finder
#         spec = importlib.util.find_spec(name, package)
#
#         # path = None
#         # if '.' in absolute_name:
#         #     parent_name, _, child_name = absolute_name.rpartition('.')
#         #     # recursive import call
#         #     parent_module = import_module(parent_name)
#         #     # getting the path instead of relying on spec (not managed by pytest it seems...)
#         #     path = [os.path.join(p, child_name) for p in parent_module.__path__ if os.path.exists(os.path.join(p, child_name))]
#
#         # getting spec with importlib.util (instead of meta path finder to avoid uncompatible pytest finder)
#         #spec = importlib.util.spec_from_file_location(absolute_name, path[0])
#         parent_module = None
#         child_name = None
#         if spec is None:
#             # We didnt find anything, but this is expected on ros packages that haven't been generated yet
#             if '.' in name:
#                 parent_name, _, child_name = name.rpartition('.')
#                 # recursive import call
#                 parent_module = import_module(parent_name)
#                 # we can check if there is a module in there..
#                 path = [os.path.join(p, child_name)
#                         for p in parent_module.__path__._path
#                         if os.path.exists(os.path.join(p, child_name))]
#                 # we attempt to get the spec from the first found location
#                 while path and spec is None:
#                     spec = importlib.util.spec_from_file_location(name, path[0])
#                     path[:] = path[1:]
#             else:
#                 raise ImportError
#
#         # checking again in case spec has been modified
#         if spec is not None:
#             if spec.name not in sys.modules:
#                 module = importlib.util.module_from_spec(spec)
#                 spec.loader.exec_module(module)
#                 sys.modules[name] = module
#             if parent_module is not None and child_name is not None:
#                 setattr(parent_module, child_name, sys.modules[name])
#             return sys.modules[name]
#         else:
#             raise ImportError
# else:
#     def import_module(name, package=None):
#         return importlib.import_module(name=name, package=package)


#
# Note : we cannot assume anything about import implementation (different python version, different version of pytest)
# => we need to test them all...
#

# HACK to fix spec from pytest
# @property
# def spec():
#     importlib.util.spec_from_file_location(__file__)


def print_importers():
    import sys
    import pprint

    print('PATH:'),
    pprint.pprint(sys.path)
    print()
    print('IMPORTERS:')
    for name, cache_value in sys.path_importer_cache.items():
        name = name.replace(sys.prefix, '...')
        print('%s: %r' % (name, cache_value))


class TestImportLibAnotherMsg(unittest.TestCase):
    rosdeps_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'rosdeps')

    @classmethod
    def setUpClass(cls):
        # We need to be before FileFinder to be able to find our '.msg' and '.srv' files without making a namespace package
        supported_loaders = rosmsg_finder._get_supported_ros_loaders()
        ros_hook = rosmsg_finder.DirectoryFinder.path_hook(*supported_loaders)
        sys.path_hooks.insert(1, ros_hook)

        sys.path.append(cls.rosdeps_path)

    @classmethod
    def tearDownClass(cls):
        # CAREFUL : Even though we remove the path from sys.path,
        # initialized finders will remain in sys.path_importer_cache
        sys.path.remove(cls.rosdeps_path)

    @unittest.skipIf(not hasattr(importlib, '__import__'), reason="importlib does not have attribute __import__")
    def test_importlib_import_absolute_msg(self):
        # Verify that files exists and are importable
        std_msgs = importlib.__import__('std_msgs.msg')
        std_msgs = std_msgs.msg

        self.assertTrue(std_msgs is not None)
        self.assertTrue(std_msgs.Bool is not None)
        self.assertTrue(callable(std_msgs.Bool))
        self.assertTrue(std_msgs.Bool._type == 'std_msgs/Bool')

        # use it !
        self.assertTrue(std_msgs.Bool(True))

    @unittest.skipIf(not hasattr(importlib, '__import__'), reason="importlib does not have attribute __import__")
    def test_importlib_import_absolute_class_raises(self):
        with self.assertRaises(ImportError):
            importlib.__import__('std_msgs.msg.Bool')

    # BROKEN 3.4
    # @unittest.skipIf(not hasattr(importlib, '__import__'), reason="importlib does not have attribute __import__")
    # def test_importlib_import_relative_pkg(self):
    #     # Verify that files exists and are importable
    #     test_msgs = importlib.__import__('.msg')
    #
    #     self.assertTrue(test_msgs is not None)
    #     self.assertTrue(test_msgs.TestMsg is not None)
    #     self.assertTrue(callable(test_msgs.TestMsg))
    #     self.assertTrue(test_msgs.TestMsg._type == 'pyros_msgs/TestMsg')  # careful between ros package name and python package name
    #
    #     # use it !
    #     self.assertTrue(test_msgs.TestMsg(test_bool=True, test_string='Test').test_bool)

    # BROKEN 3.4
    # @unittest.skipIf(not hasattr(importlib, '__import__'), reason="importlib does not have attribute __import__")
    # def test_importlib_import_relative_mod(self):
    #     # Verify that files exists and are importable
    #     msg = importlib.__import__('.msg.TestMsg')
    #     TestMsg = msg.TestMsg
    #
    #     self.assertTrue(TestMsg is not None)
    #     self.assertTrue(callable(TestMsg))
    #     self.assertTrue(TestMsg._type == 'pyros_msgs/TestMsg')  # careful between ros package name and python package name
    #
    #     # use it !
    #     self.assertTrue(TestMsg(test_bool=True, test_string='Test').test_bool)

    @unittest.skipIf(not hasattr(importlib, 'find_loader') or not hasattr(importlib, 'load_module'),
                     reason="importlib does not have attribute find_loader or load_module")
    def test_importlib_loadmodule_absolute_msg(self):
        # Verify that files exists and are dynamically importable
        pkg_list = 'std_msgs.msg'.split('.')[:-1]
        mod_list = 'std_msgs.msg'.split('.')[1:]
        pkg = None
        for pkg_name, mod_name in zip(pkg_list, mod_list):
            pkg_loader = importlib.find_loader(pkg_name, pkg.__path__ if pkg else None)
            pkg = pkg_loader.load_module(mod_name)

        std_msgs = pkg

        self.assertTrue(std_msgs is not None)
        self.assertTrue(std_msgs.Bool is not None)
        self.assertTrue(callable(std_msgs.Bool))
        self.assertTrue(std_msgs.Bool._type == 'std_msgs/Bool')

        # use it !
        self.assertTrue(std_msgs.Bool(True))

        # TODO : implement some differences and check we get them...
        if hasattr(importlib, 'reload'):  # recent version of importlib
            # attempting to reload
            importlib.reload(std_msgs)
        else:
            pass

    @unittest.skipIf(not hasattr(importlib, 'find_loader') or not hasattr(importlib, 'load_module'),
                     reason="importlib does not have attribute find_loader or load_module")
    def test_importlib_loadmodule_absolute_class(self):
        # Verify that files exists and are dynamically importable
        pkg_list = 'std_msgs.msg.Bool'.split('.')[:-1]
        mod_list = 'std_msgs.msg.Bool'.split('.')[1:]
        pkg = None
        for pkg_name, mod_name in zip(pkg_list, mod_list):
            pkg_loader = importlib.find_loader(pkg_name, pkg.__path__ if pkg else None)
            pkg = pkg_loader.load_module(mod_name)

        Bool = pkg

        self.assertTrue(Bool is not None)
        self.assertTrue(callable(Bool))
        self.assertTrue(Bool._type == 'std_msgs/Bool')

        # use it !
        self.assertTrue(Bool(True))

        # TODO : implement some differences and check we get them...
        if hasattr(importlib, 'reload'):  # recent version of importlib
            # attempting to reload
            importlib.reload(Bool)
        else:
            pass

    @unittest.skipIf(not hasattr(importlib, 'find_loader') or not hasattr(importlib, 'load_module'),
                     reason="importlib does not have attribute find_loader or load_module")
    def test_importlib_loadmodule_relative_msg(self):
        # Verify that files exists and are dynamically importable
        pkg_list = '.msg'.split('.')[:-1]
        mod_list = '.msg'.split('.')[1:]
        pkg = None
        for pkg_name, mod_name in zip(pkg_list, mod_list):
            pkg_loader = importlib.find_loader(pkg_name, pkg.__path__ if pkg else None)
            pkg = pkg_loader.load_module(mod_name)

        test_msgs = pkg

        self.assertTrue(test_msgs is not None)
        self.assertTrue(test_msgs.TestMsg is not None)
        self.assertTrue(callable(test_msgs.TestMsg))
        self.assertTrue(test_msgs.TestMsg._type == 'pyros_msgs/TestMsg')  # careful between ros package name and python package name

        # use it !
        self.assertTrue(test_msgs.TestMsg(test_bool=True, test_string='Test').test_bool)

        # TODO : implement some differences and check we get them...
        if hasattr(importlib, 'reload'):  # recent version of importlib
            # attempting to reload
            importlib.reload(test_msgs)
        else:
            pass

    @unittest.skipIf(not hasattr(importlib, 'find_loader') or not hasattr(importlib, 'load_module'),
                     reason="importlib does not have attribute find_loader or load_module")
    def test_importlib_loadmodule_relative_class(self):
        # Verify that files exists and are dynamically importable
        pkg_list = '.msg.TestMsg'.split('.')[:-1]
        mod_list = '.msg.TestMsg'.split('.')[1:]
        pkg = None
        for pkg_name, mod_name in zip(pkg_list, mod_list):
            pkg_loader = importlib.find_loader(pkg_name, pkg.__path__ if pkg else None)
            pkg = pkg_loader.load_module(mod_name)

        TestMsg = pkg

        self.assertTrue(TestMsg is not None)
        self.assertTrue(callable(TestMsg))
        self.assertTrue(TestMsg._type == 'pyros_msgs/TestMsg')

        # use it !
        self.assertTrue(TestMsg(test_bool=True, test_string='Test').test_bool)

        # TODO : implement some differences and check we get them...
        if hasattr(importlib, 'reload'):  # recent version of importlib
            # attempting to reload
            importlib.reload(TestMsg)
        else:
            pass

    # TODO : dynamic using module_spec (python 3.5)

    @unittest.skipIf(not hasattr(importlib, 'import_module'), reason="importlib does not have attribute import_module")
    def test_importlib_importmodule_absolute_msg(self):
        # Verify that files exists and are dynamically importable
        std_msgs = importlib.import_module('std_msgs.msg')

        self.assertTrue(std_msgs is not None)
        self.assertTrue(std_msgs.Bool is not None)
        self.assertTrue(callable(std_msgs.Bool))
        self.assertTrue(std_msgs.Bool._type == 'std_msgs/Bool')

        # use it !
        self.assertTrue(std_msgs.Bool(True))

        if hasattr(importlib, 'reload'):  # recent version of importlib
            # attempting to reload
            importlib.reload(std_msgs)
        else:
            pass

        assert std_msgs is not None

    @unittest.skipIf(not hasattr(importlib, 'import_module'),
                     reason="importlib does not have attribute import_module")
    def test_importlib_importmodule_absolute_class_raises(self):
        with self.assertRaises(ImportError):
            importlib.import_module('std_msgs.msg.Bool')

    @unittest.skipIf(not hasattr(importlib, 'import_module'), reason="importlib does not have attribute import_module")
    def test_importlib_importmodule_relative_msg(self):
        # Verify that files exists and are dynamically importable
        test_msgs = importlib.import_module('.msg', package=__package__)

        self.assertTrue(test_msgs is not None)
        self.assertTrue(test_msgs.TestMsg is not None)
        self.assertTrue(callable(test_msgs.TestMsg))
        self.assertTrue(test_msgs.TestMsg._type == 'pyros_msgs/TestMsg')  # careful between ros package name and python package name

        # use it !
        self.assertTrue(test_msgs.TestMsg(test_bool=True, test_string='Test').test_bool)

        if hasattr(importlib, 'reload'):  # recent version of importlib
            # attempting to reload
            importlib.reload(test_msgs)
        else:
            pass

        assert test_msgs is not None

    @unittest.skipIf(not hasattr(importlib, 'import_module'),
                     reason="importlib does not have attribute import_module")
    def test_importlib_importmodule_relative_class_raises(self):
        with self.assertRaises(ImportError):
            importlib.import_module('.msg.TestMsg', package=__package__)

    # TODO
    # def test_double_import_uses_cache(self):  #
    #     print_importers()
    #     # Verify that files exists and are importable
    #     import std_msgs.msg as std_msgs
    #
    #     self.assertTrue(std_msgs.Bool is not None)
    #     self.assertTrue(callable(std_msgs.Bool))
    #     self.assertTrue(std_msgs.Bool._type == 'std_msgs/Bool')
    #
    #     import std_msgs.msg as std_msgs2
    #
    #     self.assertTrue(std_msgs == std_msgs2)




def test_importlib_srv_module():
    pass
    # TODO
    # # Verify that files exists and are importable
    # msg_mod = importlib.import_module('test_gen_msgs.srv.TestSrv')


if __name__ == '__main__':
    import pytest
    pytest.main(['-s', '-x', __file__, '--boxed'])
