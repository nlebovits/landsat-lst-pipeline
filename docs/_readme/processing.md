<!-- vale off -->

## Data processing, storage, and access

### Processing

This dataset contains a five-year composite of 95th percentile land surface temperature values from Landsat 8/9 from 2021 through 2025. The choice of this metric was influenced by WRI's excellent work at the [Cool Cities Lab](https://coolcities.wri.org/). The data are global, excluding areas north and south of 60° latitude, which are basically unpopulated and would have increased processing and storage fees for minimal benefit. We've used standard QA masking (e.g., excluding clouds, cloud shadows, snow, ice), and also masked out pixels over water. In a handful of cases, we also filtered out physically implausible LST values (e.g., over 80°C, higher than the highest recorded LST temperature). Note that all of these are represented as nodata in the LST COG.

There are also notable gaps in some regions due to either known gaps in the ASTER coverage used by the USGS to produce LST estimates or, in some cases (mostly in the tropics), persistent cloud cover making it impossible to get reliable observations. We have not gap-filled these instances. (See [known issues](/about/known-issues.qmd) for more.)

We require at least five valid observations across the full 2021–2025 period for a pixel to receive an LST value. Pixels with fewer observations are reported as nodata. Because five observations is a permissive minimum, P95 values near this threshold are sensitive to individual observations. Users should consult the 12-band `qa_count` asset when assessing reliability, particularly in persistently cloudy regions.

The only modifications we made to the data were for the purposes of scene normalization and de-striping. We consider it very important that less technical users are presented with a product that looks visually plausible and is not covered in large, obvious jumps in temperature from one pixel to the next along, e.g., Landsat swaths. We found that this striping stemmed from two sources: atmospheric correction to Landsat scenes and overlapping swath boundaries producing more observations in some areas than others. To handle these, we applied two techniques.

#### Scene normalization

LST can shift from scene to scene because Landsat's atmospheric correction is not perfectly consistent. These shifts can make the surface appear artificially warmer or colder even when the underlying temperature pattern has not changed, and produce notable striping in the resulting image. We estimate and normalize this scene-level bias by comparing each valid pixel in a scene with that pixel's median temperature for the same calendar month across the five-year record. We take the scene-level median of those pixel-level differences to get a single offset, which we then subtract from every valid pixel in the scene. Because the same correction is applied across the scene, it changes individual, pixel-level LST values but preserves relative spatial differences within the scene.

#### Feathering

Pixels where Landsat orbital paths overlap have many more observations than pixels covered by only one path. Those extra observations can be meaningfully hotter or colder than the surrounding areas, which can appear as visible stripes. We address this by calculating P95 separately for each WRS path. Then, where paths overlap, we blend the two results together, weighted by distance from each path edge, so that pixels closer to the edge get less weight. This produces a smooth transition between the two path estimates. It changes values in overlap areas, but does not smooth variation within either path. This follows the core aim of the product: to show relative surface heat as clearly as possible, with artifacts from Landsat's sampling geometry minimized, so that the resulting patterns are useful for planning and decision-making.

<!-- vale on -->
