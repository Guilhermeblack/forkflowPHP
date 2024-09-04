# -- coding: utf-8 --
# ###################
# Author: Angelica Tiemi Mizuno Nakamura
# Date: 2022-12-28
# ###################

"""Describe the main script"""

from time import time as t
import argparse
import sys
import os
import geopandas as gpd
from scripts.file_exporter import get_exporter
import logging

logging.getLogger(__name__).propagate = False
logging.basicConfig(filename='exporter.log', filemode='w', format='%(asctime)s %(module)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
for log_name, log_obj in logging.Logger.manager.loggerDict.items():
    if log_name != __name__:
        log_obj.disabled = True

def parse_args(argv):
    """
    Build parser using [<args>] form.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    #region Mandatory arguments
    ################################################################
    required = parser.add_argument_group('Required arguments')

    required.add_argument(
        "-d", "--dirpath",
        type=str,
        required=True,
        help="Dirpath."
    )
    required.add_argument(
        "-t", "--type",
        type=str,
        required=True,
        help="File type to export. It can be 'geojson', 'shp' or 'kml'."
    )
    required.add_argument(
        "-f", "--filename",
        type=str,
        required=True,
        help="Filename."
    )
    ################################################################
    #endregion Mandatory arguments

    #region Optional arguments
    ################################################################
    optional = parser.add_argument_group('Non-required arguments')
    optional.add_argument(
        "-o", "--output_dir",
        type=str,
        required=False,
        default="",
        help="Output dirpath."
    )
    optional.add_argument(
        "--time",
        required=False,
        default=True,
        action="store_true",
        help="Measure execution time and print in the end."
    )
    #endregion

    args = parser.parse_args(args=argv)
    return args

def _ensure_valid_coordinates(geom_list:list):
    if len(geom_list)==1:
        return geom_list

    corrected = []
    for l in geom_list:
        if len(l)>2:
            corrected.append(l)
    return corrected

def _fix_geometries(df:gpd.GeoDataFrame)->gpd.GeoDataFrame:

    """
    Remove duplicated vertex and self-intersections

    Returns:
        gpd.GeoDataFrame: Fixed GeoDataFrame
    """

    tolerance = 1e-5
    if df.crs.is_geographic:
        tolerance *= 0.000009

    df.geometry = df.simplify(tolerance)
    df.geometry = df.buffer(0)

    return df

def main(dirpath:str, data_type:str, filename:str, output_dir:str, time):
    """
    Main function to export .geojson to .shp and .kml
    """

    start = t()

    # iterate over all files
    logging.debug("Processing files to export...")
    files = [fl for fl in os.listdir(dirpath) if fl.endswith('geojson')]

    if len(files) != 1:
        logging.debug("There is more than one file to convert!")
    else:
        fl = files[0]
        
        print(f"Reading file {fl}")
        filepath = os.path.join(dirpath, fl)

        # read data and explode if geometry type is multipolygon
        df = gpd.read_file(filepath)
        df.to_crs(4326)
        
        if len(df)>0:
            # ensure output dir exists
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # save
            logging.debug(f"Saving files to {filename}.{data_type}")
            exporter = get_exporter(data_type)
            exporter(df, output_dir, filename)

        else:
            logging.debug("Nothing to save. Empty dataframe!")

    logging.debug("Finished execution")
    if time:
        print(f"Execution time: {t() - start} seconds.")


if __name__ == '__main__':
    # Parse args
    args = parse_args(sys.argv[1:])
    dirpath = args.dirpath
    data_type = args.type

    assert data_type in ['geojson', 'kml', 'shp'], f"Invalid data_type. It is possible to export the data only to `shp`, `geojson` or `kml`."

    filename = args.filename
    output_dir = args.output_dir if args.output_dir else os.path.join(dirpath, "output")

    time = args.time

    print("************************* Starting script. *************************")
    main(dirpath, data_type, filename, output_dir, time)