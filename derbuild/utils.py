import logging

from subprocess import Popen, PIPE, STDOUT

from derbuild import DerbuildError

LOG = logging.getLogger(__name__)

def call(cmd, cwd=".", env=None):
    """Run command in a new process."""

    process = Popen(cmd, cwd=cwd, stdout=PIPE, stderr=STDOUT, env=env)
    while True:
        line = process.stdout.readline()
        LOG.info(line.strip('\n'))
        if line == '' and process.poll() is not None:
            break
    if process.returncode != 0:
        raise DerbuildError("The command '%s' returned non-zero code" %
                            " ".join(cmd))
