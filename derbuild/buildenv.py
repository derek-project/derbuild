import logging
import tarfile
import os
import os.path

LOG = logging.getLogger(__name__)

class BuildEnvironment(object):
    """Build environment."""

    def __init__(self, rootdir):
        """Constructor."""

        self.rootdir = rootdir

    def setup(self, rootstrap=None):
        """Set up environment."""

        LOG.debug("rootdir: %s" % self.rootdir)
        if not os.path.isdir(self.rootdir):
            os.makedirs(self.rootdir)

        if rootstrap:
            with tarfile.open(rootstrap) as tgz:
                tgz.extractall(path=self.rootdir)
