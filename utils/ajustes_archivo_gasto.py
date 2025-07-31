# Modulo para realizar ajustes de los gastos.
import pandas as pd
import numpy as np

from utils.utils import agrupa_df
from utils.utils import filtrar_dataframe

class configuracion_gastos:
    '''
    Clase para realizar ajustes de los gastos.
    '''
    def __init__(self, ventas:pd.DataFrame,gasto:pd.DataFrame ,config: dict):
        
        self.config = config
        self.ventas = ventas
        self.gastos = gasto
   
    def ajustar_archivo_cogs(self, data: pd.DataFrame):
        '''
        funcion que realiza ajustes del archivo de los cogs
        ARG: data: DF

        return df
        '''     
        data = data.fillna(0)
        #divide los ingresos sobre los gastos de la mercancia, si no hay ingresos deja por defecto 0.
        columnas = self.config['gastos']['names'].keys()
        data['porc_cogs']= np.where(data[columnas[4]] != 0, data[columnas[5]] / data[columnas[4]], np.nan)
        data = data[[columnas[0], columnas[2],'porc_cogs']]
        data = data.drop_duplicates(keep='first')
        return data
   
    def ajustes_gastos_por_otros(self, modelo = 'Directa'):
        data_gastos = self.gastos.copy()
        gastosxotro = pd.DataFrame()
        try:
            if modelo == 'Directa':
                ventas = filtrar_dataframe(ventas,self.config['filtros_modelo_directa'])
                gastos = filtrar_dataframe(data_gastos,self.config['gastos_por_otros_directa']['filtros_excluir'],modo='excluir')
                gastos = filtrar_dataframe(data_gastos,self.config['gastos_por_otros_directa']['filtros_incluir'])
                ventas_acum  = agrupa_df(ventas,
                                            self.config['agrupa_vta_gxotro_directa']['categorias'],
                                            self.config['agrupa_vta_gxotro_directa']['numericas'],
                                            operaciones=['sum'])
                gas_agrup = agrupa_df(gastos,
                                self.config['agrupa_gastos_dir']['categorias'],
                                self.config['agrupa_gastos_dir']['numericas'],
                                operaciones = ['sum'])

                gastosxotro = pd.merge(ventas_acum, gas_agrup, on = self.config['union_directa_cxo'],how='left').fillna(0)
            else:
                ventas = filtrar_dataframe(ventas,self.config['filtros_modelo_indirecta'])
                gastos = filtrar_dataframe(data_gastos,self.config['gastos_por_otros_indirecta']['filtros_excluir'],modo='excluir')
                gastos = filtrar_dataframe(data_gastos,self.config['gastos_por_otros_indirecta']['filtros_incluir'])
                ventas_acum  = agrupa_df(ventas,
                                            self.config['agrupa_vta_gxotro_indirecta']['categorias'],
                                            self.config['agrupa_vta_gxotro_indirecta']['numericas'],
                                            operaciones=['sum'])
                gas_agrup = agrupa_df(gastos,
                                self.config['agrupa_gastos_ind']['categorias'],
                                self.config['agrupa_gastos_ind']['numericas'],
                                operaciones = ['sum'])

                gastosxotro = pd.merge(ventas_acum, gas_agrup, on = self.config['union_indirecta_cxo'],how='left').fillna(0)

            gastosxotro['porc_costo_x_otros'] = np.where(gastosxotro['ventas_acumuladas_sum'] != 0, gastosxotro['gasto_sum'] / gastosxotro['ventas_acumuladas_sum'], np.nan)
            del gastosxotro['ventas_acumuladas_sum']
            del gastosxotro['gasto_sum']

            return  gastosxotro
        except Exception as e:
            return False, f"❌ al configurar archivos yml del costo por otros {str(e)}", None 
    
    def ajus_gastos_entrega_fijos(self, modelo = 'Directa'):
        '''
        Funcion que ajusta los gastos y devuelve data frames, con filtros respectivos.
        ARG: Modelo: str
        return: dd 
        '''
        try:
            ventas = self.ventas.copy()
            gastos = self.gastos.copy()
            gastosxotro = pd.DataFrame()
            if modelo == 'Directa':
                ventas_directa = filtrar_dataframe(ventas,self.config['filtros_modelo_directa'])            
                gastos_dir = filtrar_dataframe(gastos,self.config['gastos_entrega_fijos_directa']['filtros_excluir'],modo='excluir')
                gastos_dir = filtrar_dataframe(gastos,self.config['gastos_entrega_fijos_directa']['filtros_incluir'])
                ventas_acum_dir  = agrupa_df(ventas_directa,
                                            self.config['agrupa_vta_gxotro_directa']['categorias'],
                                            self.config['agrupa_vta_gxotro_directa']['numericas'],
                                            operaciones=['sum'])

                gas_agr_dir = agrupa_df(gastos_dir,
                                       self.config['agrupa_gastos_dir']['categorias'],
                                       self.config['agrupa_gastos_dir']['numericas'],
                                       operaciones = ['sum'])
                gastosxotro = pd.merge(ventas_acum_dir, gas_agr_dir, on = self.config['union_directa_cxo'],how='left').fillna(0)
                gastosxotro['porc_costo_fijo_entrega'] = np.where(gastosxotro['ventas_acumuladas_sum'] != 0, gastosxotro['gasto_sum'] / gastosxotro['ventas_acumuladas_sum'], np.nan)

            else:
                ventas_indirecta = filtrar_dataframe(ventas,self.config['filtros_modelo_indirecta'])      
                gastos_ind = filtrar_dataframe(gastos,self.config['gastos_entrega_fijos_indirecta']['filtros_excluir'],modo='excluir')
                gastos_ind = filtrar_dataframe(gastos_ind,self.config['gastos_entrega_fijos_indirecta']['filtros_incluir'])    
                ventas_acum_ind  = agrupa_df(ventas_indirecta,
                                                 self.config['agrupa_vta_gxotro_indirecta']['categorias'],
                                                 self.config['agrupa_vta_gxotro_indirecta']['numericas'],
                                                 operaciones=['sum'])
                gas_agr_ind = agrupa_df(gastos_ind,
                                       self.config['agrupa_gastos_ind']['categorias'],
                                       self.config['agrupa_gastos_ind']['numericas'],
                                       operaciones = ['sum'])               
                #uniendo las ventasnetas con los costos x otros            
                gastosxotro = pd.merge(ventas_acum_ind,gas_agr_ind , on = self.config['union_indirecta_cxo'],how='left').fillna(0)                  
            gastosxotro['porc_costo_fijo_entrega'] = np.where(gastosxotro['ventas_acumuladas_sum'] != 0, gastosxotro['gasto_sum'] / gastosxotro['ventas_acumuladas_sum'], np.nan)

            del gastosxotro['ventas_acumuladas_sum']
            del gastosxotro['gasto_sum']
    
            return gastosxotro
        except Exception as e:        
            return False, f"❌ al configurar archivos yml del costo por entrega fija {str(e)}", None 

    def ajus_gastos_entrega_variable(self):
        pass

