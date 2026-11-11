"""Extract one grid cell of the IPCC Atlas tx35 index into a small Parquet table.

The IPCC WGI AR6 Interactive Atlas publishes `tx35`, the monthly count of days
with a daily maximum temperature above 35 °C, as global NetCDF files on the
Copernicus Climate Data Store. Each experiment is a 200 to 250 MB download that
needs a CDS account and API key. The Pergamino tutorial needs one grid cell of
it, so this script reads that cell once and writes every ensemble member to a
long table the tutorial reads directly.

Download the four experiments with the CDS API (dataset
`projections-climate-atlas`, origin `cmip6`, domain `global`, variable
`monthly_count_of_days_with_maximum_temperature_above_35_c`), unzip each one
into its own directory, and run:

    uv run --group docs python docs/tutorials/data/extract_tx35.py \
        --input-dir ipcc_historical_data \
        --input-dir ipcc_ssp1_2_6_data \
        --input-dir ipcc_ssp2_4_5_data \
        --input-dir ipcc_ssp5_8_5_data \
        --lon -60.545 --lat -33.836 \
        --output docs/tutorials/data/pergamino_tx35.parquet

The output has one row per experiment, member, year, and month. A month that
the Atlas reports as missing for a member is left out rather than written as
zero.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import xarray as xr

# The Atlas file names carry the CMIP6 experiment id between fixed fields:
# tx35_CMIP6_<experiment>_mon_<start>-<end>.nc
EXPERIMENT_FIELD = 2


def experiment_of(path: Path) -> str:
    """Return the CMIP6 experiment id encoded in an Atlas file name."""
    return path.stem.split("_")[EXPERIMENT_FIELD]


def extract_file(path: Path, lon: float, lat: float) -> pd.DataFrame:
    """Read the nearest grid cell of one Atlas file for every member."""
    with xr.open_dataset(path, engine="h5netcdf", decode_timedelta=False) as ds:
        cell = ds["tx35"].sel(lon=lon, lat=lat, method="nearest")
        cell = cell.assign_coords(member=ds["member_id"].values).load()
        cell_lon = float(cell["lon"])
        cell_lat = float(cell["lat"])
    frame = cell.drop_vars(
        [c for c in cell.coords if c not in ("member", "time")]
    ).to_dataframe()
    frame = frame.reset_index().dropna(subset=["tx35"])
    return pd.DataFrame(
        {
            "experiment": experiment_of(path),
            "member": frame["member"].astype(str),
            "year": frame["time"].dt.year.astype("int16"),
            "month": frame["time"].dt.month.astype("int8"),
            "tx35": frame["tx35"].astype("float32"),
            "lon": cell_lon,
            "lat": cell_lat,
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--input-dir",
        type=Path,
        action="append",
        required=True,
        help="Directory holding one unzipped Atlas experiment. Repeat per experiment.",
    )
    parser.add_argument(
        "--lon", type=float, required=True, help="Longitude, degrees east"
    )
    parser.add_argument(
        "--lat", type=float, required=True, help="Latitude, degrees north"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Parquet file to write"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frames = []
    for directory in args.input_dir:
        for path in sorted(directory.glob("tx35_*.nc")):
            frame = extract_file(path, args.lon, args.lat)
            print(
                f"{path.name}: {frame['member'].nunique()} members, {len(frame)} rows"
            )
            frames.append(frame)
    if not frames:
        raise SystemExit("No tx35_*.nc files found in the input directories.")
    table = pd.concat(frames, ignore_index=True)
    table = table.sort_values(["experiment", "member", "year", "month"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(args.output, index=False, compression="zstd")
    size_kb = args.output.stat().st_size / 1024
    print(f"Wrote {len(table)} rows to {args.output} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
