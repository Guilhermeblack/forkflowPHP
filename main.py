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
from utils.zip_saver import ShapefileToZipSaver
import fiona 
import shutil 
import json 
import numpy as np 

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

def main(dirpath:str, data_type:str, filename:str, output_dir:str, time):
    """
    Main function to export .geojson to .shp and .kml
    """

    start = t()

    # iterate over all files 
    files = [fl for fl in os.listdir(dirpath) if fl.endswith('geojson')]
    polygons = gpd.GeoDataFrame(columns=['geometry'], crs=4326)

    # sort files by ascending order
    files_ids = [int(f.split('.')[0]) for f in files]
    files = [fl for _, fl in sorted(zip(files_ids, files))]

    for fl in files:
        
        filepath = os.path.join(dirpath, fl)

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
            continue

        coordinates = str(geom_data['geometry']['coordinates'])
        char_count = next(count for count, char in enumerate(coordinates) if char!='[')

        # get the correct amount of brackets for different types of polygons
        n_char = 4 if geom_data['geometry']['type'] == 'MultiPolygon' else 3
        while char_count>n_char:
            geom_data['geometry']['coordinates'] = geom_data['geometry']['coordinates'][0]
            char_count -= 1


        # ensure valid coordinates
        geom_data['geometry']['coordinates'] = _ensure_valid_coordinates(geom_data['geometry']['coordinates'])

        # read data and explode if geometry type is multipolygon
        df = gpd.read_file(json.dumps(geom_data))
        if n_char==4:
            df = df.explode(ignore_index=True)

        polygons = polygons.append(df)

    polygons = polygons.reset_index(drop=True)
    
    if len(polygons)>0:
        # ensure output dir exists 
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # save
        exporter = get_exporter(data_type)
        exporter(polygons, output_dir, filename)
    else: 
        print("Empty dataframe!")

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