def ajus_gastos_visita(gastos: pd.DataFrame, coste_por_minuto: pd.DataFrame ,config:str):
    '''
    funcion para calcular los gastos por visita 
    arg: gastos: df
        coste_por_minuto:  df, información de costo_por_minuto
        config: ruta archivo configuración
    '''
    gastos_visita= gastos.copy()

    gastos_visita = filtrar_dataframe(gastos_visita,config['gastos_visita']['filtros_excluir'],modo='excluir')
    gastos_visita = filtrar_dataframe(gastos_visita,config['gastos_visita']['filtros_incluir'])

    gastos_visita = agrupa_df(gastos_visita,
                           config['agrupa_gastos_visita']['categorias'],
                           config['agrupa_gastos_visita']['numericas'],
                           operaciones = ['sum'])
    gastos_visita = pd.merge(gastos_visita, coste_por_minuto, on =config['union_gasto_visita'],how='left')

    return  gastos_visita





def ajus_gastos_entrega_fijos(gas_entr_fijo: pd.DataFrame, ventas: pd.DataFrame,  config:str):
    '''
    Funcion que ajusta los gastos y devuelve data frames, con filtros respectivos.
    ARG: Data: pd.DataFrame información gastos
    return: df1, df2   
    '''
 
    ventas_directa = filtrar_dataframe(ventas,config['filtros_modelo_directa'])
    ventas_indirecta = filtrar_dataframe(ventas,config['filtros_modelo_indirecta'])
    gastos_dir = gas_entr_fijo.copy()
    
    gastos_dir = filtrar_dataframe(gastos_dir,config['gastos_entrega_fijos_directa']['filtros_excluir'],modo='excluir')
    gastos_dir = filtrar_dataframe(gastos_dir,config['gastos_entrega_fijos_directa']['filtros_incluir'])

    gastos_ind = gas_entr_fijo.copy()
    gastos_ind = filtrar_dataframe(gastos_ind,config['gastos_entrega_fijos_indirecta']['filtros_excluir'],modo='excluir')
    gastos_ind = filtrar_dataframe(gastos_ind,config['gastos_entrega_fijos_indirecta']['filtros_incluir'])

    ventas_acum_dir  = agrupa_df(ventas_directa,
                                     config['agrupa_vta_gxotro_directa']['categorias'],
                                     config['agrupa_vta_gxotro_directa']['numericas'],
                                     operaciones=['sum'])

    ventas_acum_ind  = agrupa_df(ventas_indirecta,
                                     config['agrupa_vta_gxotro_indirecta']['categorias'],
                                     config['agrupa_vta_gxotro_indirecta']['numericas'],
                                     operaciones=['sum'])
    
    gas_agr_dir = agrupa_df(gastos_dir,
                           config['agrupa_gastos_dir']['categorias'],
                           config['agrupa_gastos_dir']['numericas'],
                           operaciones = ['sum'])
    
    gas_agr_ind = agrupa_df(gastos_ind,
                           config['agrupa_gastos_ind']['categorias'],
                           config['agrupa_gastos_ind']['numericas'],
                           operaciones = ['sum'])
    #uniendo las ventasnetas con los costos x otros
    gastosxotro_dir = pd.merge(ventas_acum_dir, gas_agr_dir, on = config['union_directa_cxo'],how='left').fillna(0)
    gastosxotro_ind = pd.merge(ventas_acum_ind,gas_agr_ind , on = config['union_indirecta_cxo'],how='left').fillna(0)
    #calculando costo por otros
    gastosxotro_dir['porc_costo_fijo_entrega'] = np.where(gastosxotro_dir['ventas_acumuladas_sum'] != 0, gastosxotro_dir['gasto_sum'] / gastosxotro_dir['ventas_acumuladas_sum'], np.nan)
    gastosxotro_ind['porc_costo_fijo_entrega'] = np.where(gastosxotro_ind['ventas_acumuladas_sum'] != 0, gastosxotro_ind['gasto_sum'] / gastosxotro_ind['ventas_acumuladas_sum'], np.nan)
    
  
    del gastosxotro_dir['ventas_acumuladas_sum']
    del gastosxotro_dir['gasto_sum']

    del gastosxotro_ind['ventas_acumuladas_sum']
    del gastosxotro_ind['gasto_sum']
    
    return gastosxotro_dir, gastosxotro_ind


