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

if (2, 7) <= sys.version_info < (3, 4):
    from .importlib2 import machinery as importlib_machinery
    from .importlib2 import util as importlib_util
    import pkg_resources  # useful to have empty directory imply namespace package (like for py3)

elif sys.version_info >= (3, 4):  # we do not support 3.2 and 3.3 but importlib2 theoritically could...
    import importlib.machinery as importlib_machinery
    import importlib.util as importlib_util

else:
    raise ImportError("ros_loader : Unsupported python version")


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

    if (2, 7) <= sys.version_info < (3, 4):
        def find_module(self, fullname, path=None):
            from .rosmsg_loader import _NamespaceLoader
            spec = self.find_spec(fullname=fullname)
            loader = spec.loader
            if loader is None:
                # A backward compatibility hack from importlib2
                if spec.submodule_search_locations is not None:
                    loader = _NamespaceLoader(spec.name, spec.origin, spec.submodule_search_locations)
            return loader

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
