import logging
import shutil
import os, os.path

LOG = logging.getLogger(__name__)

class RpmPackage(object):
    """RPM package."""

    def __init__(self, path, workdir, env):
        """Constructor."""

        self.srcrpm_path = path
        self.workdir     = workdir
        self.env         = env

    def unpack(self):
        """Create build tree in working directory."""
        LOG.debug("unpack")

    def build(self):
        """Build package."""

        LOG.debug("build")
        self.env.execute("fakeroot rpmbuild --define='%_topdir %s' "
                         "--rebuild %s" % (self.workdir, self.srcrpm_path))

    def get_artifacts(self, outdir):
        """Copy built artifacts to given output directory."""

        rpmsdir = os.path.join(self.workdir, "RPMS")
        artifacts = [os.path.join(rpmsdir, fname)
                     for fname in os.listdir(rpmsdir)
                     if os.path.isfile(os.path.join(rpmsdir, fname))]
        for artifact in artifacts:
            shutil.copy(artifact, outdir)
