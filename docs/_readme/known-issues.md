<!-- vale off -->

## Known issues

### ASTER coverage gaps

There are [sizable, documented gaps in the ASTER Global Emissivity Dataset (GED)](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature-data-gaps-due-missing-aster-ged), stemming from persistent cloud cover, which affect our end product.

![Global ASTER GED emissivity coverage. Blue shows available data; white shows gaps.](/images/aster-ged-coverage-usgs.jpg)

*Via [USGS](https://www.usgs.gov/media/images/aster-ged-emissivity-coverage).*

We compared these gaps to [GHS-SMOD R2023A urban land](https://human-settlement.emergency.copernicus.eu/ghs_smod2023.php) and found that they impact 2.66% of urban land. Another 10.23% of urban land rests on only one or two ASTER observations. Here is a breakdown by region:

| Region | Share of urban land with no ASTER observations |
|---|---:|
| Southeast Asia | 12.07% |
| Amazonia | 11.62% |
| Southern Africa | 8.36% |
| Europe | 2.80% |
| North America | 1.18% |
| Australia | 0.30% |
| Sahara and Sahel | 0.00% |

Where coverage was missing due to ASTER GED gaps, we report nodata.

### Limited tropical coverage

We have also observed patches with missing coverage in, e.g., the Brazilian Amazon, which appear to be the result of persistent cloud cover. We haven't quantified the total area impacted by these gaps, but it is primarily in tropical, sparsely populated regions.

<!-- vale on -->
