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
from scripts.zip_saver import ShapefileToZipSaver
from scripts.utils import convert_3D_2D
from scripts.data_reader import file_reader
import fiona 
import shutil 
import json 
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

def _to_geojson(df:gpd.GeoDataFrame, output_dir:str, filename:str):

    # save geojson
    df.to_file(os.path.join(output_dir, f"{filename}.geojson"), driver='GeoJSON')
    return None 

def _to_shp(df:gpd.GeoDataFrame, output_dir:str, filename:str):
    # save .shp
    tmp_dir = os.path.join(output_dir, '.tmp')
    if os.path.exists(tmp_dir): shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)

    df.to_file(os.path.join(tmp_dir, f"{filename}.shp"))

    zip_filepath = os.path.join(output_dir, f"{filename}.zip")
    zip = ShapefileToZipSaver(zip_filepath, tmp_dir)
    zip.save()

def _to_kml(df:gpd.GeoDataFrame, output_dir:str, filename:str):
    # save kml 
    fiona.supported_drivers['KML'] = 'rw'
    df.to_file(os.path.join(output_dir, f"{filename}.kml"), driver='KML')
    return None 

def get_exporter(data_type:str):
    
    creator = {'kml': _to_kml,
               'shp': _to_shp,
               'geojson': _to_geojson}
            

    return creator[data_type]

def _ensure_valid_coordinates(geom_list:list):
    if len(geom_list)==1:
        return geom_list
    
    corrected = []
    for l in geom_list:
        if len(l)>2:
            corrected.append(l)
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
    if geom_type == 'point':
        return 'Point'
    elif geom_type == 'linestring':
        return 'LineString'
    else:
        return 'Polygon'

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
        geom_data = geom_data['features'][0]

    if geom_data['geometry']==None:
        return None

    coordinates = str(geom_data['geometry']['coordinates'])
    char_count = next(count for count, char in enumerate(coordinates) if char!='[')

    # get the correct amount of brackets for different types of polygons
    if geom_data['geometry']['type'] == 'MultiPoint':
        n_char = 2
    elif geom_data['geometry']['type'] == 'MultiLineString':
        n_char = 3
    elif geom_data['geometry']['type'] ==  'MultiPolygon':
        n_char = 4
    elif geom_data['geometry']['type'] == 'Point':
        n_char = 1
    elif geom_data['geometry']['type'] == 'LineString':
        n_char = 2
    elif geom_data['geometry']['type'] == 'Polygon':
        n_char = 3
    else:
        n_char = char_count
    
    while char_count>n_char:
        geom_data['geometry']['coordinates'] = geom_data['geometry']['coordinates'][0]
        char_count -= 1

    # ensure valid coordinates
    geom_data['geometry']['coordinates'] = _ensure_valid_coordinates(geom_data['geometry']['coordinates'])

    # read data and explode if geometry type is multipolygon
    df = gpd.read_file(json.dumps(geom_data))
    if n_char==4:
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
    input_type = [input_type] if input_type != 'all' else ['shp', 'geojson', 'kml']
    
    # iterate over all files 
    logging.debug("Processing files to export...")
    files = [fl for fl in os.listdir(dirpath) if fl.split(os.extsep)[-1] in input_type]
    geometries_df = gpd.GeoDataFrame(columns=['geometry'], crs=4326)

    # sort files by ascending order
    # TODO: Esta lógica está condicionada para talhões com nomes numéricos, e precisa pensar em um formato mais genérico.
    files_ids = [int(f.split('.')[0]) for f in files]
    files = [fl for _, fl in sorted(zip(files_ids, files))]

    for fl in files:
        
        filepath = os.path.join(dirpath, fl)

        if fl.split(os.extsep)[-1] == '.geojson':
            df = _load_geojson(filepath)
        else:
            df = _load_shp_or_kml(filepath)

        df = df[df.geom_type == geom_type]
        if len(df) > 0:
            geometries_df = geometries_df.append(df)

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