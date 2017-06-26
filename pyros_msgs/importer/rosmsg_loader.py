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

def _verbose_message(message, *args, **kwargs):
    """Print the message to stderr if -v/PYTHONVERBOSE is turned on."""
    verbosity = kwargs.pop('verbosity', 1)
    if sys.flags.verbose >= verbosity:
        if not message.startswith(('#', 'import ')):
            message = '# ' + message
        print(message.format(*args), file=sys.stderr)

if (2, 7) <= sys.version_info < (3, 4):  # valid until which py3 version ?

    import io
    import errno
    import imp

    try:
        ImportError('msg', name='name', path='path')
    except TypeError:
        class _ImportError(ImportError):
            def __init__(self, *args, **kwargs):
                self.name = kwargs.pop('name', None)
                self.path = kwargs.pop('path', None)
                super(_ImportError, self).__init__(*args, **kwargs)
    else:
        _ImportError = ImportError

    # Frame stripping magic ###############################################

    def _call_with_frames_removed(f, *args, **kwds):
        """remove_importlib_frames in import.c will always remove sequences
        of importlib frames that end with a call to this function

        Use it instead of a normal call in places where including the importlib
        frames introduces unwanted noise into the traceback (e.g. when executing
        module code)
        """
        return f(*args, **kwds)

    def decode_source(source_bytes):
        """Decode bytes representing source code and return the string.

        Universal newline support is used in the decoding.
        """
        import tokenize  # To avoid bootstrap issues.
        source_bytes_readline = io.BytesIO(source_bytes).readline
        encoding = tokenize.detect_encoding(source_bytes_readline)
        newline_decoder = io.IncrementalNewlineDecoder(None, True)
        return newline_decoder.decode(source_bytes.decode(encoding[0]))


    # inspired from importlib2
    class FileLoader2(object):
        """Base file loader class which implements the loader protocol methods that
        require file system usage. Also implements implicit namespace package PEP 420."""

        def __init__(self, fullname, path):
            """Cache the module name and the path to the file found by the
            finder."""
            self.name = fullname
            self.path = path

        def __eq__(self, other):
            return (self.__class__ == other.__class__ and
                    self.__dict__ == other.__dict__)

        def __hash__(self):
            return hash(self.name) ^ hash(self.path)

        def get_source(self, fullname):
            """Concrete implementation of InspectLoader.get_source."""
            path = self.get_filename(fullname)
            try:
                source_bytes = self.get_data(path)
            except OSError as exc:
                e = _ImportError('source not available through get_data()',
                                 name=fullname)
                e.__cause__ = exc
                raise e
            return source_bytes
            # return decode_source(source_bytes)

        def load_module(self, name):
            """Load a module from a file.
            """
            # Implementation inspired from pytest

            # If there is an existing module object named 'fullname' in
            # sys.modules, the loader must use that existing module. (Otherwise,
            # the reload() builtin will not work correctly.)
            if name in sys.modules:
                return sys.modules[name]

            source = self.get_source(name)
            # I wish I could just call imp.load_compiled here, but __file__ has to
            # be set properly. In Python 3.2+, this all would be handled correctly
            # by load_compiled.
            mod = sys.modules.setdefault(name, imp.new_module(name))
            try:
                # Set a few properties required by PEP 302
                mod.__file__ = self.get_filename(name)
                mod.__loader__ = self
                if self.is_package(name):
                    mod.__path__ = [self.path]
                    mod.__package__ = name  # PEP 366
                else:
                    mod.__path__ = self.path
                    mod.__package__ = '.'.join(name.split('.')[:-1])  # PEP 366

                exec source in mod.__dict__

            except:
                if name in sys.modules:
                    del sys.modules[name]
                raise
            return sys.modules[name]

        def get_filename(self, fullname):
            """Return the path to the source file."""
            if os.path.isdir(self.path) and os.path.isfile(os.path.join(self.path, '__init__.py')):
                return os.path.join(self.path, '__init__.py')  # python package
            else:
                return self.path  # module or namespace package case

        def is_package(self, fullname):
            # TODO : test this (without ROS loader)
            # in case of package we have to always have the directory as self.path
            # we can always compute init path dynamically when needed.
            return os.path.isdir(self.path)

        def get_data(self, path):
            """Return the data from path as raw bytes.
            Implements PEP 420 using pkg_resources
            """
            try:
                with io.FileIO(path, 'r') as file:
                    return file.read()
            except IOError as ioe:
                if ioe.errno == errno.EISDIR:
                    # implicit namespace package
                    return """import pkg_resources; pkg_resources.declare_namespace(__name__)"""
                else:
                    raise


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

    if (2, 7) <= sys.version_info < (3, 4):  # valid until which py3 version ?

        class ROSDefLoader(FileLoader2):

            def get_gen_path(self):
                """Returning the generated path matching the import"""
                return os.path.join(self.outdir_pkg, loader_generated_subdir)

            def __repr__(self):
                return "ROSDefLoader/{0}({1}, {2})".format(loader_file_extension, self.name, self.path)

            def __init__(self, fullname, path, implicit_ns_pkg=False):

                self.logger = logging.getLogger(__name__)

                self.implicit_ns_package = implicit_ns_pkg

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

            def is_package(self, fullname):
                return self.implicit_ns_package or super(ROSDefLoader, self).is_package(fullname=fullname)

            def get_source(self, fullname):
                """Concrete implementation of InspectLoader.get_source."""
                path = self.get_filename(fullname)
                try:
                    source_bytes = self.get_data(path)
                except OSError as exc:
                    e = _ImportError('source not available through get_data()',
                                     name=fullname)
                    e.__cause__ = exc
                    raise e
                return source_bytes
                # return decode_source(source_bytes)

            def source_to_code(self, data, path, _optimize=-1):
                """Return the code object compiled from source.

                The 'data' argument can be any object type that compile() supports.
                """
                # XXX Handle _optimize when possible?
                return _call_with_frames_removed(compile, data, path, 'exec',
                                                 dont_inherit=True)
            def get_code(self, fullname):
                source = self.get_source(fullname)
                print('compiling code for "%s"' % fullname)
                return compile(source, self._get_filename(fullname), 'exec', dont_inherit=True)

            def __repr__(self):
                return "ROSDefLoader/{0}({1}, {2})".format(loader_file_extension, self.name, self.path)

            def load_module(self, fullname):
                source = self.get_source(fullname)

                if fullname in sys.modules:
                    print('reusing existing module from previous import of "%s"' % fullname)
                    mod = sys.modules[fullname]
                else:
                    print('creating a new module object for "%s"' % fullname)
                    mod = sys.modules.setdefault(fullname, imp.new_module(fullname))

                # Set a few properties required by PEP 302 or PEP 420
                if self.implicit_ns_package:
                    mod.__path__ = [self.path]
                else:
                    mod.__file__ = self.get_filename(fullname)
                    mod.__path__ = self.path

                mod.__name__ = fullname
                mod.__loader__ = self
                mod.__package__ = '.'.join(fullname.split('.')[:-1])

                if self.is_package(fullname):
                    print('adding path for package')
                    # Set __path__ for packages
                    # so we can find the sub-modules.
                    mod.__path__ = [self.path]
                else:
                    print('imported as regular module')

                # Note : we want to avoid calling imp.load_module,
                # to eventually be able to implement this without generating temporary file
                print('execing source...')
                exec source in mod.__dict__
                print('done')
                return mod

    elif sys.version_info >= (3, 4):  # we do not support 3.2 and 3.3 (unsupported but might work ?)
        import importlib.machinery as importlib_machinery

        class ROSDefLoader(importlib_machinery.SourceFileLoader):
            def __init__(self, fullname, path, implicit_ns_pkg=False):

                self.logger = logging.getLogger(__name__)

                self.implicit_ns_package = implicit_ns_pkg

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

            def __repr__(self):
                return "ROSDefLoader/{0}({1}, {2})".format(loader_file_extension, self.name, self.path)

            def exec_module(self, module):
                # Custom implementation to declare an implicit namespace package
                if (2, 7) <= sys.version_info < (3, 4) and self.implicit_ns_package:
                    module.__path__ = [self.path]  # mandatory to trick importlib2 to think this is a package
                    import pkg_resources
                    pkg_resources.declare_namespace(module.__name__)
                else:
                    super(ROSDefLoader, self).exec_module(module)

    else:
        raise ImportError("ros_loader : Unsupported python version")

    return ROSDefLoader

ROSMsgLoader = RosLoader(rosdef_extension='.msg')
ROSSrvLoader = RosLoader(rosdef_extension='.srv')
