
# -- coding: utf-8 --
# ###################
# Author: Angelica Tiemi Mizuno Nakamura
# Date: 2023-05-29
# ###################

"""Describe the main script"""

import argparse
import os, shutil, sys
from zipfile import ZipFile

import geopandas as gpd 
from osgeo import ogr 
import fiona 
import logging

logging.getLogger(__name__).propagate = False
logging.basicConfig(filename='terrace_converter.log', filemode='w', format='%(asctime)s %(module)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)
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
        "-i", "--input_path",
        type=str,
        required=True,
        help="Path to input file."
    )
    required.add_argument(
        "-o", "--output_dir",
        type=str,
        required=True,
        help="Path to output directory"
    )
    ################################################################
    #endregion Mandatory arguments
    

    args = parser.parse_args(args=argv)
    return args

def file_reader(format, filepath):
    formats_getter = {'.kml':kml_reader,
                      '.geojson':shape_reader,
                      '.shp':shape_reader}
    
    return formats_getter[format](filepath)


def kml_reader(filepath):

    # read kml format and convert to wgs 4326

    fiona.drvsupport.supported_drivers['KML'] = 'rw'
    df = gpd.read_file(filepath, driver='kml')
    crs = get_correct_crs(filepath)
    if not crs is None: #if None, crs is in SIRGAS
        df.crs = int(crs)
    df.to_crs(4326, inplace=True)

    return df 

def shape_reader(shape_path):

    # read shapefile and convert to wgs 4326

    df = gpd.read_file(shape_path)
    logging.debug("Getting correct CRS")
    crs = get_correct_crs(shape_path)
    if not crs is None: #if None, crs is in SIRGAS
        logging.debug(f"Setting GeoDataFrame to CRS {crs}")
        df.crs = int(crs)
    logging.debug(f"Converting to 4326")
    df.to_crs(4326, inplace=True)

    return df 


def extract(zip_filepath:str, outdir:str)->str:
    # loading and creating a zip object
    with ZipFile(zip_filepath, 'r') as zObject:
    
        # Extracting all the members of the zip 
        # into outdir.
        zObject.extractall(
            path=outdir)
       
       
def get_correct_crs(filepath)->str:
    
    """ Get correct CRS from shapefile 

    Args:
        shape_df (str): shapefile filepath 

    Returns:
        str: CRS of shapefile
    """
    src_file = ogr.Open(filepath)
    crs = src_file.GetLayer().GetSpatialRef().GetAttrValue("AUTHORITY",1)

    return crs


def _remove_tmp(tmp_dir:str):

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

def convert_to_geojson(shape_path:str, output_dir:str)->str:
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

    logging.debug(f"Reading {ext} file")
    df = file_reader(ext, shape_path)
    logging.debug(f"Saving TERRACO_CLIENT.geojson in {output_dir}")
    df.to_file(os.path.join(output_dir, "TERRACO_CLIENT.geojson"), driver='GeoJSON')

    # remove tmp dir
    logging.debug(f"Removing tmp dir")
    _remove_tmp(tmp_dir)

    return 1


if __name__ == '__main__':
    # Parse args
    args = parse_args(sys.argv[1:])
    input_path = args.input_path
    output_dir = args.output_dir

    print("************************* Starting script. *************************")
    try:
        return_code = convert_to_geojson(input_path, output_dir)
        print(return_code)
        logging.debug(f"Finished!")
    except:
        # Failed execution
        logging.debug(f"Failed execution!")
        print(0)