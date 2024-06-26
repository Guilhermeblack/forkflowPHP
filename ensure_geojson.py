
# -- coding: utf-8 --
# ###################
# Author: Angelica Tiemi Mizuno Nakamura
# Date: 2023-05-29
# ###################

"""Describe the main script"""

import argparse
import os, shutil, sys
from zipfile import ZipFile

import logging
import geopandas as gpd 

from scripts.data_reader import file_reader
from scripts.utils import get_utm 
from shapely.ops import linemerge

logging.getLogger(__name__).propagate = False
logging.basicConfig(filename='terrace_converter.log', filemode='w', format='%(asctime)s %(module)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
for log_name, log_obj in logging.Logger.manager.loggerDict.items():
    if log_name != __name__:
        log_obj.disabled = True

this_dir = os.path.dirname(__file__)

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
        "-fv", "--field_vector",
        type=str,
        required=True,
        help="Path to input field vectors."
    )
    required.add_argument(
        "-i", "--input_path",
        type=str,
        required=True,
        help="Path to input terrace file."
    )
    ################################################################
    #endregion Mandatory arguments

    #region Optional arguments
    optional = parser.add_argument_group('Optional arguments')
    optional.add_argument(
        "-o", "--output_dir",
        type=str,
        required=False,
        default="",
        help="Path to output directory"
    )
    #endregion Optional arguments

    args = parser.parse_args(args=argv)
    return args


def extract(zip_filepath:str, outdir:str)->str:
    # loading and creating a zip object
    with ZipFile(zip_filepath, 'r') as zObject:
    
        # Extracting all the members of the zip 
        # into outdir.
        zObject.extractall(
            path=outdir)

def _remove_tmp(tmp_dir:str):

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

def check_inconsistency(terrace_df, field_df):
    # fix invalid geometry
    field_df.geometry = field_df.buffer(0)

    terrace_df = gpd.clip(terrace_df, field_df, keep_geom_type=True)
    terrace_df = terrace_df.explode(ignore_index=True)
    terrace_df = terrace_df.drop_duplicates('geometry')

    terrace_df = gpd.GeoDataFrame(
                    geometry=list(linemerge(list(terrace_df.geometry)).geoms),
                    crs=terrace_df.crs)

    inconsistent_points = gpd.GeoSeries()
    for roi in field_df.geometry:
        roi_boundary = roi.boundary
        terraces = terrace_df.loc[terrace_df.intersects(roi)]
        if len(terraces)==0:
            continue
        external_points = terraces.boundary
        external_points = external_points.explode(index_parts=False).reset_index(drop=True)
        external_points = external_points.loc[external_points.distance(roi_boundary)>20]
        inconsistent_points = inconsistent_points.append(external_points)

    inconsistent_points = gpd.GeoDataFrame(
                            geometry=inconsistent_points, 
                            crs=terrace_df.crs)
    
    return inconsistent_points

def convert_to_geojson(vector_path:str, shape_path:str, output_dir:str)->str:
    """
    Function to convert input file to .geojson and with 4326 CRS
    If the input is .zip file, it will be extracted and saved as .geojson file at specified output_path.

    Args:
        shape_path (str): input filepath

    Returns:
        str: filepath of .geojson file 
    """

    filename, ext = os.path.splitext(os.path.basename(shape_path))

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # create tmp dir and ensure folder exists
    tmp_dir = os.path.join(output_dir, '.tmp')

    # extraxt file in cases of zipfile        
    if '.zip' in ext:
        logging.debug("Extracting .zip file")
        # extract zip
        if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)
        aux_dir = tmp_dir
        extract(shape_path, aux_dir)

        while True:
            # iterate until find folder that contains shapefile 
            if os.path.isdir(os.path.join(aux_dir, os.listdir(aux_dir)[0])):
                aux_dir = os.path.join(aux_dir, os.listdir(aux_dir)[0])
            else:
                break

        # update shape path and file extension
        shape_path = [os.path.join(aux_dir, f) for f in os.listdir(aux_dir) if f.split('.')[-1] in ['geojson','shp', 'kml']]
        if len(shape_path)>1 or len(shape_path)==0:
            logging.debug(f"Invalid input file with {len(shape_path)} files.")
            _remove_tmp(tmp_dir)
            return 2
        else:
            shape_path, = shape_path

        logging.debug(f"Input filepath {shape_path}")
        _, ext = os.path.splitext(os.path.basename(shape_path))

    logging.debug(f"Reading field vector {vector_path}")
    vector_df = gpd.read_file(vector_path)
    logging.debug(f"Getting field vector utm")
    utm_crs = get_utm(vector_df)
    logging.debug(f"Converting to utm_crs")
    vector_df.to_crs(utm_crs, inplace=True)

    logging.debug(f"Reading {ext} file")
    df = file_reader(ext, shape_path, utm_crs)
    if not df.is_valid.all() or len(gpd.overlay(df, vector_df))==0:
        logging.debug(f"Invalid input file.")
        return 2 
    
    logging.debug(f"Searching inconstency in terrace rows...")
    inconsistent_points = check_inconsistency(df, vector_df)

    logging.debug(f"Saving TERRACO_CLIENT.geojson in {output_dir}")
    df.to_crs(4326, inplace=True)
    df.to_file(os.path.join(output_dir, "TERRACO_CLIENT.geojson"), driver='GeoJSON')

    if len(inconsistent_points)>0:
        logging.debug(f"Uploaded terrace file has {len(inconsistent_points)} inconsistent points!")
        inconsistent_points.to_file(os.path.join(output_dir, "inconsistent_points.geojson"), driver='GeoJSON')
        return 3


    # remove tmp dir
    logging.debug(f"Removing tmp dir")
    _remove_tmp(tmp_dir)

    return 1


if __name__ == '__main__':
    logging.debug("Starting script")
    # Parse args
    args = parse_args(sys.argv[1:])
    input_path = args.input_path
    vector_path = args.field_vector
    output_dir = args.output_dir if args.output_dir else os.path.join(this_dir, 'output')

    try:
        return_code = convert_to_geojson(vector_path, input_path, output_dir)
        print(return_code)
        logging.debug(f"Finished!")
    except:
        # Failed execution
        logging.debug(f"Failed execution!")
        print(0)