from __future__ import absolute_import, division, print_function

import os
import sys
import traceback
import importlib

"""
Module that can be used standalone, or as part of the pyros_msgs.importer package

It provides a set of functions to generate your ros messages, even when ROS is not installed on your system.
You might however need to have dependent messages definitions reachable by rospack somewhere.
"""

try:
    # Using genpy and genmsg directly if ROS has been setup (while using from ROS pkg)
    import genmsg as genmsg
    import genmsg.command_line as genmsg_command_line
    import genpy.generator as genpy_generator
    import genpy.generate_initpy as genpy_generate_initpy

except ImportError:

    # Otherwise we refer to our submodules here (setup.py usecase, or running from tox without site-packages)

    import site
    site.addsitedir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ros-site'))

    import genmsg as genmsg
    import genmsg.command_line as genmsg_command_line
    import genpy.generator as genpy_generator
    import genpy.generate_initpy as genpy_generate_initpy

    # Note we do not want to use pyros_setup here.
    # We do not want to do a full ROS setup, only import specific packages.
    # If needed it should have been done before (loading a parent package).
    # this handle the case where we want to be independent of any underlying ROS system.


class MsgDependencyNotFound(Exception):
    pass


def genros_py(rosfiles, generator, package, outdir, includepath=None, initpy=False):
    includepath = includepath or []

    if not os.path.exists(outdir):
        # This script can be run multiple times in parallel. We
        # don't mind if the makedirs call fails because somebody
        # else snuck in and created the directory before us.
        try:
            os.makedirs(outdir)
        except OSError as e:
            if not os.path.exists(outdir):
                raise
    # TODO : maybe we dont need this, and that translation should be handled before ?
    search_path = genmsg.command_line.includepath_to_dict(includepath)
    generator.generate_messages(package, rosfiles, outdir, search_path)

    genlist = set()
    for f in rosfiles:
        f, _ = os.path.splitext(f)  # removing extension
        genlist.add(os.path.join(outdir, '_' + os.path.basename(f) + '.py'))

    # optionally we can generate __init__.py
    if initpy:
        genpy_generate_initpy.write_modules(outdir)
        genlist.add(os.path.join(outdir, '__init__.py'))

    return genlist


def genmsgsrv_py(msgsrv_files, package, outdir_pkg, includepath=None, initpy=False):
    includepath = includepath or []

    # checking if we have files with unknown extension to except early
    for f in msgsrv_files:
        if not f.endswith(('.msg', '.srv')):
            print("WARNING: {f} doesnt have the proper .msg or .srv extension. It has been Ignored.".format(**locals()), file=sys.stderr)

    try:
        genset = set()
        genset.update(genros_py(rosfiles=[f for f in msgsrv_files if f.endswith('.msg')],
                            generator=genpy_generator.MsgGenerator(),
                            package=package,
                            outdir=os.path.join(outdir_pkg, 'msg'),
                            includepath=includepath,
                            initpy=initpy))
        # because the OS interface might not be synchronous....
        while not os.path.exists(os.path.join(outdir_pkg, 'msg')):
            time.sleep(.1)

        genset.update(genros_py(rosfiles=[f for f in msgsrv_files if f.endswith('.srv')],
                            generator=genpy_generator.SrvGenerator(),
                            package=package,
                            outdir=os.path.join(outdir_pkg, 'srv'),
                            includepath=includepath,
                            initpy=initpy))
        # because the OS interface might not be synchronous....
        while not os.path.exists(os.path.join(outdir_pkg, 'srv')):
            time.sleep(.1)

    except genmsg.InvalidMsgSpec as e:
        print("ERROR: ", e, file=sys.stderr)
        raise
    except genmsg.MsgGenerationException as e:
        print("ERROR: ", e, file=sys.stderr)
        raise
    except Exception as e:
        traceback.print_exc()
        print("ERROR: ", e)
        raise

    modlist = []
    for f in genset:
        if f.endswith('.py'):
            f = f[:-3]
        modlist.append(".".join(f.split(os.sep)))

    return modlist


def clean_generated_py(path):
    filelist = [f for f in os.listdir(path) if f.endswith('.py')]
    for f in filelist:
        os.remove(os.path.join(path, f))


def generate_msgsrv_nspkg(msgsrvfiles, package=None, dependencies=None, include_path=None, outdir_pkg=None, initpy=True, ns_pkg=False):

    # by default we generate for this package (does it make sense ?)
    # Careful it might still be None
    package = package or 'gen_msgs'

    # by default we have no dependencies
    dependencies = dependencies or []

    # by default we create a relative directory to hold our package
    outdir_pkg = outdir_pkg or package

    include_path = include_path or []

    # we might need to resolve some dependencies
    unresolved_dependencies = [d for d in dependencies if d not in [p.split(':')[0] for p in include_path]]

    if unresolved_dependencies:
        # In that case we have no choice but to rely on ros packages (on the system)
        import rospkg

        # get an instance of RosPack with the default search paths
        rospack = rospkg.RosPack()
        for d in unresolved_dependencies:
            try:
                # get the file path for a dependency
                dpath = rospack.get_path(d)
                # we populate include_path
                include_path.append('{d}:{dpath}/msg'.format(**locals()))  # AFAIK only msg can be dependent msg types
            except rospkg.ResourceNotFound as rnf:
                raise MsgDependencyNotFound(rnf.message)

    print("genmsgsrv_py(msgsrv_files={msgsrvfiles}, package={package}, outdir_pkg={outdir_pkg}, includepath={include_path}, initpy={initpy})".format(**locals()))
    gen_modules = genmsgsrv_py(msgsrv_files=msgsrvfiles, package=package, outdir_pkg=outdir_pkg, includepath=include_path, initpy=initpy)
    print(gen_modules)

    if ns_pkg:
        nspkg_init_path = os.path.join(package, '__init__.py')
        with open(nspkg_init_path, "w") as nspkg_init:
            nspkg_init.writelines([
                "from __future__ import absolute_import, division, print_function\n",
                "# this is an autogenerated file for dynamic ROS message creation\n",
                "import pkg_resources\n",
                "pkg_resources.declare_namespace(__name__)\n",
                ""
            ])

        # because the OS interface might not be synchronous....
        while not os.path.exists(nspkg_init_path):
            time.sleep(.1)

    return [m[:-len('.__init__')] if m.endswith('.__init__') else m for m in gen_modules]

    # TODO : return something that can be imported later... with custom importer or following importlib API...


# This API is useful to import after a generation has been done with details.
# To blindly import a .msg file, use the custom importer instead
def import_msgsrv(msgsrv_module, package=None):

    mod = importlib.import_module(msgsrv_module, package)

    return mod
    # TODO : doublecheck and fix that API to return the same thing as importlib.import_module returns, for consistency,...

