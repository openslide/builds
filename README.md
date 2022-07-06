# OpenSlide nightly builds

This repo contains [nightly builds of OpenSlide][builds], currently only for
Windows.

## Implementation notes

The [builds][workflow] are run in GitHub Actions.  The artifacts are hosted
in [GitHub releases][releases] in this repo, and the [index][builds] is
hosted in GitHub Pages from the [docs](docs) directory of this branch.
GitHub embeds this repo's Pages site into the main OpenSlide website at
[openslide.org/builds](https://openslide.org/builds/), so the name of this
repository directly affects the layout of the OpenSlide site.

The Windows builds are run inside a [builder container][container].  Once a
week, this repo runs a [workflow][workflow-container] to rebuild the
container.

[builds]: https://openslide.org/builds/windows/
[container]: https://github.com/openslide/openslide-winbuild/pkgs/container/winbuild-builder
[releases]: https://github.com/openslide/builds/releases/
[workflow]: https://github.com/openslide/builds/actions/workflows/winbuild.yml
[workflow-container]: https://github.com/openslide/builds/actions/workflows/winbuild-container.yml
