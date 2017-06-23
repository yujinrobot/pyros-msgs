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

# We extend importlib machinery to interpret some specific directoty with specific content as a module
# This needs to match the logic in setup.py
if (2, 7) <= sys.version_info < (3, 4):
    from .importlib2 import machinery as importlib_machinery
    from .importlib2 import util as importlib_util

    # Module-level locking ########################################################

    # A dict mapping module names to weakrefs of _ModuleLock instances
    _module_locks = {}
    # A dict mapping thread ids to _ModuleLock instances
    _blocking_on = {}

    # The following two functions are for consumption by Python/import.c.

    # def _get_module_lock(name):
    #     """Get or create the module lock for a given module name.
    #
    #     Should only be called with the import lock taken."""
    #     lock = None
    #     try:
    #         lock = _module_locks[name]()
    #     except KeyError:
    #         pass
    #     if lock is None:
    #         if _thread is None:
    #             lock = _DummyModuleLock(name)
    #         else:
    #             lock = _ModuleLock(name)
    #
    #         def cb(_):
    #             del _module_locks[name]
    #
    #         _module_locks[name] = _weakref.ref(lock, cb)
    #     return lock


    # def _lock_unlock_module(name):
    #     """Release the global import lock, and acquires then release the
    #     module lock for a given module name.
    #     This is used to ensure a module is completely initialized, in the
    #     event it is being imported by another thread.
    #
    #     Should only be called with the import lock taken."""
    #     lock = _get_module_lock(name)
    #     _imp.release_lock()
    #     try:
    #         lock.acquire()
    #     except _DeadlockError:
    #         # Concurrent circular import, we'll accept a partially initialized
    #         # module object.
    #         pass
    #     else:
    #         lock.release()

    # class _ModuleLockManager(object):
    #
    #     def __init__(self, name):
    #         self._name = name
    #         self._lock = None
    #
    #     def __enter__(self):
    #         try:
    #             self._lock = _get_module_lock(self._name)
    #         finally:
    #             _imp.release_lock()
    #         self._lock.acquire()
    #
    #     def __exit__(self, *args, **kwargs):
    #         self._lock.release()

    class _SpecMethods(object):

        """Convenience wrapper around spec objects to provide spec-specific
        methods."""

        # The various spec_from_* functions could be made factory methods here.

        def __init__(self, spec):
            self.spec = spec

        def module_repr(self):
            """Return the repr to use for the module."""
            # We mostly replicate _module_repr() using the spec attributes.
            spec = self.spec
            name = '?' if spec.name is None else spec.name
            if spec.origin is None:
                if spec.loader is None:
                    return '<module {!r}>'.format(name)
                else:
                    return '<module {!r} ({!r})>'.format(name, spec.loader)
            else:
                if spec.has_location:
                    return '<module {!r} from {!r}>'.format(name, spec.origin)
                else:
                    return '<module {!r} ({})>'.format(spec.name, spec.origin)

        def init_module_attrs(self, module, _override=False, _force_name=True):
            """Set the module's attributes.

            All missing import-related module attributes will be set.  Here
            is how the spec attributes map onto the module:

            spec.name -> module.__name__
            spec.loader -> module.__loader__
            spec.parent -> module.__package__
            spec -> module.__spec__

            Optional:
            spec.origin -> module.__file__ (if spec.set_fileattr is true)
            spec.cached -> module.__cached__ (if __file__ also set)
            spec.submodule_search_locations -> module.__path__ (if set)

            """
            spec = self.spec

            # The passed in module may be not support attribute assignment,
            # in which case we simply don't set the attributes.

            # __name__
            if (_override or _force_name or
                        getattr(module, '__name__', None) is None):
                try:
                    module.__name__ = spec.name
                except AttributeError:
                    pass

            # __loader__
            if _override or getattr(module, '__loader__', None) is None:
                loader = spec.loader
                if loader is None:
                    # A backward compatibility hack.
                    if spec.submodule_search_locations is not None:
                        loader = _NamespaceLoader.__new__(_NamespaceLoader)
                        loader._path = spec.submodule_search_locations
                try:
                    module.__loader__ = loader
                except AttributeError:
                    pass

            # __package__
            if _override or getattr(module, '__package__', None) is None:
                try:
                    module.__package__ = spec.parent
                except AttributeError:
                    pass

            # __spec__
            try:
                module.__spec__ = spec
            except AttributeError:
                pass

            # __path__
            if _override or getattr(module, '__path__', None) is None:
                if spec.submodule_search_locations is not None:
                    try:
                        module.__path__ = spec.submodule_search_locations
                    except AttributeError:
                        pass

            if spec.has_location:
                # __file__
                if _override or getattr(module, '__file__', None) is None:
                    try:
                        module.__file__ = spec.origin
                    except AttributeError:
                        pass

                # __cached__
                if _override or getattr(module, '__cached__', None) is None:
                    if spec.cached is not None:
                        try:
                            module.__cached__ = spec.cached
                        except AttributeError:
                            pass

        def create(self):
            """Return a new module to be loaded.

            The import-related module attributes are also set with the
            appropriate values from the spec.

            """
            spec = self.spec
            # Typically loaders will not implement create_module().
            if hasattr(spec.loader, 'create_module'):
                # If create_module() returns `None` it means the default
                # module creation should be used.
                module = spec.loader.create_module(spec)
            else:
                module = None
            if module is None:
                # This must be done before open() is ever called as the 'io'
                # module implicitly imports 'locale' and would otherwise
                # trigger an infinite loop.
                module = _new_module(spec.name)
            self.init_module_attrs(module)
            return module

        def _exec(self, module):
            """Do everything necessary to execute the module.

            The namespace of `module` is used as the target of execution.
            This method uses the loader's `exec_module()` method.

            """
            self.spec.loader.exec_module(module)

        # Used by importlib.reload() and _load_module_shim().
        def exec_(self, module):
            """Execute the spec in an existing module's namespace."""
            name = self.spec.name
            _imp.acquire_lock()
            with _ModuleLockManager(name):
                if sys.modules.get(name) is not module:
                    msg = 'module {!r} not in sys.modules'.format(name)
                    raise _ImportError(msg, name=name)
                if self.spec.loader is None:
                    if self.spec.submodule_search_locations is None:
                        raise _ImportError('missing loader', name=self.spec.name)
                    # namespace package
                    self.init_module_attrs(module, _override=True)
                    return module
                self.init_module_attrs(module, _override=True)
                if not hasattr(self.spec.loader, 'exec_module'):
                    # (issue19713) Once BuiltinImporter and ExtensionFileLoader
                    # have exec_module() implemented, we can add a deprecation
                    # warning here.
                    self.spec.loader.load_module(name)
                else:
                    self._exec(module)
            return sys.modules[name]

        # def _load_backward_compatible(self):
        #     # (issue19713) Once BuiltinImporter and ExtensionFileLoader
        #     # have exec_module() implemented, we can add a deprecation
        #     # warning here.
        #     spec = self.spec
        #     spec.loader.load_module(spec.name)
        #     # The module must be in sys.modules at this point!
        #     module = sys.modules[spec.name]
        #     if getattr(module, '__loader__', None) is None:
        #         try:
        #             module.__loader__ = spec.loader
        #         except AttributeError:
        #             pass
        #     if getattr(module, '__package__', None) is None:
        #         try:
        #             # Since module.__path__ may not line up with
        #             # spec.submodule_search_paths, we can't necessarily rely
        #             # on spec.parent here.
        #             module.__package__ = module.__name__
        #             if not hasattr(module, '__path__'):
        #                 module.__package__ = spec.name.rpartition('.')[0]
        #         except AttributeError:
        #             pass
        #     if getattr(module, '__spec__', None) is None:
        #         try:
        #             module.__spec__ = spec
        #         except AttributeError:
        #             pass
        #     return module

        # def _load_unlocked(self):
        #     # A helper for direct use by the import system.
        #     if self.spec.loader is not None:
        #         # not a namespace package
        #         if not hasattr(self.spec.loader, 'exec_module'):
        #             return self._load_backward_compatible()
        #
        #     module = self.create()
        #     with _installed_safely(module):
        #         if self.spec.loader is None:
        #             if self.spec.submodule_search_locations is None:
        #                 raise _ImportError('missing loader', name=self.spec.name)
        #                 # A namespace package so do nothing.
        #         else:
        #             self._exec(module)
        #
        #     # We don't ensure that the import-related module attributes get
        #     # set in the sys.modules replacement case.  Such modules are on
        #     # their own.
        #     return sys.modules[self.spec.name]

        # A method used during testing of _load_unlocked() and by
        # _load_module_shim().
        def load(self):
            """Return a new module object, loaded by the spec's loader.

            The module is not added to its parent.

            If a module is already in sys.modules, that existing module gets
            clobbered.

            """
            _imp.acquire_lock()
            with _ModuleLockManager(self.spec.name):
                return self._load_unlocked()

    def _new_module(name):
        return type(sys)(name)

    # inspired from importlib2
    class _NamespacePath(object):
        """Represents a namespace package's path.  It uses the module name
        to find its parent module, and from there it looks up the parent's
        __path__.  When this changes, the module's own path is recomputed,
        using path_finder.  For top-level modules, the parent module's path
        is sys.path."""

        def __init__(self, name, path, path_finder):
            self._name = name
            self._path = path
            self._last_parent_path = tuple(self._get_parent_path())
            self._path_finder = path_finder

        def _find_parent_path_names(self):
            """Returns a tuple of (parent-module-name, parent-path-attr-name)"""
            parent, dot, me = self._name.rpartition('.')
            if dot == '':
                # This is a top-level module. sys.path contains the parent path.
                return 'sys', 'path'
            # Not a top-level module. parent-module.__path__ contains the
            #  parent path.
            return parent, '__path__'

        def _get_parent_path(self):
            parent_module_name, path_attr_name = self._find_parent_path_names()
            return getattr(sys.modules[parent_module_name], path_attr_name)

        def _recalculate(self):
            # If the parent's path has changed, recalculate _path
            parent_path = tuple(self._get_parent_path()) # Make a copy
            if parent_path != self._last_parent_path:
                spec = self._path_finder(self._name, parent_path)
                # Note that no changes are made if a loader is returned, but we
                #  do remember the new parent path
                if spec is not None and spec.loader is None:
                    if spec.submodule_search_locations:
                        self._path = spec.submodule_search_locations
                self._last_parent_path = parent_path     # Save the copy
            return self._path

        def __iter__(self):
            return iter(self._recalculate())

        def __len__(self):
            return len(self._recalculate())

        def __repr__(self):
            return '_NamespacePath({!r})'.format(self._path)

        def __contains__(self, item):
            return item in self._recalculate()

        def append(self, item):
            self._path.append(item)

    # inspired from importlib2
    class _NamespaceLoader(object):
        def __init__(self, name, path, subdirs):
            self._path = subdirs

        @classmethod
        def module_repr(cls, module):
            """Return repr for the module.

            The method is deprecated.  The import machinery does the job itself.

            """
            return '<module {!r} (namespace)>'.format(module.__name__)

        def is_package(self, fullname):
            return True

        def get_source(self, fullname):
            return ''

        def get_code(self, fullname):
            return compile('', '<string>', 'exec', dont_inherit=True)

        def exec_module(self, module):
            pass

        def _init_module_attrs(self, spec, module, _override=False, _force_name=True):
            """Set the module's attributes.

            All missing import-related module attributes will be set.  Here
            is how the spec attributes map onto the module:

            spec.name -> module.__name__
            spec.loader -> module.__loader__
            spec.parent -> module.__package__
            spec -> module.__spec__

            Optional:
            spec.origin -> module.__file__ (if spec.set_fileattr is true)
            spec.cached -> module.__cached__ (if __file__ also set)
            spec.submodule_search_locations -> module.__path__ (if set)

            """
            # The passed in module may be not support attribute assignment,
            # in which case we simply don't set the attributes.

            # __name__
            if (_override or _force_name or
                        getattr(module, '__name__', None) is None):
                try:
                    module.__name__ = spec.name
                except AttributeError:
                    pass

            # __loader__
            if _override or getattr(module, '__loader__', None) is None:
                loader = spec.loader
                if loader is None:
                    # A backward compatibility hack.
                    if spec.submodule_search_locations is not None:
                        loader = _NamespaceLoader.__new__(_NamespaceLoader)
                        loader._path = spec.submodule_search_locations
                try:
                    module.__loader__ = loader
                except AttributeError:
                    pass

            # __package__
            if _override or getattr(module, '__package__', None) is None:
                try:
                    module.__package__ = spec.parent
                except AttributeError:
                    pass

            # __spec__
            try:
                module.__spec__ = spec
            except AttributeError:
                pass

            # __path__
            if _override or getattr(module, '__path__', None) is None:
                if spec.submodule_search_locations is not None:
                    try:
                        module.__path__ = spec.submodule_search_locations
                    except AttributeError:
                        pass

            if spec.has_location:
                # __file__
                if _override or getattr(module, '__file__', None) is None:
                    try:
                        module.__file__ = spec.origin
                    except AttributeError:
                        pass

                # __cached__
                if _override or getattr(module, '__cached__', None) is None:
                    if spec.cached is not None:
                        try:
                            module.__cached__ = spec.cached
                        except AttributeError:
                            pass

        def _create(self, spec):
            """Return a new module to be loaded.

            The import-related module attributes are also set with the
            appropriate values from the spec.

            """
            # Typically loaders will not implement create_module().
            if hasattr(spec.loader, 'create_module'):
                # If create_module() returns `None` it means the default
                # module creation should be used.
                module = spec.loader.create_module(spec)
            else:
                module = None
            if module is None:
                # This must be done before open() is ever called as the 'io'
                # module implicitly imports 'locale' and would otherwise
                # trigger an infinite loop.
                module = _new_module(spec.name)
            self._init_module_attrs(spec, module)
            return module

        def load_module(self, fullname):
            """Load a namespace module.

            This method is deprecated.  Use exec_module() instead.

            """
            # The import system never calls this method.
            _verbose_message('namespace module loaded with path {!r}', self._path)

            spec = importlib_util.spec_from_loader(fullname, self)
            spec.submodule_search_locations = self._path
            if fullname in sys.modules:
                module = sys.modules[fullname]
                self._init_module_attrs(spec, module, _override=True)
                return sys.modules[fullname]
            else:
                module = self._create(spec)
                return module


elif sys.version_info >= (3, 4):  # we do not support 3.2 and 3.3 but importlib2 theoretically could...
    import importlib.machinery as importlib_machinery

else:
    raise ImportError("ros_loader : Unsupported python version")


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

    class ROSDefLoader(importlib_machinery.SourceFileLoader):
        def __init__(self, fullname, path, implicit_ns_pkg=False):

            self.logger = logging.getLogger(__name__)

            self.implicit_ns_package = implicit_ns_pkg

            if (2, 7) <= sys.version_info < (3, 4) and implicit_ns_pkg:  # the specific python2 usecase where we want a directory to be considered as a namespace package
                # we need to use the usual FileFinder logic
                super(ROSDefLoader, self).__init__(fullname, path)
            else:
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

    return ROSDefLoader

ROSMsgLoader = RosLoader(rosdef_extension='.msg')
ROSSrvLoader = RosLoader(rosdef_extension='.srv')
