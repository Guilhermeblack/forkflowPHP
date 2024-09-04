# -- coding: utf-8 --
# ###################
# Author: Angelica Tiemi Mizuno Nakamura
# Edited by: Luiz Ricardo Takeshi Horita
# Date: 2024-08-22
# ###################

"""Describe the main script"""

from time import time as t
import argparse
import sys
import os
import geopandas as gpd 
from scripts.file_exporter import get_exporter
from scripts.utils import convert_3D_2D
from scripts.data_reader import file_reader
import json 
import logging
import pandas as pd

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
        "-it", "--input_type",
        type=str,
        required=False,
        default="geojson",
        help="Input file type. It can be 'geojson', 'shp', 'kml' or 'all'. If 'all', any file format among shp, geojson and kml will be accepted. (Default: 'geojson')"
    )
    optional.add_argument(
        "-g", "--geometry_type",
        type=str,
        required=False,
        default="Polygon",
        help="Type of geometry to be saved in output file. It can be any of those: ['Polygon', 'LineString', 'Point']. (Default: 'Polygon')"
    )
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
    # remove cases of polygons with two coordinates

    if len(geom_list)==1:
        # multipolygon with only one geometry
        return geom_list
    
    corrected = []
    for coords_list in geom_list:
        # treatment to deal with multipolygons
        if len(coords_list)==1:
            coords = coords_list[0]
        else:
            coords = coords_list
        if len(coords)>2:
            corrected.append(coords_list)

    return corrected

def _ensure_geom_type_format(geom_type:str)->str:
    """
    Ensure geom_type is provided with correct string case format.
    Point, LineString, Polygon.

    Args:
        geom_type (str): geom_type provided in argument

    Returns:
        str: formated geom_type string.
    """
    geom_type = geom_type.lower()
    formats = {'point': 'Point',
               'linestring': 'LineString',
               'polygon': 'Polygon'}
    
    return formats.get(geom_type)

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
    
    df.geometry = convert_3D_2D(df.geometry)
    
    return df

def _get_brackets_number(geom_type:str):

    # get the correct amount of brackets for different types of geometries
    # https://datatracker.ietf.org/doc/html/rfc7946
    
    brackets_map = {'MultiPoint': 2,
                  'MultiLineString': 3,
                  'MultiPolygon': 4,
                  'Point': 1,
                  'LineString': 2,
                  'Polygon': 3}
    
    return brackets_map.get(geom_type)

def _load_geojson(filepath:str)->gpd.GeoDataFrame:
    """
    Fix inconsistencies on geojson data format, and
    load data in GeoDataFrame.

    Args:
        filepath (str): Path to GeoJSON file.

    Returns:
        gpd.GeoDataFrame: Loaded GeoDataFrame.
    """
    # fix invalid data structure outside of {}
    with open(filepath) as f:
        geom_data = []
        for i, line in enumerate(f):

            line = line.strip('\n')
            
            if i==0:
                for count, char in enumerate(line):
                    if char=='{':
                        break

                if count>0: 
                    line = line[count:-count]
        
            geom_data.append(line)

    geom_data = ''.join(geom_data)
    # fix invalid data structure inside of geometry
    geom_data = json.loads(geom_data)

    # skip empty geometries or collection
    if 'Collection' in geom_data['type']:
        features_geom = geom_data['features']
    else:
        features_geom = [geom_data]

    fixed_geoms = []
    for geom in features_geom:
        if geom['geometry']==None:
            continue
        coordinates = str(geom['geometry']['coordinates'])
        char_count = next(count for count, char in enumerate(coordinates) if char!='[')

        n_char = _get_brackets_number(geom['geometry']['type'])
        if n_char == None:
            n_char = char_count
    
        while char_count>n_char:
            geom['geometry']['coordinates'] = geom['geometry']['coordinates'][0]
            char_count -= 1

        # ensure valid polygon coordinates
        if 'Polygon' in geom['geometry']['type']:
            geom['geometry']['coordinates'] = _ensure_valid_coordinates(geom['geometry']['coordinates'])

        fixed_geoms.append(geom)
    
    # update geom_data
    if 'Collection' in geom_data['type']:
        geom_data['features'] = fixed_geoms
    else:
        geom_data = fixed_geoms[0]

    # read data and explode if geometry type is multipolygon
    df = gpd.read_file(json.dumps(geom_data))
    df = df.explode(ignore_index=True)
    
    return df

def _load_shp_or_kml(filepath:str)->gpd.GeoDataFrame:
    """
    Load SHP data in GeoDataFrame.

    Args:
        filepath (str): Path to SHP file.

    Returns:
        gpd.GeoDataFrame: Loaded GeoDataFrame.
    """
    # read data and explode if geometry type is multigeometries
    ext = os.path.splitext(filepath)[-1]
    df = file_reader(ext, filepath, 4326)
    df = df.explode(ignore_index=True)
    return df
    
def main(dirpath:str, input_type:str, geom_type:str, data_type:str, filename:str, output_dir:str, time):
    """
    Main function to export .geojson to .shp and .kml
    """

    start = t()

    # acceptable input file types
    if input_type == 'all':  
        input_type = ('shp', 'geojson', 'kml')
    
    # iterate over all files 
    logging.debug("Processing files to export...")
    files = [fl for fl in os.listdir(dirpath) if fl.endswith(input_type)]
    geometries_df = gpd.GeoDataFrame(columns=['geometry'], crs=4326)

    # sort files by ascending order
    # TODO: Esta lógica está condicionada para talhões com nomes numéricos, e precisa pensar em um formato mais genérico.
    files_ids = [int(f.split('.')[0]) for f in files]
    files = [fl for _, fl in sorted(zip(files_ids, files))]

    for fl in files:
        
        filepath = os.path.join(dirpath, fl)
        if fl.endswith('.geojson'):
            df = _load_geojson(filepath)
        else:
            df = _load_shp_or_kml(filepath)

        df = df[df.geom_type == geom_type]
        if len(df) > 0:
            geometries_df = pd.concat([geometries_df, df])

    logging.debug("Finished files processing.")
    geometries_df = geometries_df.reset_index(drop=True)
    
    if len(geometries_df)>0:
        # ensure output dir exists 
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # fix geometries
        logging.debug("Fixing geometries...")
        geometries_df = _fix_geometries(geometries_df)

        # save
        logging.debug(f"Saving files to {filename}.{data_type}")
        exporter = get_exporter(data_type)
        exporter(geometries_df, output_dir, filename)
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
    input_type = args.input_type
    geom_type = (args.geometry_type).lower()

    assert data_type in ['geojson', 'kml', 'shp'], f"Invalid data_type. It is possible to export the data only to `shp`, `geojson` or `kml`."
    assert input_type in ['geojson', 'kml', 'shp', 'all'], f"Invalid input_type. It is possible to load the data only from `shp`, `geojson`, `kml` or `all` (shp, geojson and kml)."
    assert geom_type.lower() in ['polygon', 'linestring', 'point'], f"Invalid geometry_type. It is possible to load only any of these geometry types: [Polygon, LineString, Point]."
    
    geom_type = _ensure_geom_type_format(geom_type)

    filename = args.filename
    output_dir = args.output_dir if args.output_dir else os.path.join(dirpath, "output")

    time = args.time

    print("************************* Starting script. *************************")
    main(dirpath, input_type, geom_type, data_type, filename, output_dir, time)