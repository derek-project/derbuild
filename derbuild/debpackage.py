import logging
import email

from derbuild import DerbuildError

LOG = logging.getLogger(__name__)

class DebPackage(object):
    """Debian package."""

    def __init__(self, path, workdir):
        """Constructor."""

        self.dsc_path = path
        self.workdir = workdir
        with open(path) as dsc_h:
            dsc = email.message_from_file(dsc_h)
        self.name = dsc['source']
        self.version = dsc['version']
        self.binaries = [b.strip() for b in dsc['binary'].split(',')]
        self.depends = [dep.split(' ', 1)[0].strip()
                        for dep in dsc['build-depends'].split(',')]

    def unpack(self):
        """Create build tree in working directory."""
        pass
