import pandas as pd
import numpy as np
import re
from utils.utils import filtrar_dataframe

def limpiar_valor(valor):
    if pd.isna(valor):
        return np.nan
    valor = str(valor)
    # Reemplaza tabulaciones y múltiples espacios por un solo espacio
    valor = re.sub(r'[\t\s]+', '', valor)
    return valor

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

def obtener_ultimo_mes(row,meses):
    '''
    funcion para encontrar el ultimo mes con ventas.
    '''
    meses_con_ventas = [mes for mes in meses if pd.notna(row[mes]) and row[mes] > 0]
    return meses_con_ventas[-1] if meses_con_ventas else np.nan


def ajustar_archivo_afo(data: pd.DataFrame, config: dict, listado_mes: list):
    '''
    funcion que realiza ajustes en los archivos de ventas del proyecto y calcula ciertos calculos.
    arg: data: pd.DataFrame
    config: dict
    listado_mes: list con los meses
    return df
    '''    
    #calcular modelo de atención y concatenar cod_cliente agente
    try:
        data['modelo_atencion'] = data[config['lista_columnas_afo'][0]].astype(str).str.startswith('8').map({True: 'Indirecta', False: 'Directa'})    # realizando tipado de las columnas de mes y reemplazos de valores 0 a nulos

        #data[config['listo_meses_completos']] = data[config['listo_meses_completos']].astype(float)
        data[listado_mes] = data[listado_mes].replace(0, np.nan)
        #contando valores no nulos en las columnas.
        data['conteo_meses'] = data[listado_mes].notna().sum(axis=1)
        data['ultimo_mes_con_ventas'] = data.apply(obtener_ultimo_mes,axis=1,args=(listado_mes,))
        data['ventas_acumuladas'] = data[listado_mes].sum(axis=1, skipna=True)
        data['ventas_promedio'] = np.divide(
                data['ventas_acumuladas'],
                data['conteo_meses'],
                out=np.zeros_like(data['ventas_acumuladas']),
                where=data['conteo_meses'] != 0
            )
        data['total_meses_analizado'] = len(listado_mes)

        data  = filtrar_dataframe(data,config['filtros_archivo_ventas']['filtros_excluir'],modo='excluir')
        return data
    except Exception as e:
        raise Exception(f"Error en ajustar_archivo_afo: {str(e)}")

def ajustes_archivo_maestra_directa(df,config):
    '''
    funcion para realizar ajustes de la maestra de la directa
    ARG df: DataFrame
        config: dict. Archivo de configuracion
    '''
    columnas = config['cofig_archivo_maestras']['names']
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
    columnas = config['cofig_universo_indirecta']['names']

    df[columnas[2]] = df[columnas[2]].apply(limpiar_valor)
    df[columnas[2]]= df[columnas[2]].replace('', np.nan)
    df = df.fillna("-")
    df[columnas[2]]= df[columnas[2]].apply(lambda x: str(x).upper())
    df['num_visita_semana'] = df[columnas[2]].apply(calcular_visitas_semana)
    
    # agrupación
    df = df.groupby(list(df.columns[0:4:3]),dropna=False)[df.columns[4]].sum().reset_index()
    df[df.columns[1]] = df[df.columns[0]]+df[df.columns[1]]
    del df[df.columns[0]]
    return df

def concatenar_df(*dfs,ignore_index=True):

    '''
    funcion para concatenar data frames
    '''
    for i, df in enumerate(dfs):
        if not isinstance(df, pd.DataFrame):
            raise ValueError(f"El argumento número {i+1} no es un DataFrame") 
    
    return pd.concat(dfs, ignore_index=ignore_index)