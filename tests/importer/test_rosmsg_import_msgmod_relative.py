from __future__ import absolute_import, division, print_function
"""
Testing executing rosmsg_import outside of the package, otherwise the package is already imported.
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


class TestImportRelativeMsgModule(unittest.TestCase):
    """Testing custom ROS importer with path already existing and into sys.path"""

    @classmethod
    def setUpClass(cls):
        # We need to be before FileFinder to be able to find our (non .py[c]) files
        # inside, maybe already imported, python packages...
        sys.path_hooks.insert(1, rosmsg_finder.ROSFileFinder)
        # we do not need to append any path (since we rely on paths already present, and package already found)

    @classmethod
    def tearDownClass(cls):
        # CAREFUL : Even though we remove the path from sys.path,
        # initialized finders will remain in sys.path_importer_cache
        sys.path_hooks.remove(rosmsg_finder.ROSFileFinder)

    def test_import_absolute_module(self):
        print_importers()
        # Verify that files exists and are importable
        import pyros_msgs.importer.tests.msg.TestMsg as msg_mod

        self.assertTrue(msg_mod is not None)

    @unittest.skipIf(not hasattr(importlib, '__import__'), reason="importlib does not have attribute __import__")
    def test_importlib_import_absolute(self):
        # Verify that files exists and are importable
        msg_mod = importlib.__import__('pyros_msgs.importer.tests.msg.TestMsg',)

        self.assertTrue(msg_mod is not None)

    @unittest.skipIf(not hasattr(importlib, 'find_loader') or not hasattr(importlib, 'load_module'), reason="importlib does not have attribute find_loader or load_module")
    def test_importlib_loadmodule_absolute(self):
        # Verify that files exists and are dynamically importable
        pkg_list = 'pyros_msgs.importer.tests.msg.TestMsg'.split('.')[:-1]
        mod_list = 'pyros_msgs.importer.tests.msg.TestMsg'.split('.')[1:]
        pkg = None
        for pkg_name, mod_name in zip(pkg_list, mod_list):
            pkg_loader = importlib.find_loader(pkg_name, pkg.__path__ if pkg else None)
            pkg = pkg_loader.load_module(mod_name)

        msg_mod = pkg

        if hasattr(importlib, 'reload'):  # recent version of importlib
            # attempting to reload
            importlib.reload(msg_mod)
        else:
            pass

    # TODO : dynamic using specs (python 3.5)

    @unittest.skipIf(not hasattr(importlib, 'import_module'), reason="importlib does not have attribute import_module")
    def test_importlib_importmodule_absolute(self):
        # Verify that files exists and are dynamically importable
        msg_mod = importlib.import_module('pyros_msgs.importer.tests.msg.TestMsg')

        self.assertTrue(msg_mod is not None)

        if hasattr(importlib, 'reload'):  # recent version of importlib
            # attempting to reload
            importlib.reload(msg_mod)
        else:
            pass

        self.assertTrue(msg_mod is not None)


# def test_importlib_msg_module_relative():
#     # Verify that files exists and are importable
#     # TODO
#     # if hasattr(importlib, 'find_loader'):  # recent version of import lib
#     #
#     #     pkg_loader = importlib.find_loader('test_gen_msgs')
#     #     pkg = pkg_loader.load_module()
#     #
#     #     subpkg_loader = importlib.find_loader('msg', pkg.__path__)
#     #     subpkg = subpkg_loader.load_module()
#     #
#     #     loader = importlib.find_loader('TestMsg', subpkg.__path__)
#     #     m = subpkg_loader.load_module()
#     #
#     # else:  # old version
#     msg_mod = importlib.import_module('.msg.TestMsg', package=__package__)




def test_importlib_srv_module():
    pass
    # TODO
    # # Verify that files exists and are importable
    # msg_mod = importlib.import_module('test_gen_msgs.srv.TestSrv')


# imp https://pymotw.com/2/imp/index.html
# TODO

# def test_imp_msg_module():
#     # Verify that files exists and are importable
#     msg_mod = imp.import_module('test_gen_msgs.msg.TestMsg')
#
#
# def test_imp_msg_pkg():
#     # Verify that files exists and are importable
#     msg_mod = imp.import_module('test_gen_msgs.msg')
#
#
# def test_imp_srv_module():
#     # Verify that files exists and are importable
#     msg_mod = imp.import_module('test_gen_msgs.srv.TestSrv')
#
#
# def test_imp_srv_pkg():
#     # Verify that files exists and are importable
#     msg_mod = imp.import_module('test_gen_msgs.srv')


if __name__ == '__main__':
    unittest.main()
    #import nose
    #nose.main()
