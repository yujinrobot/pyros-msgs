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

if sys.version_info >= (3, 4):

    import importlib.abc
    import importlib.machinery
    import importlib.util


    class ROSFileFinder(importlib.machinery.FileFinder):

        def __init__(self, path):
            """
            Finder to get ROS specific files and directories (message and services files).
            It need to be inserted in sys.path_hooks before FileFinder, since these are Files but not python ones.

            :param path_entry: the msg or srv directory path (no finder should have been instantiated yet)
            """

            # Declaring our loaders and the different extensions
            self.extended_loader_details = [
                (ROSMsgLoader, ['.msg']),
                (ROSSrvLoader, ['.srv']),
            ]

            # We rely on FileFinder, just with different loaders for different file extensions
            super(ROSFileFinder, self).__init__(
                path,
                *self.extended_loader_details
            )

        def find_spec(self, fullname, target=None):
            """
            Try to find a spec for the specified module.
                    Returns the matching spec, or None if not found.
            :param fullname: the name of the package we are trying to import
            :param target: what we plan to do with it
            :return:
            """

            tail_module = fullname.rpartition('.')[2]
            loader = None
            spec = None
            # special code here since FileFinder expect a "__init__" that we don't need for msg or srv.
            base_path = os.path.join(self.path, tail_module)
            if os.path.isdir(base_path):
                for suffix, loader_class in self._loaders:
                    loader = loader_class(fullname, base_path) if [f for f in os.listdir(base_path) if f.endswith(suffix)] else loader
                # DO we need one or two loaders ? (package logic is same, but msg or srv differs after...)
                if loader:
                    spec = importlib.util.spec_from_file_location(fullname, base_path, loader=loader, submodule_search_locations=[base_path])
            else:
                if tail_module.startswith('_'):  # consistent with generated module from msg package
                    base_path = os.path.join(self.path, tail_module[1:])
                    for suffix, loader_class in self._loaders:
                        loader = loader_class(fullname, base_path + suffix) if os.path.isfile(base_path + suffix) else loader
                    if loader:
                        spec = importlib.util.spec_from_file_location(fullname, loader.path, loader=loader)
                else:  # probably an attempt to import the class in the generated module (shortcutting python import mechanism)
                    base_path = os.path.join(self.path, tail_module)
                    for suffix, loader_class in self._loaders:
                        loader = loader_class(fullname, base_path + suffix) if os.path.isfile(base_path + suffix) else loader
                    if loader:
                        spec = importlib.util.spec_from_file_location(fullname, loader.path, loader=loader)

            # we use default behavior if we couldn't find a spec before
            spec = spec or super(ROSFileFinder, self).find_spec(fullname=fullname, target=target)
            return spec


    class ROSImportFinder(importlib.abc.PathEntryFinder):
        # TODO : we can use this to enable ROS Finder only on relevant paths (ros distro paths + dev workspaces) from sys.path

        def __init__(self, workspace_entry):
            """
            Finder to get ROS packages (python code and message files).
            It need to be inserted in sys.path_hooks before FileFinder, since these are Files but not python

            Note : it is currently not possible (tested on python 3.4) to build a solid finder only for a set of messages that would be part of a python package,
             since sub-packages do not follow the same import logic as modules (finder not called since we are already with a known standard python importer)
            Therefore this finder focuses on importing a whole ROS package, and messages have to be in a ROS package.

            :param path_entry: the ROS workspace path (no finder should have been instantiated yet)
            """
            super(ROSImportFinder, self).__init__()

            # First we need to skip all the cases that we are not concerned with

            # if path_entry != self.PATH_TRIGGER:
            #     self.logger.debug('ROSImportFinder does not work for %s' % path_entry)
            #     raise ImportError()

            # Adding the share path (where we can find all packages and their messages)
            share_path = os.path.join(workspace_entry, 'share')
            if os.path.exists(share_path):
                self.share_path = share_path

                python_libpath = os.path.join(workspace_entry, 'lib',
                                              'python' + sys.version_info.major + '.' + sys.version_info.minor)
                if os.path.exists(python_libpath):
                    # adding python site directories for the ROS distro (to find python modules as usual with ROS)
                    if os.path.exists(os.path.join(python_libpath, 'dist-packages')):
                        site.addsitedir(os.path.join(python_libpath, 'dist-packages'))
                    if os.path.exists(os.path.join(python_libpath, 'site-packages')):
                        site.addsitedir(os.path.join(python_libpath, 'site-packages'))
                    # Note : here we want to keep a pure python logic to not pollute the environment (not like with pyros-setup)

                # self.rospkgs = []
                # for root, dirs, files in os.walk(self.share_path, topdown=False):
                #     if 'package.xml' in files:  # we have found a ros package
                #
                #
                #
                #         self.rospkgs.append(root)
                #         found_one = True
                # if not found_one:
                #     raise ImportError("No ROS package found in {0}".format(workspace_entry))

            else:  # this is not a workspace, maybe we are expected to get the package directly from source ?
                found_one = False
                self.src_rospkgs = []
                for root, dirs, files in os.walk(workspace_entry, topdown=False):
                    if 'package.xml' in files:  # we have found a ros package
                        self.src_rospkgs.append(root)
                        found_one = True
                if not found_one:
                    raise ImportError("No ROS package found in {0}".format(workspace_entry))


            # # path_entry contains the path where the finder has been instantiated...
            # if (not os.path.exists(path_entry) or  # non existent path
            #     not os.path.basename(path_entry) in ['msg', 'srv']  # path not terminated with msg/srv (msg and srv inside python source)
            # ):
            #     raise ImportError  # we raise if we cannot find msg or srv folder

            # Then we can do the initialisation
            self.logger = logging.getLogger(__name__)
            self.logger.debug('Checking ROSImportFinder support for %s' % workspace_entry)

            self.workspace_entry = workspace_entry


        def find_spec(self, fullname, target = None):
            print('ROSImportFinder looking for "%s"' % fullname)
            """
            :param fullname: the name of the package we are trying to import
            :param target: what we plan to do with it
            :return:
            """
            # TODO: read PEP 420 :)
            last_mile = fullname.split('.')[-1]

            for src_pkg in self.src_rospkgs:
                if os.path.basename(src_pkg) == fullname:  # we found it
                    return importlib.machinery.ModuleSpec(
                        fullname,
                        None,  # TODO loader
                        origin=src_pkg,
                        is_package=True
                    )

            # If we get here, we need to find the package in a workspace...

            # If we can find it in share/ with messages, we can generate them.
              # good or bad idea ?
            # Else, we can use the usual python import (since we added them to site)
            #return importlib.util.. (fullname).



            for root, dirs, files in os.walk(self.workspace_entry, topdown=False):
                if last_mile + '.msg' in files:
                    return importlib.machinery.ModuleSpec(
                        fullname,
                        None,  # TODO loader
                        origin=root,
                        is_package=False
                    )
                if last_mile + '.srv' in files:
                    return importlib.machinery.ModuleSpec(
                        fullname,
                        None,  # TODO loader
                        origin=root,
                        is_package=False
                    )

            # we couldn't find the module. let someone else find it.
            return None


