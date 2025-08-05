import yaml
import os
from typing import Dict, List, Optional, Union, Any
from loguru import logger
import pandas as pd
import numpy as np
import time
import re


def limpiar_valor(valor):
    if pd.isna(valor):
        return np.nan
    valor = str(valor)
    # Reemplaza tabulaciones y múltiples espacios por un solo espacio
    valor = re.sub(r'[\t\s]+', '', valor)
    return valor


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


def asignar_valor(row, reglas, default):
    '''
    funcion para asginar la segmentación de los canales.
    '''
    for regla in reglas:
        condicion = regla['condicion']
        try:
            if eval(f"row.{condicion}"):
                return regla['asignar']
        except Exception:
            # Manejar errores en el eval (por ejemplo, columna faltante)
            continue
    return default


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


    Registro_tiempo
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
        
    
def agrupa_df(
    df: pd.DataFrame,
    columnas_categoricas: List[str],
    columnas_numericas: List[str],
    operaciones: Union[List[str], Dict[str, Union[str, List[str]]]]
    ) -> pd.DataFrame:
    """
    Agrupa un DataFrame con múltiples operaciones sobre columnas numéricas.

    Parámetros:
    - df: DataFrame original.
    - columnas_categoricas: columnas por las que se agrupará.
    - columnas_numericas: columnas numéricas sobre las que se aplicarán operaciones.
    - operaciones: lista de operaciones (ej: ['sum', 'mean']) o un diccionario con columnas como claves y funciones como valores.

    Retorna:
    - DataFrame agrupado y con índice reseteado.
    """
    # Validaciones básicas
    if isinstance(operaciones, list):
        # Aplica mismas operaciones a todas las columnas numéricas
        agg_dict = {col: operaciones for col in columnas_numericas}
    elif isinstance(operaciones, dict):
        agg_dict = operaciones
    else:
        raise ValueError("El parámetro 'operaciones' debe ser una lista o un diccionario.")
    df_agrupado = df.groupby(columnas_categoricas).agg(agg_dict)
    df_agrupado.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df_agrupado.columns]
    return df_agrupado.reset_index()



def filtrar_dataframe(
    df: pd.DataFrame,
    filtros: Dict[str, Union[str, int, float, List[Union[str, int, float]]]],
    modo: str = 'incluir'
) -> pd.DataFrame:
    """
    Filtra un DataFrame según un diccionario de condiciones de inclusión o exclusión.

    Parámetros:
    - df: DataFrame a filtrar.
    - filtros: Diccionario donde la clave es el nombre de la columna,
               y el valor puede ser un único valor o una lista de valores.
    - modo: 'incluir' para mantener los valores especificados,
            'excluir' para eliminar los valores especificados.

    Retorna:
    - DataFrame filtrado.
    """

    if not isinstance(filtros, dict):
        raise ValueError("El parámetro 'filtros' debe ser un diccionario.")

    if modo not in ['incluir', 'excluir']:
        raise ValueError("El parámetro 'modo' debe ser 'incluir' o 'excluir'.")

    df_filtrado = df.copy()

    for columna, valor in filtros.items():
        if columna not in df_filtrado.columns:
            raise KeyError(f"La columna '{columna}' no existe en el DataFrame.")

        if isinstance(valor, list):
            if modo == 'incluir':
                df_filtrado = df_filtrado[df_filtrado[columna].isin(valor)]
            else:
                df_filtrado = df_filtrado[~df_filtrado[columna].isin(valor)]
        else:
            if modo == 'incluir':
                df_filtrado = df_filtrado[df_filtrado[columna] == valor]
            else:
                df_filtrado = df_filtrado[df_filtrado[columna] != valor]

    return df_filtrado.reset_index(drop=True)

'''
Modulo para crear columnas calculadas
'''

class calculos_personalizados:

    def __init__(self,dataframe,params):
        '''
        arg: data frame,
            params
        '''
        
        if not isinstance(dataframe, pd.DataFrame):
            raise ValueError(f"El argumento no es un DataFrame") 
        else:
            self.dataframe = dataframe
            self.params = params

    def eliminar_columnas(self, columnas: List[str]):
        '''
        Funcion para eliminar columnas de un data frame
        '''
        for col in columnas:
            try:
                del self.dataframe[col]
            except ValueError:
                print(f'valor {col} no se elimino al no encontrase en el data frame')
        return self.dataframe

    def col_caluladas(self,nombre_diccionario:str):
        '''
            funcion para realizar diferentes calculo a un data frame
        '''
        if nombre_diccionario not in self.params .keys():
            raise ValueError(f"no se encuentra {nombre_diccionario} en archivo de configuración") 
        else:
            columnas = self.params .get(nombre_diccionario, {})
            for nueva_col, formula in columnas.items():
                try:
                    self.dataframe[nueva_col] = self.dataframe.eval(formula)
                except Exception as e:
                    raise ValueError(f"Error al calcular '{nueva_col}' con fórmula '{formula}': {e}")
        return self.dataframe
