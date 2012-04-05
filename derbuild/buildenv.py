import logging
import tarfile
import os
import os.path

from derbuild.utils import call

LOG = logging.getLogger(__name__)

ARCH_QEMU_MAP = {
    "armel": "qemu-arm"
}

class BuildEnvironment(object):
    """Build environment."""

    def __init__(self, arch, rootdir):
        """Constructor."""

        self.rootdir = rootdir
        self.arch    = arch

    def setup(self, rootstrap=None):
        """Set up environment."""

        LOG.debug("rootdir: %s" % self.rootdir)
        if not os.path.isdir(self.rootdir):
            os.makedirs(self.rootdir)

        if rootstrap:
            tgz = tarfile.open(rootstrap)
            tgz.extractall(path=self.rootdir)
            tgz.close()

    def execute(self, cmd, cwd):
        """Execute given command inside environment."""

        fullcmd = "proot -Q %(qemu)s -w %(cwd)s %(rootdir)s %(cmd)s" % {
            "qemu": ARCH_QEMU_MAP[self.arch],
            "rootdir": self.rootdir,
            "cwd": cwd,
            "cmd": cmd
        }
        LOG.debug("Executing `%s` inside env" % fullcmd)
        call(fullcmd.split())
