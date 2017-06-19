from __future__ import absolute_import, division, print_function

import imp

import py

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


class ROSLoader(object):

    def __init__(self, path_entry, msgsrv_files, package, outdir_pkg, includepath = None, ns_pkg = None):

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

    def _get_filename(self, fullname):
        # Make up a fake filename that starts with the path entry
        # so pkgutil.get_data() works correctly.
        return os.path.join(self.path_entry, fullname)

    # defining this to benefit from backward compat import mechanism in python 3.X
    def is_package(self, name):
        names = name.split(".")
        parent_idx = len(names) -1
        # trying to find a parent already loaded
        while 0<= parent_idx < len(names) :
            if names[parent_idx] in sys.modules: # we found a parent, we can get his path and go back
                pass
            else:  # parent not found, need to check its parent
                parent_idx-=1


        else:  # No loaded parent found, lets attempt to import it directly (searching in all sys.paths)

            pass


        return None  # TODO : implement check

    def load_module(self, fullname):

        if fullname in sys.modules:
            self.logger.debug('reusing existing module from previous import of "%s"' % fullname)
            mod = sys.modules[fullname]
        else:
            self.logger.debug('creating a new module object for "%s"' % fullname)
            mod = sys.modules.setdefault(fullname, imp.new_module(fullname))

        # Set a few properties required by PEP 302
        mod.__file__ = self._get_filename(fullname)
        mod.__name__ = fullname
        mod.__path__ = self.path_entry
        mod.__loader__ = self
        mod.__package__ = '.'.join(fullname.split('.')[:-1])

        if self.is_package(fullname):
            self.logger.debug('adding path for package')
            # Set __path__ for packages
            # so we can find the sub-modules.
            mod.__path__ = [self.path_entry]
        else:
            self.logger.debug('imported as regular module')

        source = self.get_source(fullname)

        self.logger.debug('execing source...')
        exec(source, mod.__dict__)
        self.logger.debug('done')
        return mod

# https://pymotw.com/3/sys/imports.html#sys-imports

# class NoisyImportFinder:
#
#     PATH_TRIGGER = 'NoisyImportFinder_PATH_TRIGGER'
#
#     def __init__(self, path_entry):
#         print('Checking {}:'.format(path_entry), end=' ')
#         if path_entry != self.PATH_TRIGGER:
#             print('wrong finder')
#             raise ImportError()
#         else:
#             print('works')
#         return
#
#     def find_module(self, fullname, path=None):
#         print('Looking for {!r}'.format(fullname))
#         return None
#
#
# sys.path_hooks.append(NoisyImportFinder)





if sys.version_info >= (3, 5):

    import importlib.abc

    class ROSImportFinder(object):  #importlib.abc.PathEntryFinder):
        # TODO : we can use this to enable ROS Finder only on relevant paths (ros distro paths + dev workspaces) from sys.path

        def __init__(self, path_entry):

            super(ROSImportFinder, self).__init__()

            # First we need to skip all the cases that we are not concerned with

            # if path_entry != self.PATH_TRIGGER:
            #     self.logger.debug('ROSImportFinder does not work for %s' % path_entry)
            #     raise ImportError()

            # path_entry contains the path where the finder has been instantiated...
            if not os.path.exists(os.path.join(path_entry, 'msg')) and not os.path.exists(os.path.join(path_entry, 'srv')):
                raise ImportError  # we raise if we cannot find msg or srv folder

            # Then we can do the initialisation
            self.logger = logging.getLogger(__name__)
            self.logger.debug('Checking ROSImportFinder support for %s' % path_entry)

            self.path_entry = path_entry


        def find_spec(self, fullname, target = None):
            print('ROSImportFinder looking for "%s"' % fullname)
            return None

        def find_module(self, fullname, path=None):
            print('ROSImportFinder looking for "%s"' % fullname)
            return None


# elif sys.version_info >= (2, 7, 12):
#     class ROSImportFinder(object):
#         PATH_TRIGGER = 'ROSFinder_PATH_TRIGGER'
#
#         def __init__(self, path_entry):
#             self.logger = logging.getLogger(__name__)
#             self.logger.debug('Checking ROSImportFinder support for %s' % path_entry)
#             if path_entry != self.PATH_TRIGGER:
#                 self.logger.debug('ROSImportFinder does not work for %s' % path_entry)
#                 raise ImportError()
#
#             self.loaders = {
#                 '.srv': ROSLoader(genpy.generator.SrvGenerator(), 'srv'),
#                 '.msg': ROSLoader(genpy.generator.MsgGenerator(), 'msg')
#             }
#
#         def find_module(self, fullname, path=None):
#             print('ROSImportFinder looking for "%s"' % fullname)
#             return None

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

#_ros_finder_instance_obsolete_python = ROSImportFinder


def activate():
    #if sys.version_info >= (2, 7, 12):  # TODO : which exact version matters ?
    sys.path_hooks.append(ROSImportFinder)

    # else:  # older (trusty) version
    #     sys.path_hooks.append(_ros_finder_instance_obsolete_python)

    for hook in sys.path_hooks:
        print('Path hook: {}'.format(hook))


def deactivate():
    #if sys.version_info >= (2, 7, 12):  # TODO : which exact version matters ?
    sys.path_hooks.remove(ROSImportFinder)
    # else:  # older (trusty) version
    #     sys.path_hooks.remove(_ros_finder_instance_obsolete_python)


# TODO : a meta finder could find a full ROS distro...
