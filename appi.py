
import streamlit as st
import pandas as pd
import yaml
import io
import os
from typing import Dict, Any, Optional, Tuple
from utils.utils import procesar_configuracion
from utils.utils import read_file


ruta_config =  os.path.join(os.getcwd(),'config','config.yml') # archivo yml para configurar archivos de excel
ruta_parametros = os.path.join(os.getcwd(),'config','params.yml') # parametros y valores constantes del breakeven
config = procesar_configuracion(ruta_config)
parametros = procesar_configuracion(ruta_parametros)


def main():
    st.title("📊 Sistema Actualización breakeven CN")
    st.markdown("---")
    
    # Cargar configuración
    # config = load_config()
    
    # Inicializar session state
    if 'dataframes' not in st.session_state:
        st.session_state.dataframes = {}
    if 'validation_status' not in st.session_state:
        st.session_state.validation_status = {}
    
    # Definir archivos a cargar
    file_configs = {
        'ventas': {
            'label': '📈 Carga Aqui archivos AFO Ventas',
            'help': 'Archivo Excel con datos de ventas (fecha, producto, cantidad, precio_unitario, total)'
        },
        'gastos': {
            'label': '💸 Carga aquí archivos de gasto',
            'help': 'Archivo Excel con datos de gastos (fecha, categoria, descripcion, monto)'
        },
        'facturas': {
            'label': '🧾 Carga aquí tus AFO de Facturas',
            'help': 'Archivo Excel con datos de facturas (numero_factura, fecha_emision, cliente, subtotal, impuestos, total)'
        },
        'universo_directa': {
            'label': '📦 Carga aquí maestra de clientes directa',
            'help': 'Archivo Excel con maestra de clietnes directa (codigo_producto, nombre_producto, categoria, stock_actual, precio_compra, precio_venta)'
        },
        'universo_indirecta': {
            'label': '👥 Carga archivo universo de clientes Indirecta',
            'help': 'Archivo Excel con datos de clientes indirecta (id_empleado, nombre_completo, departamento, salario, fecha_ingreso)'
        },
        'costo_por_minuto': {
            'label': '👥 Carga archivo de costo por minuto',
            'help': 'Archivo Excel con datos de costo por minuto (id_empleado, nombre_completo, departamento, salario, fecha_ingreso)'
        },
        'costo_merc_vend' : {'label': '👥 Carga costo mercancia vendida',
            'help': 'Archivo AFO costo mercancia vendida (id_empleado, nombre_completo, departamento, salario, fecha_ingreso)'}
            
    }
    
    # Crear columnas para la interfaz
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📁 Carga de Archivos")
        
        # Crear sección para cada archivo
        for file_key, file_info in file_configs.items():
            with st.expander(file_info['label'], expanded=True):
                uploaded_file = st.file_uploader(
                    f"Selecciona el archivo",
                    type=['xlsx', 'xls'],
                    key=f"file_{file_key}",
                    help=file_info['help']
                )
                
                if uploaded_file is not None:
                    try:
                        if file_key == "ventas":  # carga archivo afo de ventas
                           columnas_ventas = list(config[file_key]['columns'].keys())+parametros['anio_mes'] #concatena el nombre de las columnas con la lista de meses
                        
                           lectura_archivos = read_file(uploaded_file,'xlsx')
                           is_valid, message, processed_df =  lectura_archivos.dfarchivoAFO(columnas_ventas,n=2)
                        elif file_key == "facturas":  
                            columnas_facturas = (config['facturas']['columns'].keys()) # carga archivo afo de facturas
                            lectura_archivos = read_file(uploaded_file,'xlsx')
                            is_valid, message, processed_df = lectura_archivos.dfarchivoAFO(columnas_facturas, hoja_nombre='AFO', n=1, types= config[file_key]['columns'] )
                        elif file_key == "costo_merc_vend":
                             columnas_facturas = list(config['costo_merc_vend']['columns'].keys())
                             is_valid, message, processed_df = lectura_archivos.dfarchivoAFO(columnas_facturas, hoja_nombre='AFO', n=1, types= config[file_key]['columns'])
                        else:
                            lectura_archivos = read_file(uploaded_file,'xlsx')
                            is_valid, message, processed_df = lectura_archivos.leer_excel(config[file_key])

                        # Validar el DataFrame
                        # is_valid, message, processed_df = validate_dataframe(df, config[file_key])

                        # Mostrar el resultado
                        if is_valid:
                            st.success(message)
                            st.session_state.dataframes[file_key] = processed_df
                            st.session_state.validation_status[file_key] = True

                            # Mostrar preview del DataFrame
                            st.write("**Vista previa:**")
                            st.dataframe(processed_df.head(3), use_container_width=True)

                        else:
                            st.error(message)
                            st.session_state.validation_status[file_key] = False
                            if file_key in st.session_state.dataframes:
                                del st.session_state.dataframes[file_key]

                            # Mostrar información esperada
                            st.write("**Estructura esperada:**")
                            expected_info = pd.DataFrame([
                                {'Columna': col, 'Tipo': dtype} 
                                for col, dtype in config[file_key]['columns'].items()
                            ])
                            st.dataframe(expected_info, use_container_width=True)

                    except Exception as e:
                            st.error(f"❌ Error al leer el archivo: {str(e)}")
                            st.session_state.validation_status[file_key] = False
                            if file_key in st.session_state.dataframes:
                                del st.session_state.dataframes[file_key]
                else:
                    # Si no hay archivo, marcar como no validado
                    st.session_state.validation_status[file_key] = False
                    if file_key in st.session_state.dataframes:
                        del st.session_state.dataframes[file_key]
    
    with col2:
        st.subheader("✅ Lista de Chequeo")
        
        # Mostrar estado de cada archivo
        all_valid = True
        for file_key, file_info in file_configs.items():
            status = st.session_state.validation_status.get(file_key, False)
            if status:
                st.success(f"✅ {file_info['label'].split(' ')[-1]}")
            else:
                st.error(f"❌ {file_info['label'].split(' ')[-1]}")
                all_valid = False
        
        st.markdown("---")
        
        # Mostrar resumen
        loaded_count = sum(st.session_state.validation_status.values())
        total_count = len(file_configs)
        
        st.metric(
            label="Archivos Cargados",
            value=f"{loaded_count}/{total_count}",
            delta=f"{(loaded_count/total_count)*100:.0f}% completado"
        )
        
        # Botón de calcular
        st.markdown("---")
        calculate_button = st.button(
            "🚀 Calcular",
            disabled=not all_valid,
            use_container_width=True,
            type="primary" if all_valid else "secondary"
        )
        
        if calculate_button and all_valid:
            st.success("¡Todos los archivos están listos para el cálculo!")
            st.balloons()
            
            # Aquí puedes agregar tu lógica de cálculo
            with st.expander("📊 Información de DataFrames Cargados"):
                for file_key, df in st.session_state.dataframes.items():
                    st.write(f"**{file_key.capitalize()}**: {len(df)} filas, {len(df.columns)} columnas")
        
        elif not all_valid:
            st.warning("⚠️ Completa la carga de todos los archivos para continuar")
    
    # Sección de configuración (opcional)
    #with st.expander("⚙️ Ver Configuración YAML", expanded=False):
    #    st.code(DEFAULT_CONFIG, language='yaml')
    #    st.info("Esta es la configuración que define la estructura esperada de cada archivo.")

if __name__ == "__main__":
    main()