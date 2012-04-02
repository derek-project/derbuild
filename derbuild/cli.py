import sys
import os.path
import mimetypes
import logging, logging.config

from optparse import OptionParser
from pkg_resources import iter_entry_points
from ConfigParser import SafeConfigParser as ConfigParser, NoSectionError

LOG = logging.getLogger(__name__)

DERBUILD_SECTION = "derbuild"

LOGCONFIG_OPT = "logconfig"

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
    parser.add_option("-L", "--log-config", dest="logconfig",
                      help="path to logger config file")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
                      help="show debug output")

    try:
        options, [srcpkg_path] = parser.parse_args()
    except ValueError:
        print "ERROR: wrong command\n"
        parser.print_help()
        sys.exit(1)

    opt_dict = {}
    if options.logconfig:
        opt_dict[LOGCONFIG_OPT] = options.logconfig

    return options, opt_dict, srcpkg_path

def init_mimetypes():
    """Register known file types."""
    mimetypes.init()
    mimetypes.add_type('application/x-debian-sources-descriptor', '.dsc')

def main():
    """Entry point."""

    logconfig = None
    options, overrides, srcpkg_path = parse_cmdline()

    if os.path.exists(options.config):
        config = ConfigParser()
        config.read(options.config)
        try:
            logconfig = config.get(DERBUILD_SECTION, LOGCONFIG_OPT,
                                   vars=overrides)
        except NoSectionError:
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

    # Detect the type of the package
    if options.type != 'auto':
        pkgtype = TYPEMAP[options.type]
    else:
        init_mimetypes()
        pkgtype, _ = mimetypes.guess_type(srcpkg_path)

    # Load handler for the source package
    srcpkg = None
    for entry in iter_entry_points(group='srcpkgs', name=pkgtype):
        LOG.debug("found entry %r" % entry)
        cls = entry.load()
        srcpkg = cls()
        break
    if not srcpkg:
        LOG.error("no handler found for the type '%s'" % pkgtype)
        sys.exit(1)
