import logging
import tarfile
import os
import shutil
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

    def setup(self, rootstrap=None, overrides=None):
        """Set up environment."""

        def env_members(members):
            for tarinfo in members:
                if tarinfo.isdev():
                    continue
                yield tarinfo

        LOG.debug("rootdir: %s" % self.rootdir)
        if os.path.isdir(self.rootdir):
            shutil.rmtree(self.rootdir)
        os.makedirs(self.rootdir)

        if rootstrap:
            tgz = tarfile.open(rootstrap, 'r|*')
            tgz.extractall(path=self.rootdir, members=env_members(tgz))
            tgz.close()

        if overrides:
            if not overrides.endswith("/"):
                overrides = overrides + "/"
            for root, _, files in os.walk(overrides):
                reldir = root.split(overrides)[1]
                targetdir = os.path.join(self.rootdir, reldir)
                if not os.path.isdir(targetdir):
                    os.makedirs(targetdir)
                for fname in files:
                    shutil.copyfile(os.path.join(root, fname),
                                    os.path.join(targetdir, fname))

    def execute(self, cmd, cwd):
        """Execute given command inside environment."""

        fullcmd = "proot -Q %(qemu)s -b /usr/bin/m4 -b /opt -w %(cwd)s %(rootdir)s %(cmd)s" % {
            "qemu": ARCH_QEMU_MAP[self.arch],
            "rootdir": self.rootdir,
            "cwd": cwd,
            "cmd": cmd
        }
        LOG.debug("Executing `%s` inside env" % fullcmd)
        env = os.environ
        env['LANG'] = 'C'
        env['CC'] = '/opt/arm-2011.09-gnueabi/bin/arm-none-linux-gnueabi-gcc'
        call(fullcmd.split(), env=env)
