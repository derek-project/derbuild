Purpose
=======

We need to have a simple tool to build binary packages from sources for
different package management systems and for architectures that can differ from
our host architecture. Ideally the tool should be package management system
agnostic that is support for new systems can be developed by third parties and
can be easily plugged in.

Design
======

Currently Derbuild consists of two major abstractions:

 - build environment isolated from host environment,
 - package.

Build environment
-----------------

The abstracted build environment knows how to set up itself, how to execute
programs inside itself and how to destroy itself. This abstraction is
represented by the class `derbuild.buildenv.BuildEnvironment` which
incapsulates all this knowledge and exposes its functionality through the
public methods :meth:`derbuild.buildenv.BuildEnvironment.setup()`,
:meth:`derbuild.buildenv.BuildEnvironment.execute()` and
:meth:`derbuild.buildenv.BuildEnvironment.destroy()`.

The build environment knows nothing about package management systems.

Current implementation uses the `PRoot`_ utility to emulate a build environment
which is isolated from the host environment and potentially runs on different
architecture. But technically this abstraction might be implemented to use
Scratchbox2 or something else instead of PRoot thus it makes sense to
make the actual implementation pluggable in future.

Package
-------

The abstracted package knows how to transform given source packages to binary
packages inside a given build environment (thus it'll be renamed to something
like "package builder" eventually). This abstraction exposes three methods:

 - unpack() preparing sources for build,
 - build() and
 - get_artifacts() used to get built binaries from the build environment
   to the host environment.

The most important is build(). This method not only tries to build binaries,
but adjusts the build environment - installs build dependencies if needed.

Actual implementation is specific to the used package management system thus
the `derbuild` application loads the code from a plugin corresponding to the
type of a source package to be built. The application uses the standard
library `mimetypes` to define the type of a source package.

Bootstrapping
-------------

Currently the bootstrap method for build enviroments is to unpack an existing
rootstrap and (optionally) modify some files in the unpacked file tree.
Further adjustments (fetching and installing build dependencies) burden the
Package classes.

But the requirement of a pre-existing rootstrap complicates the overall setup
because the rootstraps need to be updated constantly to reflect changes in
the target package repository. And these updates can't be controlled by
derbuild. So it might be beneficial to borrow the idea of a rootstrap-less
bootstrapping method from OpenSUSE's `build`_ utility. This would require a new
abstraction - a bootstrap method - incapsulating fetching from a repo,
unpacking and setting up base packages and build dependencies in one go.

The most appropriate place for this method is the pluggable Package classes. And
the method `BuildEnvironment.setup()` should contain only the code handling
optional overrides modifying already bootstrapped file tree.

.. _PRoot: http://proot.me
.. _build: http://cgit.sugarlabs.org/0sugar/build.git/
