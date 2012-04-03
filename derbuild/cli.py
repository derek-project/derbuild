import sys
import os.path
import mimetypes
import logging, logging.config

from optparse import OptionParser
from pkg_resources import iter_entry_points
from ConfigParser import SafeConfigParser as ConfigParser, NoSectionError, \
        NoOptionError

from derbuild import DerbuildError

LOG = logging.getLogger(__name__)

DERBUILD_SECTION = "derbuild"

LOGCONFIG_OPT = "logconfig"
WORKDIR_OPT   = "workdir"

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
    parser.add_option("-w", "--workdir", dest=WORKDIR_OPT,
                      help="path to working directory where to unpack source "
                           "package")
    parser.add_option("-L", "--log-config", dest=LOGCONFIG_OPT,
                      help="path to logger config file")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
                      help="show debug output")

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

def get_source_package(ptype, path, workdir):
    """Return source package object."""

    if not os.path.exists(path):
        raise DerbuildError("No such file: %s" % path)

    # Detect the type of the package
    if ptype != 'auto':
        mimetp = TYPEMAP[ptype]
    else:
        init_mimetypes()
        mimetp, _ = mimetypes.guess_type(path)

    srcpkg = None
    for entry in iter_entry_points(group='srcpkgs', name=mimetp):
        LOG.debug("found entry %r" % entry)
        cls = entry.load()
        srcpkg = cls(path=path, workdir=workdir)
        break
    if not srcpkg:
        LOG.error("no handler found for the type '%s'" % mimetp)
        sys.exit(1)
    return srcpkg

def main():
    """Entry point."""

    logconfig = None
    options, overrides, srcpkg_path = parse_cmdline()

    if os.path.exists(options.config):
        config = ConfigParser()
        config.read(options.config)
        if not config.has_section(DERBUILD_SECTION):
            config.add_section(DERBUILD_SECTION)
        try:
            logconfig = config.get(DERBUILD_SECTION, LOGCONFIG_OPT,
                                   vars=overrides)
        except NoOptionError:
            if config.has_section("loggers"):
                logconfig = config.config

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

    # TODO: unify getting option values
    try:
        workdir = config.get(DERBUILD_SECTION, WORKDIR_OPT, vars=overrides)
    except NoOptionError:
        workdir = "."

    srcpkg = get_source_package(options.type, srcpkg_path, workdir)

    srcpkg.unpack()
