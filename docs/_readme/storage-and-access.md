<!-- vale off -->

### Storage and access

Data are stored as Cloud-Optimized GeoTIFFs in a Portolan catalog on [Source Cooperative](https://data.source.coop/nlebovits/landsat-lst/catalog.json). Each STAC item contains two COG assets, spanning 5° in EPSG:4326:

| Asset | Contents | Encoding | Nodata |
|---|---|---|---|
| `lst_p95` | Corrected and blended P95 LST | `uint16`, one band, with `celsius = DN * 0.01 - 50.0` | DN `0` |
| `qa_count` | Valid observations by calendar month | `uint8`, 12 bands from January through December | none |

The data can be opened normally with, e.g., `rasterio`, `pystac`, QGIS, etc. You can, for example, use the STAC item to resolve the COG URL, then read only the area you need with `rasterio`.

```python
import pystac
import rasterio
from rasterio.windows import from_bounds

item = pystac.Item.from_file(
    "https://data.source.coop/nlebovits/landsat-lst/"
    "lst-p95-2021-2025/S30W065/S30W065.json"
)

with rasterio.open(item.assets["lst_p95"].get_absolute_href()) as src:
    # Filter by region.
    window = from_bounds(-64, -34, -63.9, -33.9, src.transform)
    lst = src.read(1, window=window, masked=True)

    # The scale and offset stored in the COG metadata convert the integer values to °C.
    lst_celsius = lst * src.scales[0] + src.offsets[0]
```

<!-- vale on -->
