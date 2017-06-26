from __future__ import absolute_import, division, print_function

import contextlib
import importlib
import site

from pyros_msgs.importer import rosmsg_loader

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

import logging

from .rosmsg_loader import ROSMsgLoader, ROSSrvLoader

if (2, 7) <= sys.version_info < (3, 4):  # valid until which py3 version ?
    # from .importlib2 import machinery as importlib_machinery
    # from .importlib2 import util as importlib_util
    import pkg_resources  # useful to have empty directory imply namespace package (like for py3)

    from .rosmsg_loader import _ImportError, _verbose_message, FileLoader2

    import imp

    def spec_from_file_location(name, location=None, loader=None,
                                submodule_search_locations=None):
        """Return a module spec based on a file location.

        To indicate that the module is a package, set
        submodule_search_locations to a list of directory paths.  An
        empty list is sufficient, though its not otherwise useful to the
        import system.

        The loader must take a spec as its only __init__() arg.

        """

        if location is None:
            # The caller may simply want a partially populated location-
            # oriented spec.  So we set the location to a bogus value and
            # fill in as much as we can.
            location = '<unknown>'
            if hasattr(loader, 'get_filename'):
                # ExecutionLoader
                try:
                    location = loader.get_filename(name)
                except ImportError:
                    pass

        # If the location is on the filesystem, but doesn't actually exist,
        # we could return None here, indicating that the location is not
        # valid.  However, we don't have a good way of testing since an
        # indirect location (e.g. a zip file or URL) will look like a
        # non-existent file relative to the filesystem.

        spec = ModuleSpec(name, loader, origin=location)
        spec._set_fileattr = True

        # Pick a loader if one wasn't provided.
        if loader is None:
            for loader_class, suffixes in _get_supported_file_loaders():
                if location.endswith(tuple(suffixes)):
                    loader = loader_class(name, location)
                    spec.loader = loader
                    break
            else:
                return None

        # Set submodule_search_paths appropriately.
        if submodule_search_locations is None:
            # Check the loader.
            if hasattr(loader, 'is_package'):
                try:
                    is_package = loader.is_package(name)
                except ImportError:
                    pass
                else:
                    if is_package:
                        spec.submodule_search_locations = []
        else:
            spec.submodule_search_locations = submodule_search_locations
        if spec.submodule_search_locations == []:
            if location:
                dirname = os.path.split(location)[0]
                spec.submodule_search_locations.append(dirname)

        return spec

    class FileFinder2(object):
        def __init__(self, path, *loader_details):
            """Initialize with the path to search on and a variable number of
            2-tuples containing the loader and the file suffixes the loader
            recognizes."""
            loaders = []
            for loader, suffixes in loader_details:
                loaders.extend((suffix, loader) for suffix in suffixes)
            self._loaders = loaders
            # Base (directory) path
            self.path = path or '.'
            # Note : we are not playing with cache here (too complex to get right and not worth it for obsolete python)

        def _get_spec(self, loader_class, fullname, path, smsl, target):
            loader = loader_class(fullname, path)
            return spec_from_file_location(fullname, path, loader=loader, submodule_search_locations=smsl)

        def find_module(self, fullname, path=None):
            """Try to find a loader for the specified module, or the namespace
            package portions. Returns loader."""
            path = path or self.path
            tail_module = fullname.rpartition('.')[2]

            base_path = os.path.join(path, tail_module)
            for suffix, loader_class in self._loaders:
                full_path = None  # adjusting path for package or file
                if os.path.isdir(base_path) and os.path.isfile(os.path.join(base_path, '__init__' + suffix)):
                    return loader_class(fullname, base_path)  # __init__.py path will be computed by the loader when needed
                elif os.path.isfile(base_path + suffix):
                    return loader_class(fullname, base_path + suffix)
            else:
                if os.path.isdir(base_path):
                    # If a namespace package, return the path if we don't
                    #  find a module in the next section.
                    _verbose_message('possible namespace for {}'.format(base_path))
                    return FileLoader2(fullname, base_path)

            # # Check for a file w/ a proper suffix exists.
            # for suffix, loader_class in self._loaders:
            #     full_path = os.path.join(self.path, tail_module + suffix)
            #     _verbose_message('trying {}'.format(full_path), verbosity=2)
            #     if cache_module + suffix in cache:
            #         if os.path.isfile(full_path):
            #             return loader_class(fullname, full_path)
            #             #return self._get_spec(loader_class, fullname, full_path, None, target)

            # if is_namespace:
            #     _verbose_message('possible namespace for {}'.format(base_path))
            #     return loader_class(fullname, None)
            #     # spec = ModuleSpec(fullname, None)
            #     # spec.submodule_search_locations = [base_path]
            #     # return spec
            return None

        @classmethod
        def path_hook(cls, *loader_details):
            """A class method which returns a closure to use on sys.path_hook
            which will return an instance using the specified loaders and the path
            called on the closure.

            If the path called on the closure is not a directory, ImportError is
            raised.

            """
            def path_hook_for_FileFinder(path):
                """Path hook for importlib.machinery.FileFinder."""
                if not os.path.isdir(path):
                    raise _ImportError('only directories are supported', path=path)
                return cls(path, *loader_details)

            return path_hook_for_FileFinder

        def __repr__(self):
            return 'FileFinder2({!r})'.format(self.path)


    class FileFinder(object):

        """File-based finder.

        Interactions with the file system are cached for performance, being
        refreshed when the directory the finder is handling has been modified.

        """

        def __init__(self, path, *loader_details):
            """Initialize with the path to search on and a variable number of
            2-tuples containing the loader and the file suffixes the loader
            recognizes."""
            loaders = []
            for loader, suffixes in loader_details:
                loaders.extend((suffix, loader) for suffix in suffixes)
            self._loaders = loaders
            # Base (directory) path
            self.path = path or '.'
            self._path_mtime = -1
            self._path_cache = set()
            self._relaxed_path_cache = set()

        def invalidate_caches(self):
            """Invalidate the directory mtime."""
            self._path_mtime = -1

        #find_module = _find_module_shim

        def find_loader(self, fullname):
            """Try to find a loader for the specified module, or the namespace
            package portions. Returns (loader, list-of-portions).

            This method is deprecated.  Use find_spec() instead.

            """
            spec = self.find_spec(fullname)
            if spec is None:
                return None, []
            return spec.loader, spec.submodule_search_locations or []



        def find_spec(self, fullname, target=None):
            """Try to find a loader for the specified module, or the namespace
            package portions. Returns (loader, list-of-portions)."""
            is_namespace = False
            tail_module = fullname.rpartition('.')[2]
            try:
                mtime = _path_stat(self.path or _os.getcwd()).st_mtime
            except OSError:
                mtime = -1
            if mtime != self._path_mtime:
                self._fill_cache()
                self._path_mtime = mtime
            # tail_module keeps the original casing, for __file__ and friends
            if _relax_case():
                cache = self._relaxed_path_cache
                cache_module = tail_module.lower()
            else:
                cache = self._path_cache
                cache_module = tail_module
            # Check if the module is the name of a directory (and thus a package).
            if cache_module in cache:
                base_path = _path_join(self.path, tail_module)
                for suffix, loader_class in self._loaders:
                    init_filename = '__init__' + suffix
                    full_path = _path_join(base_path, init_filename)
                    if _path_isfile(full_path):
                        return self._get_spec(loader_class, fullname, full_path, [base_path], target)
                else:
                    # If a namespace package, return the path if we don't
                    #  find a module in the next section.
                    is_namespace = _path_isdir(base_path)
            # Check for a file w/ a proper suffix exists.
            for suffix, loader_class in self._loaders:
                full_path = _path_join(self.path, tail_module + suffix)
                _verbose_message('trying {}'.format(full_path), verbosity=2)
                if cache_module + suffix in cache:
                    if _path_isfile(full_path):
                        return self._get_spec(loader_class, fullname, full_path, None, target)
            if is_namespace:
                _verbose_message('possible namespace for {}'.format(base_path))
                spec = ModuleSpec(fullname, None)
                spec.submodule_search_locations = [base_path]
                return spec
            return None


    def _get_supported_ns_loaders():
        """Returns a list of file-based module loaders.
        Each item is a tuple (loader, suffixes).
        """
        loader = FileLoader2, [suffix for suffix, mode, type in imp.get_suffixes()]
        return [loader]


    class DirectoryFinder(FileFinder2):
        """Finder to interpret directories as modules, and files as classes"""

        def __init__(self, path, *ros_loader_details):
            """
            Finder to get directories containing ROS message and service files.
            It need to be inserted in sys.path_hooks before FileFinder, since these are Directories but not containing __init__ as per python hardcoded convention.

            Note: There is a matching issue between msg/ folder and msg/My.msg on one side, and package, module, class concepts on the other.
            Since a module is not callable, but we need to call My(data) to build a message class (ROS convention), we match the msg/ folder to a module (and not a package)
            And to keep matching ROS conventions, a directory without __init__ or any message/service file, will become a namespace (sub)package.

            :param path_entry: the msg or srv directory path (no finder should have been instantiated yet)
            """

            ros_loaders = []
            for loader, suffixes in ros_loader_details:
                ros_loaders.extend((suffix, loader) for suffix in suffixes)
            self._ros_loaders = ros_loaders

            # # Form importlib FileFinder
            # loaders = []
            # for loader, suffixes in [(importlib_machinery.SourceFileLoader, ['.py']), (importlib_machinery.SourcelessFileLoader, ['.pyc'])]:
            #     loaders.extend((suffix, loader) for suffix in suffixes)
            # self._loaders = loaders
            # Base (directory) path
            self.path = path or '.'
            self._path_mtime = -1
            self._path_cache = set()
            self._relaxed_path_cache = set()

        def __repr__(self):
            return 'DirectoryFinder({!r})'.format(self.path)

        def find_module(self, fullname, path=None):
            path = path or self.path

            tail_module = fullname.rpartition('.')[2]

            loader = None

            # ignoring the generated message module when looking for it. Instead we want to start again from the original .msg/.srv.
            # if tail_module.startswith('_') and any(os.path.isfile(os.path.join(self.path, tail_module[1:] + sfx) for sfx, _ in self._loaders)):  # consistent with generated module from msg package
            #     tail_module = tail_module[1:]
            base_path = os.path.join(self.path, tail_module)

            # special code here since FileFinder expect a "__init__" that we don't need for msg or srv.
            if os.path.isdir(base_path):
                loader_class = None
                rosdir = None
                # Figuring out if we should care about this directory at all
                for root, dirs, files in os.walk(base_path):
                    for suffix, loader_cls in self._ros_loaders:
                        if any(f.endswith(suffix) for f in files):
                            loader_class = loader_cls
                            rosdir = root
                if loader_class and rosdir:
                    if rosdir == base_path:  # we found a message/service file in the hierarchy, that belong to our module
                        # Generate something !
                        # we are looking for submodules either in generated location (to be able to load generated python files) or in original msg location
                        loader = loader_class(fullname, base_path)  # loader.get_gen_path()])
                        # We DO NOT WANT TO add the generated dir in sys.path to use a python loader
                        # since the plan is to eventually not have to rely on files at all TODO
                    else:
                        # directory not matching our path, so this should be a namespace, and has to be explicit in python < 3.2

                        # But we still rely on importlib2 code to backport namespace packages logic
                        # Done via loader custom code
                        loader = loader_class(fullname, base_path, implicit_ns_pkg=True)

            # we return None if we couldn't build a loader before
            return loader

        # inspired from importlib2
        @classmethod
        def path_hook(cls, *loader_details):
            """A class method which returns a closure to use on sys.path_hook
            which will return an instance using the specified loaders and the path
            called on the closure.

            If the path called on the closure is not a directory, ImportError is
            raised.

            """

            def path_hook_for_FileFinder(path):
                """Path hook for rosimport.DirectoryFinder."""
                if not os.path.isdir(path):
                    raise _ImportError('only directories are supported', path=path)
                return cls(path, *loader_details)

            return path_hook_for_FileFinder

        def __repr__(self):
            return 'FileFinder({!r})'.format(self.path)

        # def find_spec(self, fullname, target=None):
        #     """
        #     Try to find a spec for the specified module.
        #             Returns the matching spec, or None if not found.
        #     :param fullname: the name of the package we are trying to import
        #     :param target: what we plan to do with it
        #     :return:
        #     """
        #
        #     tail_module = fullname.rpartition('.')[2]
        #
        #     spec = None
        #
        #     # ignoring the generated message module when looking for it. Instead we want to start again from the original .msg/.srv.
        #     # if tail_module.startswith('_') and any(os.path.isfile(os.path.join(self.path, tail_module[1:] + sfx) for sfx, _ in self._loaders)):  # consistent with generated module from msg package
        #     #     tail_module = tail_module[1:]
        #     base_path = os.path.join(self.path, tail_module)
        #
        #     # special code here since FileFinder expect a "__init__" that we don't need for msg or srv.
        #     if os.path.isdir(base_path):
        #         loader_class = None
        #         rosdir = None
        #         # Figuring out if we should care about this directory at all
        #         for root, dirs, files in os.walk(base_path):
        #             for suffix, loader_cls in self._ros_loaders:
        #                 if any(f.endswith(suffix) for f in files):
        #                     loader_class = loader_cls
        #                     rosdir = root
        #         if loader_class and rosdir:
        #             if rosdir == base_path:  # we found a message/service file in the hierarchy, that belong to our module
        #                 # Generate something !
        #                 loader = loader_class(fullname, base_path)
        #                 # we are looking for submodules either in generated location (to be able to load generated python files) or in original msg location
        #                 spec = importlib_util.spec_from_file_location(fullname, base_path, loader=loader, submodule_search_locations=[base_path, loader.get_gen_path()])
        #                 # We DO NOT WANT TO add the generated dir in sys.path to use a python loader
        #                 # since the plan is to eventually not have to rely on files at all TODO
        #             # elif (2, 7) <= sys.version_info < (3, 4):
        #             #     # Found nothing, so this should be a namespace, and has to be explicit in python < 3.2
        #             #     # But we still rely on importlib2 code to backport namespace packages logic
        #             #     # Done via loader custom code
        #             #     spec = importlib_util.spec_from_file_location(fullname, base_path,
        #             #                                                   loader=None,
        #             #                                                   #loader=loader_class(fullname, base_path, implicit_ns_pkg=True)
        #             #                                                   submodule_search_locations=[base_path])
        #             #     #spec = importlib_machinery.ModuleSpec(name=fullname, origin=base_path, loader=loader_class(fullname, base_path, implicit_ns_pkg=True), is_package=True)
        #
        #     # Relying on FileFinder if we couldn't find any specific directory structure/content
        #     # It will return a namespace spec if no file can be found (even with python2.7, thanks to importlib2)
        #     # or will return a proper loader for already generated python files
        #     spec = spec or super(DirectoryFinder, self).find_spec(fullname, target=target)
        #     # we return None if we couldn't find a spec before
        #     return spec



