# Changelog

This file follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The release workflow runs commitizen, which writes each new release above the
previous one from the Conventional Commits merged since that release.

## Unreleased

## v0.1.0 (2026-11-11)

The first tagged release. It covers the pipeline that built the published
composite, the catalog that describes it, and the documentation site.

### Added

- A five-year 95th-percentile land surface temperature composite from Landsat
  Collection 2 Level-2 scenes, 2021 through 2025, on 5-degree tiles between
  60 degrees south and 60 degrees north.
- Scene normalization against a per-pixel monthly median, and a WRS-2 path
  blend that removes the seams where orbital paths overlap.
- The `fused` engine, which submits one task per block on a frisky cluster,
  as the default. The `graph` engine builds the same reduction as one lazy
  dask-xarray graph, and the tests assert that both write identical bytes.
- A precomputed Landsat scene inventory and an authoritative list of land
  tiles, with an ASTER GED observation-count raster and two land geometries
  for the output mask.
- An EC2 fleet that plans, launches, watches, verifies, and tears down a run
  over a tile set, with a cost report per run.
- The output as two cloud-optimized GeoTIFFs per tile, `lst_p95` and
  `qa_count`, in a Portolan catalog on
  [Source Cooperative](https://source.coop/nlebovits/landsat-lst).
- A git-backed catalog: the metadata under `catalog/` is the source of truth
  for the bucket, and CI validates each change to it.
- CI that runs every documented Python example against the published catalog.
- A documentation site built with Quarto and published to GitHub Pages, with
  a quickstart, a tutorial, an examples gallery, and the governance files.
- Prose rules enforced by Vale, Conventional Commits enforced by commitizen,
  and a release workflow that tags each version and writes this file.

### Changed

- The repository became one installed package, `lst`, with console scripts
  for every command and import contracts between its layers.
- Each published share of land divides by the unbuffered land geometry
  rather than the 25 km processing buffer.
- Each tile's coverage figures moved onto its STAC item and into the
  collection README.

### Fixed

- The composite no longer publishes a land temperature over water.
- The output mask removes the pixels that ASTER GED gaps spoil, rather than
  every cell that ASTER GED missed.
- A pixel with fewer than five valid observations in the five years reports
  nodata instead of a percentile it cannot support.
- Staging fetches each scene object once, where it had fetched the same
  object up to 155 times.
