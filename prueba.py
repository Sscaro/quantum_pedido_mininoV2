from utils.utils import procesar_configuracion
from utils.utils import read_file
import os
import pandas as pd

ruta_ventas = os.path.join(os.getcwd(),'AFOventas.xlsx')
ruta_parametros = os.path.join(os.getcwd(),'config','params.yml') 
ruta_config =  os.path.join(os.getcwd(),'config','config.yml') 
config = procesar_configuracion(ruta_config)
parametros = procesar_configuracion(ruta_parametros)


#lectura_archivos = read_file(ruta_ventas,'xlsx')
#lectura_archivos.dfarchivoAFO()

file = pd.ExcelFile(ruta_ventas)
file = file.parse("AFO",dtype=str)
file = file.loc[:,file.count() > 1] 

file = file[2:] # Eliminar columnas vacías
print(file.head())
#file.columns = nombrecol
#file = file[n:]
#file = file.reset_index(drop=True