def asignacion_costos_entrega_variables(gastos_entrega:pd.DataFrame,ventas: pd.DataFrame ,config:str):
    '''
    Funcion que ajusta los gastos de entrega variables.
    '''
    ventas_directa = filtrar_dataframe(ventas,config['filtros_modelo_directa'])
    ventas_indirecta = filtrar_dataframe(ventas,config['filtros_modelo_indirecta'])

    gastosdir= gastos_entrega.copy()
    gastosdir = filtrar_dataframe(gastosdir,config['gastos_entrega_variable_directa']['filtros_excluir'],modo='excluir')
    gastosdir = filtrar_dataframe(gastosdir,config['gastos_entrega_variable_directa']['filtros_incluir'])

    gastosind= gastos_entrega.copy()
    gastosind = filtrar_dataframe(gastosind,config['gastos_entrega_variable_indirecta']['filtros_excluir'],modo='excluir')
    gastosind = filtrar_dataframe(gastosind,config['gastos_entrega_variable_indirecta']['filtros_incluir'])

    ventas_acum_dir  = agrupa_df(ventas_directa,
                                     config['agrupa_vta_gxotro_directa']['categorias'],
                                     config['agrupa_vta_gxotro_directa']['numericas'],
                                     operaciones=['sum'])

    ventas_acum_ind  = agrupa_df(ventas_indirecta,
                                     config['agrupa_vta_gxotro_indirecta']['categorias'],
                                     config['agrupa_vta_gxotro_indirecta']['numericas'],
                                     operaciones=['sum'])
    
    gastosdir = agrupa_df(gastosdir,
                           config['agrupa_gastos_dir']['categorias'],
                           config['agrupa_gastos_dir']['numericas'],
                           operaciones = ['sum'])
    
    gastosind = agrupa_df(gastosind,
                           config['agrupa_gastos_ind']['categorias'],
                           config['agrupa_gastos_ind']['numericas'],
                           operaciones = ['sum'])

    gastosxotro_dir = pd.merge(ventas_acum_dir, gastosdir, on = config['union_directa_cxo'],how='left').fillna(0)
    gastosxotro_ind = pd.merge(ventas_acum_ind,gastosind , on = config['union_indirecta_cxo'],how='left').fillna(0)
    #calculando costo por otros
    gastosxotro_dir['porc_costo_variable_entrega'] = np.where(gastosxotro_dir['ventas_acumuladas_sum'] != 0, gastosxotro_dir['gasto_sum'] / gastosxotro_dir['ventas_acumuladas_sum'], np.nan)
    gastosxotro_ind['porc_costo_variable_entrega'] = np.where(gastosxotro_ind['ventas_acumuladas_sum'] != 0, gastosxotro_ind['gasto_sum'] / gastosxotro_ind['ventas_acumuladas_sum'], np.nan)
    
  
    del gastosxotro_dir['ventas_acumuladas_sum']
    del gastosxotro_dir['gasto_sum']

    del gastosxotro_ind['ventas_acumuladas_sum']
    del gastosxotro_ind['gasto_sum']
    return gastosxotro_dir, gastosxotro_ind