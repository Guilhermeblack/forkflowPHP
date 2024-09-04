# Converter tipo de arquivo 

Script genérico para converter qualquer formato de arquivo (shp, geojson, kml) para qualquer formato (shp, geojson, kml). O script deve ser capaz de filtrar arquivos de input por formato, filtrar quais geometrias serão salvas no arquivo de saída, e especificar qual formato de arquivo de saída.

```python3 shape_converter.py --dirpath <input_dir> --type <'geojson'/'shp'/'kml'> --filename <filename> --input_type <'geojson'/'shp'/'kml'/'all'> --geometry_type <'Polygon'/'LineString'/'Point'> --output_dir <output_dirpath>```

- --input_dir: diretorio com os arquivos a serem convertido
- --type: extensao do arquivo a ser gerado. ['geojson'/'shp'/'kml]

- --filename: nome do arquivo que sera gerado

- --input_type: tipo do arquivo de entrada ['geojson'/'shp'/'kml'/'all']. Se 'all', ele vai tentar ler todos os arquivos dentro de input_dir

- --geometry_type: tipo de geometrias que serao consideradas ['Polygon'/'LineString'/'Point']

- --output_dir: diretorio de saida onde o arquivo convertido sera salvo