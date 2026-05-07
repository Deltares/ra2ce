import gc
import sys
from pathlib import Path

import xarray as xr

# Input and output folder paths
_input_folder = Path(sys.argv[0])
_output_folder = Path(sys.argv[1])

# Iterate over each input GeoTIFF file
for _input_tiff in list(_input_folder.glob("*.tif")):
    _output_tiff = _output_folder.joinpath(_input_tiff.name)

    _input_dataarray = xr.open_dataarray(_input_tiff)
    _input_as_wgs84 = _input_dataarray.raster.reproject(dst_crs=4326)

    _input_as_wgs84.raster.to_raster(_output_tiff, driver="GTiff", compress="lzw")

    # Clean up
    del _input_dataarray, _input_as_wgs84
    gc.collect()
