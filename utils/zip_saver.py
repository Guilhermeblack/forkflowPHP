from zipfile import ZipFile
import os

class ShapefileToZipSaver:
    """
    Acessa todos os arquivos gerados no processo e compacta
    em um arquivo zip que será servido para download como resultado do processo.
    """

    def __init__(self, zipname, zipdir):
        # checa as extensões geradas pelo shapefile
        self.ext = ['.cpg', '.dbf', '.prj', '.shp', '.shx', '.geojson', '.json']
        # verifica o nome do arquivo e da propriedade
        self.zipname = zipname
        # verifica o diretório que o arquivo será salvo.
        self.zipdir = zipdir

    def save(self):

        zipObj = ZipFile(self.zipname, 'w')

        for f in os.listdir(self.zipdir):
            if os.path.splitext(f)[1] in self.ext:
                filePath = os.path.join(self.zipdir, f)
                zipObj.write(filePath, os.path.basename(filePath))

        zipObj.close()
        return True
