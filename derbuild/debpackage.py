import logging
import deb822
import os.path

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

    @property
    def version_without_epoch(self):
        """Return version without epoch."""

        try:
            _, ver = self.version.split(':')
        except ValueError:
            ver = self.version

        return ver

    @property
    def version_upstream(self):
        """Return upstream version."""
        return "-".join(self.version_without_epoch.split('-')[:-1])

    def unpack(self):
        """Create build tree in working directory."""

        LOG.debug("unpack")
        call(["dpkg-source", "-x", self.dsc_path], cwd=self.workdir)

    def build(self):
        """Build package."""

        LOG.debug("build")
        builddir = os.path.join(self.workdir, "%s-%s" %
                                             (self.name, self.version_upstream))
        call(["dpkg-buildpackage", "-rfakeroot"], cwd=builddir)