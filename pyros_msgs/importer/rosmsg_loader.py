from __future__ import absolute_import, division, print_function

import contextlib
import importlib
import site
import tempfile

from pyros_msgs.importer import rosmsg_generator

"""
A module to setup custom importer for .msg and .srv files
Upon import, it will first find the .msg file, then generate the python module for it, then load it.

TODO...
"""

# We need to be extra careful with python versions
# Ref : https://docs.python.org/dev/library/importlib.html#importlib.import_module

# Ref : http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
# Note : Couldn't find a way to make imp.load_source deal with packages or relative imports (necessary for our generated message classes)
import os
import sys

# This will take the ROS distro version if ros has been setup
import genpy.generator
import genpy.generate_initpy

import logging


def _mk_init_name(fullname):
    """Return the name of the __init__ module for a given package name."""
    if fullname.endswith('.__init__'):
        return fullname
    return fullname + '.__init__'


def _get_key_name(fullname, db):
    """Look in an open shelf for fullname or fullname.__init__, return the name found."""
    if fullname in db:
        return fullname
    init_name = _mk_init_name(fullname)
    if init_name in db:
        return init_name
    return None




if sys.version_info >= (3, 4):

    import importlib.abc
    import importlib.machinery

    # To do only once when starting up
    rosimport_path = os.path.join(tempfile.gettempdir(), 'rosimport')
    if os.path.exists(rosimport_path):
        os.removedirs(rosimport_path)
    os.makedirs(rosimport_path)

    class ROSMsgLoader(importlib.abc.SourceLoader):


        def __init__(self, fullname, path):

            self.logger = logging.getLogger(__name__)
            self.path = path

            self.msgsrv_files = [f for f in os.listdir(self.path) if f.endswith('.msg')]

            self.rospackage = fullname.partition('.')[0]

            self.outdir_pkg = tempfile.mkdtemp(prefix=self.rospackage, dir=rosimport_path)

            # TODO : we need to determine that from the loader
            self.includepath = []
            self.ns_pkg = False  # doesnt seem needed yet and is overall safer...

            gen = rosmsg_generator.genmsgsrv_py(
                msgsrv_files=self.msgsrv_files,
                package=self.rospackage,
                outdir_pkg=self.outdir_pkg,
                includepath=self.includepath,
                ns_pkg=self.ns_pkg
            )

        def get_data(self, path):
            """Returns the bytes from the source code (will be used to generate bytecode)"""
            self.get_filename()
            return None


        def get_source(self, fullname):
            self.logger.debug('loading source for "%s" from msg' % fullname)
            try:

                self._generate()

                # with shelve_context(self.path_entry) as db:
                #     key_name = _get_key_name(fullname, db)
                #     if key_name:
                #         return db[key_name]
                #     raise ImportError('could not find source for %s' % fullname)

                pass


            except Exception as e:
                self.logger.debug('could not load source:', e)
                raise ImportError(str(e))

        # defining this to benefit from backward compat import mechanism in python 3.X
        def get_filename(self, name):
            """
            Deterministic temporary filename.
            :param name:
            :return:
            """
            os.sep.join(name.split(".")) + '.' + self.ext

            # def _get_filename(self, fullname):
            #     # Make up a fake filename that starts with the path entry
            #     # so pkgutil.get_data() works correctly.
            #     return os.path.join(self.path_entry, fullname)
            #
            # # defining this to benefit from backward compat import mechanism in python 3.X
            # def is_package(self, name):
            #     names = name.split(".")
            #     parent_idx = len(names) -1
            #     # trying to find a parent already loaded
            #     while 0<= parent_idx < len(names) :
            #         if names[parent_idx] in sys.modules: # we found a parent, we can get his path and go back
            #             pass
            #         else:  # parent not found, need to check its parent
            #             parent_idx-=1
            #
            #
            #     else:  # No loaded parent found, lets attempt to import it directly (searching in all sys.paths)
            #
            #         pass
            #
            #
            #     return None  # TODO : implement check
            #
            # def load_module(self, fullname):
            #
            #     if fullname in sys.modules:
            #         self.logger.debug('reusing existing module from previous import of "%s"' % fullname)
            #         mod = sys.modules[fullname]
            #     else:
            #         self.logger.debug('creating a new module object for "%s"' % fullname)
            #         mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
            #
            #     # Set a few properties required by PEP 302
            #     mod.__file__ = self._get_filename(fullname)
            #     mod.__name__ = fullname
            #     mod.__path__ = self.path_entry
            #     mod.__loader__ = self
            #     mod.__package__ = '.'.join(fullname.split('.')[:-1])
            #
            #     if self.is_package(fullname):
            #         self.logger.debug('adding path for package')
            #         # Set __path__ for packages
            #         # so we can find the sub-modules.
            #         mod.__path__ = [self.path_entry]
            #     else:
            #         self.logger.debug('imported as regular module')
            #
            #     source = self.get_source(fullname)
            #
            #     self.logger.debug('execing source...')
            #     exec(source, mod.__dict__)
            #     self.logger.debug('done')
            #     return mod

    class ROSSrvLoader(importlib.abc.SourceLoader):

        def __init__(self, path_entry, msgsrv_files, package, outdir_pkg, includepath=None, ns_pkg=None):

            self.logger = logging.getLogger(__name__)
            self.path_entry = path_entry

            self.msgsrv_files = msgsrv_files
            self.package = package
            self.outdir_pkg = outdir_pkg

            # TODO : we need to determine that from the loader
            self.includepath = includepath
            self.ns_pkg = ns_pkg

        def _generate(self, fullname):

            gen = rosmsg_generator.genmsgsrv_py(
                msgsrv_files=self.msgsrv_files,
                package=self.package,
                outdir_pkg=self.outdir_pkg,
                includepath=self.includepath,
                ns_pkg=self.ns_pkg
            )
            return gen

        def get_source(self, fullname):
            self.logger.debug('loading source for "%s" from msg' % fullname)
            try:

                self._generate()

                # with shelve_context(self.path_entry) as db:
                #     key_name = _get_key_name(fullname, db)
                #     if key_name:
                #         return db[key_name]
                #     raise ImportError('could not find source for %s' % fullname)

                pass


            except Exception as e:
                self.logger.debug('could not load source:', e)
                raise ImportError(str(e))

        # defining this to benefit from backward compat import mechanism in python 3.X
        def get_filename(self, name):
            os.sep.join(name.split(".")) + '.' + self.ext



