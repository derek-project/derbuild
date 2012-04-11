import sys
import os.path
import mimetypes
import shutil
import logging, logging.config

from optparse import OptionParser
from pkg_resources import iter_entry_points
from ConfigParser import SafeConfigParser as ConfigParser, NoSectionError, \
        NoOptionError

from derbuild import DerbuildError
from derbuild.buildenv import BuildEnvironment

LOG = logging.getLogger(__name__)

DERBUILD_SECTION = "derbuild"

LOGCONFIG_OPT = "logconfig"
WORKDIR_OPT   = "workdir"
ROOTDIR_OPT   = "rootdir"
ROOTSTRAP_OPT = "rootstrap"
ARCH_OPT      = "arch"
OVERDIR_OPT   = "overdir"
ENVIRON_OPT   = "envvars"
BINDS_OPT      = "binds"
OUTDIR_OPT    = "outdir"

PKG_DEB = "deb"

TYPEMAP = {PKG_DEB: 'application/x-debian-sources-descriptor'}

def parse_cmdline():
    """Parse command line options."""

    usage = "usage: %prog [options] path/to/source/package"
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--config", dest="config",
                      default="/etc/derbuild/config.ini",
                      help="path to config file")
    parser.add_option("-t", "--type", dest="type", default="auto",
                      choices=["auto", PKG_DEB],
                      help="type of packaging")
    parser.add_option("-a", "--arch", dest=ARCH_OPT,
                      help="target architecture")
    parser.add_option("-w", "--workdir", dest=WORKDIR_OPT,
                      help="path to working directory where to unpack source "
                           "package")
    parser.add_option("-L", "--log-config", dest=LOGCONFIG_OPT,
                      help="path to logger config file")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
                      help="show debug output")
    parser.add_option("-R", "--rootdir", dest=ROOTDIR_OPT,
                      help="path proot's root")
    parser.add_option("-r", "--rootstrap", dest=ROOTSTRAP_OPT,
                      help="URI to rootstrap tarball")
    parser.add_option("-O", "--overdir", dest=OVERDIR_OPT,
                      help="path to file system tree with files to override")
    parser.add_option("-e", "--environment", dest=ENVIRON_OPT,
                      help="comma-separated list of environment variables to be"
                           " used inside build environment")
    parser.add_option("-b", "--bind", dest=BINDS_OPT, action="append",
                      default=[],
                      help="path on host system to make accessible inside "
                           "build environment")
    parser.add_option("-o", "--outdir", dest=OUTDIR_OPT,
                      help="directory where to put built artifacts")

    try:
        options, [srcpkg_path] = parser.parse_args()
    except ValueError:
        print "ERROR: wrong command\n"
        parser.print_help()
        sys.exit(1)

    opt_dict = dict([(opt, options.__dict__[opt])
                     for opt in options.__dict__ if options.__dict__[opt]])

    return options, opt_dict, srcpkg_path

def init_mimetypes():
    """Register known file types."""
    mimetypes.init()
    mimetypes.add_type('application/x-debian-source-control', '.dsc')

def get_package(ptype, path, workdir, env):
    """Return source package object."""

    if not os.path.exists(path):
        raise DerbuildError("No such file: %s" % path)

    # Detect the type of the package
    if ptype != 'auto':
        mimetp = TYPEMAP[ptype]
    else:
        init_mimetypes()
        mimetp, _ = mimetypes.guess_type(path)

    pkg = None
    for entry in iter_entry_points(group='srcpkgs', name=mimetp):
        LOG.debug("found entry %r" % entry)
        cls = entry.load()
        pkg = cls(path=path, workdir=workdir, env=env)
        break
    if not pkg:
        LOG.error("no handler found for the type '%s'" % mimetp)
        sys.exit(1)
    return pkg

def parse_vars(vars_str):
    """Parse string with list of variables."""
    return dict([[token.strip() for token in var.split("=")]
                                for var in vars_str.split(",")])

def main():
    """Entry point."""

    # 1. Configure

    logconfig = None
    options, overrides, srcpkg_path = parse_cmdline()

    config = ConfigParser()
    if os.path.exists(options.config):
        config.read(options.config)
        if not config.has_section(DERBUILD_SECTION):
            config.add_section(DERBUILD_SECTION)
        try:
            logconfig = config.get(DERBUILD_SECTION, LOGCONFIG_OPT,
                                   vars=overrides)
        except NoOptionError:
            if config.has_section("loggers"):
                logconfig = config.config
    else:
        config.add_section(DERBUILD_SECTION)

    # Initialize logging:
    # 1. try to find settings for logging
    #   * in the command line option '--log-config' first,
    #   * then in option 'logconfig' in the section [derbuild] of
    #     derbuild's config file,
    #   * then in derbuild's config file itself
    # 2. if logging settings have been found then load them
    # 3. otherwise initialize logging with standard basic settings.
    if logconfig:
        logging.config.fileConfig(logconfig, disable_existing_loggers=False)
        if option.debug:
            rootlogger = logging.getLogger()
            rootlogger.setLevel(logging.DEBUG)
    else:
        if options.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)
    LOG.debug("logging initialized")

    # TODO: unify getting option values. Move it to get_effective_options()
    try:
        workdir = config.get(DERBUILD_SECTION, WORKDIR_OPT, vars=overrides)
    except NoOptionError:
        LOG.error("No working directory specified. Exiting...")
        sys.exit(1)

    try:
        rootdir = config.get(DERBUILD_SECTION, ROOTDIR_OPT, vars=overrides)
    except NoOptionError:
        rootdir = "."

    try:
        outdir = config.get(DERBUILD_SECTION, OUTDIR_OPT, vars=overrides)
    except NoOptionError:
        outdir = "."

    try:
        rootstrap = config.get(DERBUILD_SECTION, ROOTSTRAP_OPT, vars=overrides)
    except NoOptionError:
        LOG.error("No rootstrap specified. Exiting...")
        sys.exit(1)

    try:
        arch = config.get(DERBUILD_SECTION, ARCH_OPT, vars=overrides)
    except NoOptionError:
        LOG.error("No target architecture specified. Exiting...")
        sys.exit(1)

    try:
        overdir = config.get(DERBUILD_SECTION, OVERDIR_OPT, vars=overrides)
    except NoOptionError:
        overdir = None

    try:
        envvars = parse_vars(config.get(DERBUILD_SECTION, ENVIRON_OPT))
    except NoOptionError:
        envvars = {}
    if ENVIRON_OPT in overrides.keys():
        cmdenvvars = parse_vars(overrides[ENVIRON_OPT])
    else:
        cmdenvvars = {}
    envvars.update(cmdenvvars)
    LOG.debug("effective environment variables: %r" % envvars)

    try:
        binds = [bind.strip() for bind in
                         config.get(DERBUILD_SECTION, BINDS_OPT).split(",")]
    except NoOptionError:
        binds = []
    binds.extend(options.binds)
    binds.append(workdir)

    # 2. Set up

    # prepare working directory
    if os.path.exists(workdir):
        LOG.error("working directory '%s' exists already. Exiting..." % workdir)
        sys.exit(1)
    os.makedirs(workdir)

    # prepare output directory
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    env = BuildEnvironment(arch, rootdir, envvars, binds)
    env.setup(rootstrap, overdir)

    pkg = get_package(options.type, srcpkg_path, workdir, env)

    # 3. Build

    pkg.unpack()
    pkg.build()
    pkg.get_artifacts(outdir)

    # 4. Clean up

    env.destroy()
    shutil.rmtree(workdir)
