# Modulo para realizar ajustes de los gastos.
import pandas as pd
import numpy as np
from utils.utils import agrupa_df
from utils.utils import filtrar_dataframe
from utils.utils import Registro_tiempo

 

class configuracion_gastos:
    '''
    Clase para realizar ajustes de los gastos.
    '''
    def __init__(self, ventas:pd.DataFrame,gasto:pd.DataFrame ,config: dict):
        
        self.config = config
        self.ventas = ventas
        self.gastos = gasto
    @Registro_tiempo
    def ajustar_archivo_cogs(self, data: pd.DataFrame):
        '''
        funcion que realiza ajustes del archivo de los cogs
        ARG: data: DF

        return df
        '''     
        data = data.fillna(0)
        #divide los ingresos sobre los gastos de la mercancia, si no hay ingresos deja por defecto 0.
        columnas = list(self.config['costo_merc_vend']['columns'].keys())
        data['porc_cogs']= np.where(data[columnas[4]] != 0, data[columnas[5]] / data[columnas[4]], np.nan)
        data = data[[columnas[0], columnas[2],'porc_cogs']]
        data = data.drop_duplicates(keep='first')
        return data
    @Registro_tiempo
    def ajustes_gastos_por_otros(self, modelo = 'directa'):
        data_gastos = self.gastos.copy()
        gastosxotro = pd.DataFrame()
        try:
            ventas = filtrar_dataframe(self.ventas,self.config['filtros'][modelo])
            gastos = filtrar_dataframe(data_gastos,self.config['gastos_por_otros'][modelo]['filtros_excluir'],modo='excluir')
            gastos = filtrar_dataframe(data_gastos,self.config['gastos_por_otros'][modelo]['filtros_incluir'])
            ventas_acum  = agrupa_df(ventas,
                                        self.config['agrupa_vta_gxotro'][modelo]['categorias'],
                                        self.config['agrupa_vta_gxotro'][modelo]['numericas'],
                                        operaciones=['sum'])
            gas_agrup = agrupa_df(gastos,
                            self.config['agrupa_gastos'][modelo]['categorias'],
                            self.config['agrupa_gastos'][modelo]['numericas'],
                            operaciones = ['sum'] )
            gastosxotro = pd.merge(ventas_acum, gas_agrup, on = self.config['union_cxo'][modelo],how='left').fillna(0)
            gastosxotro['porc_costo_x_otros'] = np.where(gastosxotro['ventas_acumuladas_sum'] != 0, gastosxotro['gasto_sum'] / gastosxotro['ventas_acumuladas_sum'], np.nan)
            del gastosxotro['ventas_acumuladas_sum']
            del gastosxotro['gasto_sum']    
            return  gastosxotro
        except Exception as e:
           return False, f"❌ al configurar archivos yml del costo por otros {str(e)}", None 
    
    def ajus_gastos_entrega_fijos(self, modelo = 'directa'):
        '''
        Funcion que ajusta los gastos y devuelve data frames, con filtros respectivos.
        ARG: Modelo: str
        return: dd 
        '''
        try:
            ventas = self.ventas.copy()
            gastos = self.gastos.copy()     
            ventas = filtrar_dataframe(ventas,self.config['filtros'][modelo])            
            gastos = filtrar_dataframe(gastos,self.config['gastos_entrega_fijos'][modelo]['filtros_excluir'],modo='excluir')
            gastos = filtrar_dataframe(gastos,self.config['gastos_entrega_fijos'][modelo]['filtros_incluir'])
            ventas_acum  = agrupa_df(ventas,
                                        self.config['agrupa_vta_gxotro'][modelo]['categorias'],
                                        self.config['agrupa_vta_gxotro'][modelo]['numericas'],
                                        operaciones=['sum'])
            gas_agr = agrupa_df(gastos,
                                   self.config['agrupa_gastos'][modelo]['categorias'],
                                   self.config['agrupa_gastos'][modelo]['numericas'],
                                   operaciones = ['sum'])
            gastosxotro = pd.merge(ventas_acum, gas_agr, on = self.config['union_cxo'][modelo],how='left').fillna(0)
            gastosxotro['porc_costo_fijo_entrega'] = np.where(gastosxotro['ventas_acumuladas_sum'] != 0, gastosxotro['gasto_sum'] / gastosxotro['ventas_acumuladas_sum'], np.nan)
            del gastosxotro['ventas_acumuladas_sum']
            del gastosxotro['gasto_sum']
        
            return gastosxotro
        except Exception as e:        
           return False, f"❌ algo fallo en la funcion ajus_gastos_entrega_fijos {str(e)}", None 

    def ajus_gastos_entrega_variable(self, modelo = 'directa'):
        try:
            ventas = self.ventas.copy()
            gastos = self.gastos.copy()
        
            ventas = filtrar_dataframe(ventas,self.config['filtros'][modelo])
            gastos = filtrar_dataframe(gastos,self.config['gastos_entrega_variable'][modelo]['filtros_excluir'],modo='excluir')
            gastos = filtrar_dataframe(gastos,self.config['gastos_entrega_variable'][modelo]['filtros_incluir'])
            ventas_acum  = agrupa_df(ventas,
                                         self.config['agrupa_vta_gxotro'][modelo]['categorias'],
                                         self.config['agrupa_vta_gxotro'][modelo]['numericas'],
                                         operaciones=['sum'])
            gastos = agrupa_df(gastos,
                               self.config['agrupa_gastos'][modelo]['categorias'],
                               self.config['agrupa_gastos'][modelo]['numericas'],
                               operaciones = ['sum'])
            gastos = pd.merge(ventas_acum, gastos, on = self.config['union_cxo'][modelo],how='left').fillna(0)
            gastos['porc_costo_variable_entrega'] = np.where(gastos['ventas_acumuladas_sum'] != 0, gastos['gasto_sum'] / gastos['ventas_acumuladas_sum'], np.nan)
            del gastos['ventas_acumuladas_sum']
            del gastos['gasto_sum']
            return gastos
        except Exception as e:        
            return False, f"❌ algo fallo en la funcion ajus_gastos_entrega_variable {str(e)}", None

    def ajus_gastos_visita(self, coste_por_minuto: pd.DataFrame):
        '''
        funcion para calcular los gastos por visita 
        arg: gastos: df
            coste_por_minuto:  df, información de costo_por_minuto
            config: ruta archivo configuración
        '''
        try:
            gastos_visita = filtrar_dataframe(self.gastos,self.config['gastos_visita']['filtros_excluir'],modo='excluir')
            gastos_visita = filtrar_dataframe(gastos_visita,self.config['gastos_visita']['filtros_incluir'])
            gastos_visita = agrupa_df(gastos_visita,
                                   self.config['agrupa_gastos_visita']['categorias'],
                                   self.config['agrupa_gastos_visita']['numericas'],
                                   operaciones = ['sum'])
            gastos_visita = pd.merge(gastos_visita, coste_por_minuto, on =self.config['union_gasto_visita'],how='left')
            #del gastos_visita['ventas_acumuladas_sum']
            #del gastos_visita['gasto_sum']
            return  gastos_visita
        except Exception as e:
            False, f"❌ algo fallo en la funcion ajus_gastos_visita {str(e)}", None
        
