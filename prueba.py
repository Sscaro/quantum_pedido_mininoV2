import pandas as pd
import tempfile
import yaml
import io
import os
import glob
import time
from typing import Dict, Any, Optional, Tuple
from utils.utils import procesar_configuracion, asignar_valor, calculos_personalizados
from utils.utils import read_file
from utils.ajustes_archivo_ventas import ajustar_archivo_afo
from utils.ajustes_archivo_gasto import configuracion_gastos
from utils.ajustes_universos import ajustes_archivo_maestra_directa, ajustes_archivo_universos_indirecta


ruta_config =  os.path.join(os.getcwd(),'config','config.yml') # archivo yml para configurar archivos de excel
ruta_parametros = os.path.join(os.getcwd(),'config','params.yml') # parametros y valores constantes del breakeven
config = procesar_configuracion(ruta_config)
parametros = procesar_configuracion(ruta_parametros)

def procesar_archivo(file_key: str, file_path: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Procesa un archivo específico según su tipo
    """
    try:
        if file_key == "ventas":
            columnas_ventas = list(config[file_key]['columns'].keys()) + parametros['anio_mes']
            lectura_archivos = read_file(file_path, 'xlsx')
            return lectura_archivos.dfarchivoAFO(columnas_ventas, n=2)
        
        elif file_key == "facturas":
            columnas_facturas = list(config['facturas']['columns'].keys())
            lectura_archivos = read_file(file_path, 'xlsx')
            return lectura_archivos.dfarchivoAFO(columnas_facturas, hoja_nombre='AFO', n=1, types=config[file_key]['columns'])
        
        elif file_key == "costo_merc_vend":
            columnas_facturas = list(config['costo_merc_vend']['columns'].keys())
            lectura_archivos = read_file(file_path, 'xlsx')
            return lectura_archivos.dfarchivoAFO(columnas_facturas, hoja_nombre='AFO', n=2, types=config[file_key]['columns'])
        
        else:
            lectura_archivos = read_file(file_path, 'xlsx')
            return lectura_archivos.leer_excel(config[file_key])
    
    except Exception as e:
        return False, f"❌ Error al procesar archivo: {str(e)}", None

def run():
    ruta_afo_ventas = os.path.join(os.getcwd(),'insumos','AFOventas.xlsx')
    ruta_afo_facturas = os.path.join(os.getcwd(),'insumos','AFOFacturas.xlsx')
    ruta_gastos = os.path.join(os.getcwd(),'insumos','gastos.xlsx')
    ruta_cmv = os.path.join(os.getcwd(),'insumos','costo_mercancia_vendida.xlsx')
    ruta_directa = os.path.join(os.getcwd(),'insumos','maestra_clientes_activos_directa.xlsx')
    ruta_indirecta = os.path.join(os.getcwd(),'insumos','universo_indirecta.xlsx')
    ruta_cxm = os.path.join(os.getcwd(),'insumos','Costo_por_minuto.xlsx')
    
    is_valid, message, costo_por_minuto_visita = procesar_archivo('costo_por_minuto', ruta_cxm)
    is_valid, message, costo_por_minuto_entrega = procesar_archivo('costo_minuto_x_entrega',ruta_cxm)
    is_valid, message, ventas = procesar_archivo('ventas', ruta_afo_ventas)
    is_valid, message, facturas = procesar_archivo('facturas', ruta_afo_facturas)
    is_valid, message, costo_merc_vend = procesar_archivo('costo_merc_vend', ruta_cmv)
    is_valid, message, gastos = procesar_archivo('gastos', ruta_gastos)
    is_valid, message, maestra_directa = procesar_archivo('universo_directa', ruta_directa)
    is_valid, message, universo_indirecta = procesar_archivo('universo_indirecta', ruta_indirecta)
    

    data_ventas_ajustada = ajustar_archivo_afo(
                            ventas,
                            config,
                            parametros['anio_mes']
                        )
                        #asociando facturas
    data_ventas_ajustada = data_ventas_ajustada.merge(facturas,
                                  on=list(config['facturas']['columns'].keys())[0:2], how='left')                        
    # añadiendo nueva segmentiación quantum
    data_ventas_ajustada['nueva_segmentacion'] = data_ventas_ajustada.apply(lambda row: asignar_valor(row, parametros['prioridad'], parametros['default']), axis=1)

    #leyendo archivo COGS:
    objeto_gastos = configuracion_gastos(config=config,
                                         ventas=data_ventas_ajustada,
                                          gasto = gastos
                                         )
    data_cogs_ajustada = objeto_gastos.ajustar_archivo_cogs(costo_merc_vend)
    # Costo_por_otros:
    costo_otros_dir  =  objeto_gastos.ajustes_gastos_por_otros(modelo='directa')
    costo_otros_ind = objeto_gastos.ajustes_gastos_por_otros(modelo='indirecta')

    #gastos por entrega fijos
    gastos_entrega_dir = objeto_gastos.ajus_gastos_entrega_fijos(modelo='directa')
    gastos_entrega_ind = objeto_gastos.ajus_gastos_entrega_fijos(modelo='indirecta')
    gastos_entrega_var_dir= objeto_gastos.ajus_gastos_entrega_variable(modelo='directa')
    gastos_entrega_var_ind= objeto_gastos.ajus_gastos_entrega_variable(modelo='indirecta')

    data_ventas_ajustada = data_ventas_ajustada.merge(data_cogs_ajustada,left_on=[list(config['ventas']['columns'].keys())[3],
                                                                                  list(config['ventas']['columns'].keys())[7]],
                                                    right_on=[list(config['costo_merc_vend']['columns'].keys())[0],
                                                    list(config['costo_merc_vend']['columns'].keys())[2]],
                                                    how = 'left')
    
    #Ajustes relaciones modelo de atención directo.
    data_ventas_ajustada_directa  = data_ventas_ajustada[data_ventas_ajustada['modelo_atencion']=='Directa']          
    data_ventas_ajustada_directa = data_ventas_ajustada_directa.merge(
                                                                costo_otros_dir, on =config['agrupa_vta_gxotro']['directa']['categorias'],   
                                                                how='left')
    data_ventas_ajustada_directa = data_ventas_ajustada_directa.merge(
                                                                gastos_entrega_dir, on =config['agrupa_vta_gxotro']['directa']['categorias'],       
                                                                how='left')
    data_ventas_ajustada_directa = data_ventas_ajustada_directa.merge(gastos_entrega_var_dir, on =config['agrupa_vta_gxotro']['directa']['categorias'],
                                                                        how='left')
    #Ajustes relaciones modelo de atención Indirecta.
    data_ventas_ajustada_indirecta  = data_ventas_ajustada[data_ventas_ajustada['modelo_atencion']=='Indirecta']
    data_ventas_ajustada_indirecta = data_ventas_ajustada_indirecta.merge(
                                                                costo_otros_ind, on =config['agrupa_vta_gxotro']['indirecta']['categorias'],
                                                                how='left')
    data_ventas_ajustada_indirecta = data_ventas_ajustada_indirecta.merge(
                                                                gastos_entrega_ind, on =config['agrupa_vta_gxotro']['indirecta']['categorias'],
                                                                how='left')
    data_ventas_ajustada_indirecta = data_ventas_ajustada_indirecta.merge(gastos_entrega_var_ind, on =config['agrupa_vta_gxotro']['indirecta']['categorias'],
                                                                        how='left')
       
    # maestra de clientes directa e indirecta
    maestra_directa = ajustes_archivo_maestra_directa(maestra_directa, config)
    #cruce de información universos con ventas
    universo_indirecta = ajustes_archivo_universos_indirecta(universo_indirecta, config)        
    data_ventas_ajustada_directa = data_ventas_ajustada_directa.merge(
        maestra_directa,
        left_on=list(config['ventas']['columns'].keys())[0],
        right_on=config['universo_directa']['names'][0],
        how='left')
     #cruce de información universos indicra
    data_ventas_ajustada_indirecta = data_ventas_ajustada_indirecta.merge(
        universo_indirecta,
        left_on=(list(config['ventas']['columns'].keys())[0],list(config['ventas']['columns'].keys())[2]),
        right_on=(config['universo_indirecta']['names'][3],config['universo_indirecta']['names'][0]),
        how='left')
    
    data_ventas_ajustada =  pd.concat([data_ventas_ajustada_directa,data_ventas_ajustada_indirecta])

    ### gasto por visita
    gasto_visita = objeto_gastos.ajus_gastos_visita(costo_por_minuto_visita)   
    data_ventas_ajustada = data_ventas_ajustada.merge(
        gasto_visita,
        left_on=config['merge_cxm']['left_on'],
        right_on=config['merge_cxm']['right_on'],
        how='left')
    
    #leyendo archivo de minutos por entrega
  
    #cruce costo por minuto entrega
    data_ventas_ajustada = data_ventas_ajustada.merge(
        costo_por_minuto_entrega,
        left_on=config['merge_cxe']['left_on'],
        right_on=config['merge_cxe']['right_on'],
        how='left')

    calculando = calculos_personalizados(data_ventas_ajustada, parametros)
    data_con_calculos = calculando.col_caluladas('columnas_calculadas')
    data_con_calculos = calculando.eliminar_columnas(parametros['columnas_borrar'])
    data_con_calculos.to_excel('resultado.xlsx',index=False)


if __name__ == '__main__':
    run()