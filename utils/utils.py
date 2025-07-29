import yaml
import os
from typing import Dict, Any, Optional, Tuple
from loguru import logger
import pandas as pd
import time

class DataProcessorError(Exception):
    """Excepción personalizada para errores del DataProcessor"""
    pass


def Registro_tiempo(original_func):
    # Decorador para registrar el tiempo de ejecución de una función.
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = original_func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(
            f"Tiempo de ejecución de {original_func.__name__}: {execution_time} segundos"
        )
        return result
    return wrapper

def procesar_configuracion(nom_archivo_configuracion: Optional[str]) -> dict:
    """Lee un archivo YAML de configuración para un proyecto.

    Args:
        nom_archivo_configuracion (str): Nombre del archivo YAML que contiene
            la configuración del proyecto.

    Returns:
        dict: Un diccionario con la información de configuración leída del archivo YAML.
    """

    if nom_archivo_configuracion:
        if not os.path.exists(nom_archivo_configuracion):
                raise DataProcessorError(f"El archivo de configuración no existe: {nom_archivo_configuracion}")
        try:
            with open(nom_archivo_configuracion, "r", encoding="utf-8") as archivo:
                configuracion_yaml = yaml.safe_load(archivo)
            logger.success("Proceso de obtención de configuración satisfactorio")
            return configuracion_yaml

        except yaml.YAMLError  as e:
            logger.critical(f"Proceso de lectura de configuración fallido {e}")
            raise e


class read_file:
    archivos_disponibles = ['xlsx','csv']
    def __init__(self,ruta:str,tipo_arhivo:str):
        self.ruta = ruta

        if tipo_arhivo in read_file.archivos_disponibles:
            self.archivo = tipo_arhivo
        else:
            raise ValueError("seleccionar un achivo correcto, {}".format(read_file.archivos_disponibles))
        
    @Registro_tiempo
    def leer_excel(self,parametros):
        '''
        Metodo para leer archivo .xlsx
        ARG: parametros

        return = pd. DataFrame
        ''' 
        try:
            params = {'io': self.ruta}

            if 'skiprows' in parametros:
                params['skiprows'] = parametros['skiprows']
            
            if 'names' in parametros:
                params['names'] = parametros['names']

            if 'sheet_name' in parametros:
                params['sheet_name'] = parametros['sheet_name']
            else:
                params['sheet_name'] = 0
            
            if 'usecols' in parametros:
                params['usecols'] = parametros['usecols']
            
            if 'dtype' in parametros:
                params['dtype'] = parametros['dtype']
            else:
                params['dtype'] = 'str'                
        
            df = pd.read_excel(**params)
            #df = df.drop_duplicates(keep='first')
            return True, "✅ Archivo cargado correctamente", df
        except Exception as e:
            return False, f"❌ Error al procesar archivo: {str(e)}", None


    @Registro_tiempo
    def dfarchivoAFO(self,nombrecol,
                     hoja_nombre = "AFO",
                     n=1,
                     types=str):#fucion para leer archivo con
        '''
        Metodo para leer archivo .xlsx que contiene un afo
        nombrecol: lista con los nombres de las columnas
        hoja_nombre: numero de la hoja a leer
        n: numero de filas a saltar
        types: dict con tipado de datos.
        return pd.DataFrame
        '''
        try:
            file = pd.ExcelFile(self.ruta)# elimina columnas vacias
            file = file.parse(hoja_nombre,dtype=str)
            file = file.loc[:,file.count() > 1]
            print(file.columns)
            file.columns = nombrecol
            file = file[n:]
            file = file.reset_index(drop=True)
            file = file.astype(types)
            return True, "✅ Archivo cargado correctamente", file
        except Exception as e:
            return False, f"❌ Error al procesar archivo: {str(e)}", None