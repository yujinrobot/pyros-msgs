from __future__ import absolute_import, division, print_function

import contextlib
import importlib
import site
import tempfile

import shutil

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

    def RosLoader(rosdef_extension):
        """
        Function generating ROS loaders.
        This is used to keep .msg and .srv loaders very similar
        """
        if rosdef_extension == '.msg':
            loader_origin_subdir = 'msg'
            loader_file_extension = rosdef_extension
            loader_generated_subdir = 'msg'
        elif rosdef_extension == '.srv':
            loader_origin_subdir = 'srv'
            loader_file_extension = rosdef_extension
            loader_generated_subdir = 'srv'
        else:
            raise RuntimeError("RosLoader for a format {0} other than .msg or .srv is not supported".format(rosdef_extension))

        class ROSDefLoader(importlib.machinery.SourceFileLoader):
            def __init__(self, fullname, path):

                self.logger = logging.getLogger(__name__)

                # Doing this in each loader, in case we are running from different processes,
                # avoiding to reload from same file (especially useful for boxed tests).
                # But deterministic path to avoid regenerating from the same interpreter
                self.rosimport_path = os.path.join(tempfile.gettempdir(), 'rosimport', str(os.getpid()))
                if os.path.exists(self.rosimport_path):
                    shutil.rmtree(self.rosimport_path)
                os.makedirs(self.rosimport_path)

                self.rospackage = fullname.partition('.')[0]
                # We should reproduce package structure in generated file structure
                dirlist = path.split(os.sep)
                pkgidx = dirlist[::-1].index(self.rospackage)
                indirlist = [p for p in dirlist[:len(dirlist)-pkgidx-1:-1] if p != loader_origin_subdir and not p.endswith(loader_file_extension)]
                self.outdir_pkg = os.path.join(self.rosimport_path, self.rospackage, *indirlist[::-1])

                # : hack to be able to import a generated class (if requested)
                # self.requested_class = None

                if os.path.isdir(path):
                    if path.endswith(loader_origin_subdir) and any([f.endswith(loader_file_extension) for f in os.listdir(path)]):  # if we get a non empty 'msg' folder
                        init_path = os.path.join(self.outdir_pkg, loader_generated_subdir, '__init__.py')
                        if not os.path.exists(init_path):
                            # TODO : we need to determine that from the loader
                            # as a minimum we need to add current package
                            self.includepath = [self.rospackage + ':' + path]

                            # TODO : unify this after reviewing rosmsg_generator API
                            if loader_file_extension == '.msg':
                                # TODO : dynamic in memory generation (we do not need the file ultimately...)
                                self.gen_msgs = rosmsg_generator.genmsg_py(
                                    msg_files=[os.path.join(path, f) for f in os.listdir(path)],  # every file not ending in '.msg' will be ignored
                                    package=self.rospackage,
                                    outdir_pkg=self.outdir_pkg,
                                    includepath=self.includepath,
                                    initpy=True  # we always create an __init__.py when called from here.
                                )
                                init_path = None
                                for pyf in self.gen_msgs:
                                    if pyf.endswith('__init__.py'):
                                        init_path = pyf
                            elif loader_file_extension == '.srv':
                                # TODO : dynamic in memory generation (we do not need the file ultimately...)
                                self.gen_msgs = rosmsg_generator.gensrv_py(
                                    srv_files=[os.path.join(path, f) for f in os.listdir(path)],
                                    # every file not ending in '.msg' will be ignored
                                    package=self.rospackage,
                                    outdir_pkg=self.outdir_pkg,
                                    includepath=self.includepath,
                                    initpy=True  # we always create an __init__.py when called from here.
                                )
                                init_path = None
                                for pyf in self.gen_msgs:
                                    if pyf.endswith('__init__.py'):
                                        init_path = pyf
                            else:
                                raise RuntimeError(
                                    "RosDefLoader for a format {0} other than .msg or .srv is not supported".format(
                                        rosdef_extension))

                        if not init_path:
                            raise ImportError("__init__.py file not found".format(init_path))
                        if not os.path.exists(init_path):
                            raise ImportError("{0} file not found".format(init_path))

                        # relying on usual source file loader since we have generated normal python code
                        super(ROSDefLoader, self).__init__(fullname, init_path)
                    else:  # it is a directory potentially containing an 'msg'
                        # If we are here, it means it wasn't loaded before
                        # We need to be able to load from source
                        super(ROSDefLoader, self).__init__(fullname, path)

                        # or to load from installed ros package (python already generated, no point to generate again)
                        # Note : the path being in sys.path or not is a matter of ROS setup or metafinder.
                        # TODO

                elif os.path.isfile(path):
                    # The file should have already been generated (by the loader for a msg package)
                    # Note we do not want to rely on namespace packages here, since they are not standardized for python2,
                    # and they can prevent some useful usecases.

                    # Hack to be able to "import generated classes"
                    modname = fullname.rpartition('.')[2]
                    filepath = os.path.join(self.outdir_pkg, loader_generated_subdir, '_' + modname + '.py')  # the generated module
                    # relying on usual source file loader since we have previously generated normal python code
                    super(ROSDefLoader, self).__init__(fullname, filepath)

            def get_gen_path(self):
                """Returning the generated path matching the import"""
                return os.path.join(self.outdir_pkg, loader_generated_subdir)

        return ROSDefLoader

    ROSMsgLoader = RosLoader(rosdef_extension='.msg')
    ROSSrvLoader = RosLoader(rosdef_extension='.srv')

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
