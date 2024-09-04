# -- coding: utf-8 --
# ###################
# Author: Angelica Tiemi Mizuno Nakamura
# Date: 2024-09-04
# ###################

import geopandas as gpd 
import fiona 
import os 
import shutil

from scripts.zip_saver import ShapefileToZipSaver

def __convert_dtype(df:gpd.GeoDataFrame)->gpd.GeoDataFrame:
    # Funcao para converter atributos do tipo object para string
    df = df.astype({col: 'string' for col in df.select_dtypes(include=['object']).columns})

    return df

def _to_geojson(df:gpd.GeoDataFrame, output_dir:str, filename:str):

    # save geojson
    df = __convert_dtype(df)
    df.to_file(os.path.join(output_dir, f"{filename}.geojson"), driver='GeoJSON')
    return None 

def _to_shp(df:gpd.GeoDataFrame, output_dir:str, filename:str):
    # save .shp
    tmp_dir = os.path.join(output_dir, '.tmp')
    if os.path.exists(tmp_dir): shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)

    df = __convert_dtype(df)
    df.to_file(os.path.join(tmp_dir, f"{filename}.shp"))

    zip_filepath = os.path.join(output_dir, f"{filename}.zip")
    zip = ShapefileToZipSaver(zip_filepath, tmp_dir)
    zip.save()

    shutil.rmtree(tmp_dir)

def _to_kml(df:gpd.GeoDataFrame, output_dir:str, filename:str):
    
    # save kml 
    fiona.supported_drivers['KML'] = 'rw'
    
    df = __convert_dtype(df)
    df.to_file(os.path.join(output_dir, f"{filename}.kml"), driver='KML')
    return None 

def get_exporter(data_type:str):
    
    creator = {'kml': _to_kml,
               'shp': _to_shp,
               'geojson': _to_geojson}
            

    return creator[data_type]