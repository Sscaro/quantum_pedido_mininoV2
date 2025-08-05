from utils.utils import limpiar_valor
import pandas as pd
import numpy as np

def calcular_visitas_semana(cod):
    '''
    Funcion para convertir el codigo de visita a numero de visitas por semana
    '''
    try:
        if pd.isna(cod):
            return 0
        elif str(cod).startswith("S"):
            return 1
        elif str(cod).startswith("Q"):
            return 0.5
        elif str(cod).startswith("M"):
            return 0.25
        else:
            return 1
    except KeyError:
        print("valor No convertido")


def ajustes_archivo_maestra_directa(df,config):
    '''
    funcion para realizar ajustes de la maestra de la directa
    ARG df: DataFrame
        config: dict. Archivo de configuracion
    '''
    columnas = config['universo_directa']['names']
    df[columnas[0]] = df[columnas[0]].astype(str).str.lstrip('0') # columnas[0] debe ser el cod cliente
    df = df[df[columnas[1]].isin(config['filtros_func_in'])]
    df = df.drop_duplicates(keep='first')
    
    df[columnas[2]] = df[columnas[2]].apply(limpiar_valor)
    df[columnas[2]] = df[columnas[2]].replace('', np.nan)
    df = df.fillna("-")
    df[columnas[2]]= df[columnas[2]].apply(lambda x: str(x).upper())
    df['num_visita_semana'] = df[columnas[2]].apply(calcular_visitas_semana)
    
    #agrupacion
    df = df.groupby(df.columns[0],dropna=False)[df.columns[3]].sum().reset_index()
    return df

def ajustes_archivo_universos_indirecta(df,config):
    '''
    funcion para realizar ajustes de la universo de la indirecta
    ARG df: DataFrame
        config: dict. Archivo de configuracion
    '''
    columnas = config['universo_indirecta']['names']
    df[columnas[2]] = df[columnas[2]].apply(limpiar_valor)
    df[columnas[2]]= df[columnas[2]].replace('', np.nan)
    df = df.fillna("-")
    df[columnas[2]]= df[columnas[2]].apply(lambda x: str(x).upper())
    df['num_visita_semana'] = df[columnas[2]].apply(calcular_visitas_semana)
    
    # agrupación
    df = df.groupby(list(df.columns[0:4:3]),dropna=False)[df.columns[4]].sum().reset_index()
    #df[df.columns[1]] = df[df.columns[0]]+df[df.columns[1]]
    #del df[df.columns[0]]
    return df

def concatenar_df(*dfs,ignore_index=True):
    '''
    funcion para concatenar data frames
    '''
    for i, df in enumerate(dfs):
        if not isinstance(df, pd.DataFrame):
            raise ValueError(f"El argumento número {i+1} no es un DataFrame") 
    
    return pd.concat(dfs, ignore_index=ignore_index)