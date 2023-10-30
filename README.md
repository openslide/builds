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

The Windows builds are run inside a [builder container][container-windows],
which is periodically [rebuilt][workflow-container-windows] by the
[openslide-winbuild][openslide-winbuild] repo.

[builds]: https://openslide.org/builds/
[container-windows]: https://github.com/openslide/openslide-winbuild/pkgs/container/winbuild-builder
[openslide-winbuild]: https://github.com/openslide/openslide-winbuild
[releases]: https://github.com/openslide/builds/releases/
[workflow]: https://github.com/openslide/builds/actions/workflows/build.yml
[workflow-container-windows]: https://github.com/openslide/openslide-winbuild/actions/workflows/container-windows.yml