else:

    class ROSLoader(object):

        def __init__(self, path_entry, msgsrv_files, package, outdir_pkg, includepath=None, ns_pkg=None):

            self.logger = logging.getLogger(__name__)
            self.path_entry = path_entry

            self.msgsrv_files = msgsrv_files
            self.package = package
            self.outdir_pkg = outdir_pkg

            # TODO : we need to determine that from the loader
            self.includepath = includepath
            self.ns_pkg = ns_pkg

        def _generate(self, fullname):

            gen = rosmsg_generator.genmsgsrv_py(
                msgsrv_files=self.msgsrv_files,
                package=self.package,
                outdir_pkg=self.outdir_pkg,
                includepath=self.includepath,
                ns_pkg=self.ns_pkg
            )
            return gen

        def get_source(self, fullname):
            self.logger.debug('loading source for "%s" from msg' % fullname)
            try:

                self._generate()

                # with shelve_context(self.path_entry) as db:
                #     key_name = _get_key_name(fullname, db)
                #     if key_name:
                #         return db[key_name]
                #     raise ImportError('could not find source for %s' % fullname)

                pass


            except Exception as e:
                self.logger.debug('could not load source:', e)
                raise ImportError(str(e))

        # defining this to benefit from backward compat import mechanism in python 3.X
        def get_filename(self, name):
            os.sep.join(name.split(".")) + '.' + self.ext

            # def _get_filename(self, fullname):
            #     # Make up a fake filename that starts with the path entry
            #     # so pkgutil.get_data() works correctly.
            #     return os.path.join(self.path_entry, fullname)
            #
            # # defining this to benefit from backward compat import mechanism in python 3.X
            # def is_package(self, name):
            #     names = name.split(".")
            #     parent_idx = len(names) -1
            #     # trying to find a parent already loaded
            #     while 0<= parent_idx < len(names) :
            #         if names[parent_idx] in sys.modules: # we found a parent, we can get his path and go back
            #             pass
            #         else:  # parent not found, need to check its parent
            #             parent_idx-=1
            #
            #
            #     else:  # No loaded parent found, lets attempt to import it directly (searching in all sys.paths)
            #
            #         pass
            #
            #
            #     return None  # TODO : implement check
            #
            # def load_module(self, fullname):
            #
            #     if fullname in sys.modules:
            #         self.logger.debug('reusing existing module from previous import of "%s"' % fullname)
            #         mod = sys.modules[fullname]
            #     else:
            #         self.logger.debug('creating a new module object for "%s"' % fullname)
            #         mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
            #
            #     # Set a few properties required by PEP 302
            #     mod.__file__ = self._get_filename(fullname)
            #     mod.__name__ = fullname
            #     mod.__path__ = self.path_entry
            #     mod.__loader__ = self
            #     mod.__package__ = '.'.join(fullname.split('.')[:-1])
            #
            #     if self.is_package(fullname):
            #         self.logger.debug('adding path for package')
            #         # Set __path__ for packages
            #         # so we can find the sub-modules.
            #         mod.__path__ = [self.path_entry]
            #     else:
            #         self.logger.debug('imported as regular module')
            #
            #     source = self.get_source(fullname)
            #
            #     self.logger.debug('execing source...')
            #     exec(source, mod.__dict__)
            #     self.logger.debug('done')
            #     return mod
