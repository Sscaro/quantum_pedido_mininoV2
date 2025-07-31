from utils.utils import procesar_configuracion
from utils.utils import read_file
import os
import pandas as pd

ruta_ventas = os.path.join(os.getcwd(),'AFOventas.xlsx')
ruta_parametros = os.path.join(os.getcwd(),'config','params.yml') 
ruta_config =  os.path.join(os.getcwd(),'config','config.yml') 
config = procesar_configuracion(ruta_config)
parametros = procesar_configuracion(ruta_parametros)

print(list(config['facturas']['columns'].keys())[0:2])
#lectura_archivos = read_file(ruta_ventas,'xlsx')
#lectura_archivos.dfarchivoAFO()

#file.columns = nombrecol
#file = file[n:]
#file = file.reset_index(drop=True