else:
    class ROSImportFinder(object):
        """Find ROS message/service modules"""
        def __init__(self, path_entry=None):
            # First we need to skip all the cases that we are not concerned with

            # path_entry contains the path where the finder has been instantiated...
            if not os.path.exists(os.path.join(path_entry, 'msg')) and not os.path.exists(os.path.join(path_entry, 'srv')):
                raise ImportError  # we raise if we cannot find msg or srv folder

            # Then we can do the initialisation
            self.logger = logging.getLogger(__name__)
            self.logger.debug('Checking ROSImportFinder support for %s' % path_entry)

            self.path_entry = path_entry


        # This is called for the first unknown (not loaded) name inside path
        def find_module(self, name, path=None):
            self.logger.debug('ROSImportFinder looking for "%s"' % name)

            # on 2.7
            path = path or self.path_entry

            # implementation inspired from pytest.rewrite
            names = name.rsplit(".", 1)
            lastname = names[-1]


            if not os.path.exists(os.path.join(path, lastname)):
                raise ImportError
            elif os.path.isdir(os.path.join(path, lastname)):

                rosf = [f for f in os.listdir(os.path.join(path, lastname)) if os.path.splitext(f)[-1] in ['.msg', '.srv']]

                if rosf:
                    return ROSLoader(
                        msgsrv_files=rosf,
                        path_entry=os.path.join(path, lastname),
                        package=name,
                        outdir_pkg=path,  # TODO: if we cannot write into source, use tempfile
                        #includepath=,
                        #ns_pkg=,
                    )

                # # package case
                # for root, dirs, files in  os.walk(path, topdown=True):
                #
                #     #rosmsg_generator.genmsgsrv_py(msgsrv_files=[f for f in files if ], package=package, outdir_pkg=outdir_pkg, includepath=include_path, ns_pkg=ns_pkg)
                #
                #     # generated_msg = genmsg_py(msg_files=[f for f in files if f.endswith('.msg')],
                #     #                           package=package,
                #     #                           outdir_pkg=outdir_pkg,
                #     #                           includepath=includepath,
                #     #                           initpy=True)  # we always create an __init__.py when called from here.
                #     # generated_srv = gensrv_py(srv_files=[f for f in files if f.endswith('.srv')],
                #     #                           package=package,
                #     #                           outdir_pkg=outdir_pkg,
                #     #                           includepath=includepath,
                #     #                           initpy=True)  # we always create an __init__.py when called from here.
                #
                #     for name in dirs:
                #         print(os.path.join(root, name))
                #         # rosmsg_generator.genmsgsrv_py(msgsrv_files=msgsrvfiles, package=package, outdir_pkg=outdir_pkg, includepath=include_path, ns_pkg=ns_pkg)

            elif os.path.isfile(os.path.join(path, lastname)):
                # module case
                return ROSLoader(
                    msgsrv_files=os.path.join(path, lastname),
                    path_entry=path,
                    package=name,
                    outdir_pkg=path,  # TODO: if we cannot write into source, use tempfile
                    # includepath=,
                    # ns_pkg=,
                )

            return None





    # def find_module(self, name, path=None):
    #     """
    #     Return the loader for the specified module.
    #     """
    #     # Ref : https://www.python.org/dev/peps/pep-0302/#specification-part-1-the-importer-protocol
    #
    #     #
    #     loader = None
    #
    #     # path = path or sys.path
    #     # for p in path:
    #     #     for f in os.listdir(p):
    #     #         filename, ext = os.path.splitext(f)
    #     #         # our modules generated from messages are always a leaf in import tree so we only care about this case
    #     #         if ext in self.loaders.keys() and filename == name.split('.')[-1]:
    #     #             loader = self.loaders.get(ext)
    #     #             break  # we found it. break out.
    #     #
    #     # return loader
    #
    #     # implementation inspired from pytest.rewrite
    #     self.logger.debug("find_module called for: %s" % name)
    #     names = name.rsplit(".", 1)
    #     lastname = names[-1]
    #     pth = None
    #     if path is not None:
    #         # Starting with Python 3.3, path is a _NamespacePath(), which
    #         # causes problems if not converted to list.
    #         path = list(path)
    #         if len(path) == 1:
    #             pth = path[0]
    #
    #
    #     if pth is None:
    #
    #
    #
    #
    #
    #         try:
    #             fd, fn, desc = imp.find_module(lastname, path)
    #         except ImportError:
    #             return None
    #         if fd is not None:
    #             fd.close()
    #
    #
    #
    #
    #         tp = desc[2]
    #         if tp == imp.PY_COMPILED:
    #             if hasattr(imp, "source_from_cache"):
    #                 try:
    #                     fn = imp.source_from_cache(fn)
    #                 except ValueError:
    #                     # Python 3 doesn't like orphaned but still-importable
    #                     # .pyc files.
    #                     fn = fn[:-1]
    #             else:
    #                 fn = fn[:-1]
    #         elif tp != imp.PY_SOURCE:
    #             # Don't know what this is.
    #             return None
    #     else:
    #         fn = os.path.join(pth, name.rpartition(".")[2] + ".py")
    #
    #     fn_pypath = py.path.local(fn)
    #     if not self._should_rewrite(name, fn_pypath, state):
    #         return None
    #
    #     self._rewritten_names.add(name)
    #
    #     # The requested module looks like a test file, so rewrite it. This is
    #     # the most magical part of the process: load the source, rewrite the
    #     # asserts, and load the rewritten source. We also cache the rewritten
    #     # module code in a special pyc. We must be aware of the possibility of
    #     # concurrent pytest processes rewriting and loading pycs. To avoid
    #     # tricky race conditions, we maintain the following invariant: The
    #     # cached pyc is always a complete, valid pyc. Operations on it must be
    #     # atomic. POSIX's atomic rename comes in handy.
    #     write = not sys.dont_write_bytecode
    #     cache_dir = os.path.join(fn_pypath.dirname, "__pycache__")
    #     if write:
    #         try:
    #             os.mkdir(cache_dir)
    #         except OSError:
    #             e = sys.exc_info()[1].errno
    #             if e == errno.EEXIST:
    #                 # Either the __pycache__ directory already exists (the
    #                 # common case) or it's blocked by a non-dir node. In the
    #                 # latter case, we'll ignore it in _write_pyc.
    #                 pass
    #             elif e in [errno.ENOENT, errno.ENOTDIR]:
    #                 # One of the path components was not a directory, likely
    #                 # because we're in a zip file.
    #                 write = False
    #             elif e in [errno.EACCES, errno.EROFS, errno.EPERM]:
    #                 state.trace("read only directory: %r" % fn_pypath.dirname)
    #                 write = False
    #             else:
    #                 raise
    #     cache_name = fn_pypath.basename[:-3] + PYC_TAIL
    #     pyc = os.path.join(cache_dir, cache_name)
    #     # Notice that even if we're in a read-only directory, I'm going
    #     # to check for a cached pyc. This may not be optimal...
    #     co = _read_pyc(fn_pypath, pyc, state.trace)
    #     if co is None:
    #         state.trace("rewriting %r" % (fn,))
    #         source_stat, co = _rewrite_test(self.config, fn_pypath)
    #         if co is None:
    #             # Probably a SyntaxError in the test.
    #             return None
    #         if write:
    #             _make_rewritten_pyc(state, source_stat, pyc, co)
    #     else:
    #         state.trace("found cached rewritten pyc for %r" % (fn,))
    #     self.modules[name] = co, pyc
    #     return self


# Useless ?
#_ros_finder_instance_obsolete_python = ROSImportFinder

ros_distro_finder = None


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
