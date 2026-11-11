<!-- vale off -->

## Provenance

The USGS produces the Landsat Collection 2 Level-2 surface temperature scenes that these composites read, and distributes them through [LandsatLook](https://landsatlook.usgs.gov/stac-server). The compositing is ours: every numeric rule, and every run that wrote a tile, lives in [landsat-lst-smoke](https://github.com/nlebovits/landsat-lst-smoke). [Source Cooperative](https://source.coop/) hosts the published result. Each item's `processing:lineage` records the rules that produced its pixels and names every input artifact by checksum, so a tile can be traced back to the scenes and the ancillary rasters it was built from.

<!-- vale on -->