elif sys.version_info >= (3, 4):  # we do not support 3.2 and 3.3 but importlib2 theoritically could...
    import importlib.machinery as importlib_machinery
    import importlib.util as importlib_util



    class DirectoryFinder(importlib_machinery.FileFinder):
        """Finder to interpret directories as modules, and files as classes"""

        def __init__(self, path, *ros_loader_details):
            """
            Finder to get directories containing ROS message and service files.
            It need to be inserted in sys.path_hooks before FileFinder, since these are Directories but not containing __init__ as per python hardcoded convention.

            Note: There is a matching issue between msg/ folder and msg/My.msg on one side, and package, module, class concepts on the other.
            Since a module is not callable, but we need to call My(data) to build a message class (ROS convention), we match the msg/ folder to a module (and not a package)
            And to keep matching ROS conventions, a directory without __init__ or any message/service file, will become a namespace (sub)package.

            :param path_entry: the msg or srv directory path (no finder should have been instantiated yet)
            """

            ros_loaders = []
            for loader, suffixes in ros_loader_details:
                ros_loaders.extend((suffix, loader) for suffix in suffixes)
            self._ros_loaders = ros_loaders

            # We rely on FileFinder and python loader to deal with our generated code
            super(DirectoryFinder, self).__init__(
                path,
                (importlib_machinery.SourceFileLoader, ['.py']),
                (importlib_machinery.SourcelessFileLoader, ['.pyc']),
            )

        def __repr__(self):
            return 'DirectoryFinder({!r})'.format(self.path)

        def find_spec(self, fullname, target=None):
            """
            Try to find a spec for the specified module.
                    Returns the matching spec, or None if not found.
            :param fullname: the name of the package we are trying to import
            :param target: what we plan to do with it
            :return:
            """

            tail_module = fullname.rpartition('.')[2]

            spec = None

            # ignoring the generated message module when looking for it. Instead we want to start again from the original .msg/.srv.
            # if tail_module.startswith('_') and any(os.path.isfile(os.path.join(self.path, tail_module[1:] + sfx) for sfx, _ in self._loaders)):  # consistent with generated module from msg package
            #     tail_module = tail_module[1:]
            base_path = os.path.join(self.path, tail_module)

            # special code here since FileFinder expect a "__init__" that we don't need for msg or srv.
            if os.path.isdir(base_path):
                loader_class = None
                rosdir = None
                # Figuring out if we should care about this directory at all
                for root, dirs, files in os.walk(base_path):
                    for suffix, loader_cls in self._ros_loaders:
                        if any(f.endswith(suffix) for f in files):
                            loader_class = loader_cls
                            rosdir = root
                if loader_class and rosdir:
                    if rosdir == base_path:  # we found a message/service file in the hierarchy, that belong to our module
                        # Generate something !
                        loader = loader_class(fullname, base_path)
                        # we are looking for submodules either in generated location (to be able to load generated python files) or in original msg location
                        spec = importlib_util.spec_from_file_location(fullname, base_path, loader=loader, submodule_search_locations=[base_path, loader.get_gen_path()])
                        # We DO NOT WANT TO add the generated dir in sys.path to use a python loader
                        # since the plan is to eventually not have to rely on files at all TODO
                    # elif (2, 7) <= sys.version_info < (3, 4):
                    #     # Found nothing, so this should be a namespace, and has to be explicit in python < 3.2
                    #     # But we still rely on importlib2 code to backport namespace packages logic
                    #     # Done via loader custom code
                    #     spec = importlib_util.spec_from_file_location(fullname, base_path,
                    #                                                   loader=None,
                    #                                                   #loader=loader_class(fullname, base_path, implicit_ns_pkg=True)
                    #                                                   submodule_search_locations=[base_path])
                    #     #spec = importlib_machinery.ModuleSpec(name=fullname, origin=base_path, loader=loader_class(fullname, base_path, implicit_ns_pkg=True), is_package=True)

            # Relying on FileFinder if we couldn't find any specific directory structure/content
            # It will return a namespace spec if no file can be found (even with python2.7, thanks to importlib2)
            # or will return a proper loader for already generated python files
            spec = spec or super(DirectoryFinder, self).find_spec(fullname, target=target)
            # we return None if we couldn't find a spec before
            return spec


