# OpenSlide nightly builds

This repo contains [nightly builds of OpenSlide][builds].

## Implementation notes

The [builds][workflow] are run in GitHub Actions.  The artifacts are hosted
in [GitHub releases][releases] in this repo, and the [index][builds] is
deployed to GitHub Pages from the [site](site) directory of this branch.
GitHub embeds this repo's Pages site into the main OpenSlide website at
[openslide.org/builds](https://openslide.org/builds/), so the name of this
repository directly affects the layout of the OpenSlide site.

The Windows builds are run inside a [builder container][container-windows],
which is periodically [rebuilt][workflow-container-windows] by the
[openslide-bin][openslide-bin] repo.

[builds]: https://openslide.org/builds/
[container-windows]: https://github.com/openslide/openslide-bin/pkgs/container/winbuild-builder
[openslide-bin]: https://github.com/openslide/openslide-bin
[releases]: https://github.com/openslide/builds/releases/
[workflow]: https://github.com/openslide/builds/actions/workflows/build.yml
[workflow-container-windows]: https://github.com/openslide/openslide-bin/actions/workflows/container-windows.yml
