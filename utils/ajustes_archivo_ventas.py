import pandas as pd
import numpy as np
import re
from utils.utils import filtrar_dataframe, limpiar_valor


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
    data[listado_mes] = data[listado_mes].astype(float)
    data['modelo_atencion'] = data[list(config['ventas']['columns'].keys())[0]].astype(str).str.startswith('8').map({True: 'Indirecta', False: 'Directa'})    # realizando tipado de las columnas de mes y reemplazos de valores 0 a nulos
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
    print(data.info())
    return data