else:
    raise ImportError("ros_loader : Unsupported python version")


MSG_SUFFIXES = ['.msg']
SRV_SUFFIXES = ['.srv']

def _get_supported_ros_loaders():
    """Returns a list of file-based module loaders.
    Each item is a tuple (loader, suffixes).
    """
    msg = ROSMsgLoader, MSG_SUFFIXES
    srv = ROSSrvLoader, SRV_SUFFIXES
    return [msg, srv]


def _install():
    """Install the path-based import components."""
    supported_loaders = _get_supported_ros_loaders()
    sys.path_hooks.extend([DirectoryFinder.path_hook(*supported_loaders)])
    # TODO : sys.meta_path.append(DistroFinder)



# Useless ?
#_ros_finder_instance_obsolete_python = ROSImportFinder

ros_distro_finder = None

# TODO : metafinder
def activate(rosdistro_path=None, *workspaces):
    global ros_distro_finder
    if rosdistro_path is None:  # autodetect most recent installed distro
        if os.path.exists('/opt/ros/lunar'):
            rosdistro_path = '/opt/ros/lunar'
        elif os.path.exists('/opt/ros/kinetic'):
            rosdistro_path = '/opt/ros/kinetic'
        elif os.path.exists('/opt/ros/jade'):
            rosdistro_path = '/opt/ros/jade'
        elif os.path.exists('/opt/ros/indigo'):
            rosdistro_path = '/opt/ros/indigo'
        else:
            raise ImportError(
                "No ROS distro detected on this system. Please specify the path when calling ROSImportMetaFinder()")

    ros_distro_finder = ROSImportMetaFinder(rosdistro_path, *workspaces)
    sys.meta_path.append(ros_distro_finder)

    #if sys.version_info >= (2, 7, 12):  # TODO : which exact version matters ?

    # We need to be before FileFinder to be able to find our (non .py[c]) files
    # inside, maybe already imported, python packages...
    sys.path_hooks.insert(1, ROSImportFinder)

    # else:  # older (trusty) version
    #     sys.path_hooks.append(_ros_finder_instance_obsolete_python)

    for hook in sys.path_hooks:
        print('Path hook: {}'.format(hook))

    # TODO : mix that with ROS PYTHONPATH shenanigans... to enable the finder only for 'ROS aware' paths
    if paths:
        sys.path.append(*paths)


def deactivate(*paths):
    """ CAREFUL : even if we remove our path_hooks, the created finder are still cached in sys.path_importer_cache."""
    #if sys.version_info >= (2, 7, 12):  # TODO : which exact version matters ?
    sys.path_hooks.remove(ROSImportFinder)
    # else:  # older (trusty) version
    #     sys.path_hooks.remove(_ros_finder_instance_obsolete_python)
    if paths:
        sys.path.remove(*paths)

    sys.meta_path.remove(ros_distro_finder)


@contextlib.contextmanager
def ROSImportContext(*paths):
    activate(*paths)
    yield
    deactivate(*paths)


# TODO : a meta finder could find a full ROS distro...
