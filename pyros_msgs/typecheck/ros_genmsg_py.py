from __future__ import absolute_import, division, print_function

import os
import sys
import traceback
import importlib


# This will take the ROS distro version if ros has been setup
import genpy.generator
import genpy.generate_initpy

import genmsg
import genmsg.command_line

import rospkg


# TODO : integrate all that in pyros_setup
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
        genpy.generate_initpy.write_modules(outdir)
        genlist.add(os.path.join(outdir, '__init__.py'))

    return genlist


def genmsgsrv_py(msgsrv_files, package, outdir, includepath=None, initpy=False):
    includepath = includepath or []

    try:
        genset = set()
        genset.update(genros_py(rosfiles=[f for f in msgsrv_files if f.endswith('.msg')],
                            generator=genpy.generator.MsgGenerator(),
                            package=package,
                            outdir=outdir,
                            includepath=includepath,
                            initpy=initpy))

        genset.update(genros_py(rosfiles=[f for f in msgsrv_files if f.endswith('.srv')],
                            generator=genpy.generator.SrvGenerator(),
                            package=package,
                            outdir=outdir,
                            includepath=includepath,
                            initpy=initpy))

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


def import_msgsrv(msgsrvfile, package=None, dependencies=None):
    # by default we add to current package (careful : it might still be None)
    package = package or __package__

    # by default we have no dependencies
    dependencies = dependencies or []

    include_path = []
    for d in dependencies:
        # get an instance of RosPack with the default search paths
        rospack = rospkg.RosPack()
        # get the file path for a dependency
        dpath = rospack.get_path(d)
        # we populate include_path
        include_path.append('{d}:{dpath}/msg'.format(**locals()))

    if msgsrvfile.endswith(('.msg', '.srv')):
        msgsrv_pkg = (package + '.gen') if package else 'gen'
        outdir_pkg = (package.__path__ if package and hasattr(package, '__path__') else '') + 'gen'

        print("genmsgsrv_py(msgsrv_files=[{msgsrvfile}], package={msgsrv_pkg}, outdir={outdir_pkg}, includepath={include_path}, initpy=True)".format(**locals()))
        gen_modules = genmsgsrv_py(msgsrv_files=[msgsrvfile], package=msgsrv_pkg, outdir=outdir_pkg, includepath=include_path, initpy=True)
        print(gen_modules)
        for m in gen_modules:
            if m.endswith('.__init__'):  # thisis the package __init__, we should import it
                mod_name = m[:-len('.__init__')]
                if mod_name in sys.modules:
                    # we need to force the reload in case we already have that module loaded (without the newest message)
                    # TODO : handle python >= 3.4 with importlib.reload()
                    mod = reload(sys.modules.get(mod_name))
                else:
                    mod = importlib.import_module(mod_name)
                class_name = os.path.basename(msgsrvfile)[:-4]
                #print(vars(mod))
                print(class_name)
                if hasattr(mod, class_name):
                    return getattr(mod, class_name)
                else:
                    raise ImportError("GENERATED module {class_name} not found in package {mod}".format(**locals()))
        # TODO : doublecheck and fix that API to return the same thing as importlib.import_module returns, for consistency,...
    else:
        raise ImportError("{msgsrvfile} doesnt have the proper .msg or .srv extension.")


