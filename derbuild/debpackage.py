import logging
import deb822

from derbuild import DerbuildError
from derbuild.utils import call

LOG = logging.getLogger(__name__)

class DebPackage(object):
    """Debian package."""

    def __init__(self, path, workdir):
        """Constructor."""

        self.dsc_path = path
        self.workdir = workdir
        with open(path) as dsc_h:
            dsc = deb822.Dsc(dsc_h)
        self.name = dsc['source']
        self.version = dsc['version']
        self.binaries = [b.strip() for b in dsc['binary'].split(',')]
        self.depends = [dep.split()[0].strip()
                        for dep in dsc['build-depends'].split(',')]

    def unpack(self):
        """Create build tree in working directory."""

        LOG.debug("unpack")
        call(["dpkg-source", "-x", self.dsc_path], cwd=self.workdir)
