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

    def __init__(self, arch, rootdir, envvars=None, binds=None):
        """Constructor."""

        if envvars is None:
            envvars = {}
        if binds is None:
            binds = []

        self.rootdir = rootdir
        self.arch    = arch
        self.envvars = envvars
        self.binds   = binds

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

        bind_opts = " ".join(["-b %s" % bind for bind in self.binds])
        fullcmd = "proot -Q %(qemu)s %(binds)s -w %(cwd)s %(rootdir)s " \
                  "%(cmd)s" % \
                {
                    "qemu": ARCH_QEMU_MAP[self.arch],
                    "rootdir": self.rootdir,
                    "cwd": cwd,
                    "cmd": cmd,
                    "binds": bind_opts
                }
        LOG.debug("Executing `%s` inside env" % fullcmd)
        env = os.environ
        env.update(self.envvars)
        call(fullcmd, env=env, shell=True)

    def destroy(self):
        """Do clean up."""

        LOG.debug("removing the rootfs directory '%s'" % self.rootdir)
        shutil.rmtree(self.rootdir)
