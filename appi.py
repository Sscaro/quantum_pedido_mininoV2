import streamlit as st
import pandas as pd
import yaml
import io
import os
import glob
import time
from typing import Dict, Any, Optional, Tuple
from utils.utils import procesar_configuracion
from utils.utils import read_file
from utils.ajustes_archivos import ajustar_archivo_afo, ajustes_archivo_universos

ruta_config =  os.path.join(os.getcwd(),'config','config.yml') # archivo yml para configurar archivos de excel
ruta_parametros = os.path.join(os.getcwd(),'config','params.yml') # parametros y valores constantes del breakeven
config = procesar_configuracion(ruta_config)
parametros = procesar_configuracion(ruta_parametros)


def cargar_archivos_desde_carpeta(folder_path: str) -> Dict[str, Any]:
    """
    Carga automáticamente archivos Excel desde una carpeta siguiendo el orden de file_configs
    """
    archivos_cargados = {}
    file_patterns = {
        'ventas': ['*venta*', '*AFOventa*', '*afo_venta*'],
        'gastos': ['*gasto*', '*expense*'],
        'facturas': ['*factura*', '*AFOfactura*', '*invoice*'],
        'universo_directa': ['*universo*directa*', '*cliente*directa*', '*maestra*directa*'],
        'universo_indirecta': ['*universo*indirecta*', '*cliente*indirecta*', '*maestra*indirecta*'],
        'costo_por_minuto': ['*costo*minuto*', '*cost*minute*'],
        'costo_merc_vend': ['*costo*mercancia*', '*cost*merchandise*', '*cmv*']
    }
    
    try:
        excel_files = glob.glob(os.path.join(folder_path, "*.xlsx")) + glob.glob(os.path.join(folder_path, "*.xls"))
        
        for file_key, patterns in file_patterns.items():
            for pattern in patterns:
                matching_files = [f for f in excel_files if any(p.lower().replace('*', '') in os.path.basename(f).lower() for p in [pattern])]
                if matching_files:
                    archivo_path = matching_files[0]  # Tomar el primer archivo que coincida
                    archivos_cargados[file_key] = archivo_path
                    break
        
        return archivos_cargados
    except Exception as e:
        st.error(f"Error al cargar archivos desde carpeta: {str(e)}")
        return {}


def guardar_parametros(parametros_actualizados: Dict[str, Any]) -> bool:
    """
    Guarda los parámetros actualizados en el archivo params.yml
    """
    try:
        with open(ruta_parametros, 'w', encoding='utf-8') as file:
            yaml.dump(parametros_actualizados, file, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        st.error(f"Error al guardar parámetros: {str(e)}")
        return False


def mostrar_editor_parametros():
    """
    Muestra un editor para los parámetros del archivo params.yml
    """
    st.subheader("⚙️ Editor de Parámetros")
    global parametros
    # Crear una copia de los parámetros para editar
    if 'parametros_editados' not in st.session_state:
        st.session_state.parametros_editados = parametros.copy()
    
    # Editor para anio_mes
    st.write("**Configuración de Meses:**")
    
    # Mostrar los meses actuales
    meses_actuales = st.session_state.parametros_editados.get('anio_mes', [])
    
    # Crear columnas para organizar mejor
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Editor de meses existentes
        meses_editados = []
        for i, mes in enumerate(meses_actuales):
            nuevo_mes = st.text_input(f"Mes {i+1}:", value=mes, key=f"mes_{i}")
            if nuevo_mes.strip():
                meses_editados.append(nuevo_mes.strip())
        
        # Opción para agregar nuevo mes
        nuevo_mes = st.text_input("Agregar nuevo mes:", key="nuevo_mes_input")
        if st.button("➕ Agregar Mes") and nuevo_mes.strip():
            meses_editados.append(nuevo_mes.strip())
            st.session_state.parametros_editados['anio_mes'] = meses_editados
            st.rerun()
    
    with col2:
        st.write("**Acciones:**")
        if st.button("🗑️ Limpiar Lista"):
            st.session_state.parametros_editados['anio_mes'] = []
            st.rerun()
        
        if st.button("🔄 Restaurar Original"):
            st.session_state.parametros_editados = parametros.copy()
            st.rerun()
    
    # Actualizar los meses editados
    st.session_state.parametros_editados['anio_mes'] = meses_editados
    
    # Mostrar vista previa
    st.write("**Vista Previa de Configuración:**")
    st.code(yaml.dump(st.session_state.parametros_editados, default_flow_style=False), language='yaml')
    
    # Botones de acción
    col_save, col_cancel = st.columns(2)
    
    with col_save:
        if st.button("💾 Guardar Cambios", type="primary", use_container_width=True):
            if guardar_parametros(st.session_state.parametros_editados):
                st.success("✅ Parámetros guardados correctamente")
                # Recargar parámetros globales
              
                parametros = procesar_configuracion(ruta_parametros)
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Error al guardar los parámetros")
    
    with col_cancel:
        if st.button("❌ Cancelar Cambios", use_container_width=True):
            st.session_state.parametros_editados = parametros.copy()
            st.rerun()


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


def main():
    st.set_page_config(
        page_title="Sistema Breakeven CN",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Sistema Actualización breakeven CN")
    st.markdown("---")
    
    # Inicializar session state
    if 'dataframes' not in st.session_state:
        st.session_state.dataframes = {}
    if 'validation_status' not in st.session_state:
        st.session_state.validation_status = {}
    if 'archivos_validados' not in st.session_state:
        st.session_state.archivos_validados = False
    if 'calculo_completado' not in st.session_state:
        st.session_state.calculo_completado = False
    if 'resultado_calculo' not in st.session_state:
        st.session_state.resultado_calculo = None
    if 'mostrar_resultado' not in st.session_state:
        st.session_state.mostrar_resultado = False
    
    # Crear tabs para organizar la interfaz
    tab1, tab2, tab3 = st.tabs(["📁 Carga de Archivos", "📂 Carga desde Carpeta", "⚙️ Configuración"])
    
    # Definir archivos a cargar
    file_configs = {
        'ventas': {
            'label': '📈 Carga Aqui archivos AFO Ventas',
            'help': 'Archivo Excel con datos de ventas (cod_cliente, Agente, canal, sub canal, meses...)'
        },
        'gastos': {
            'label': '💸 Carga aquí archivos de gasto',
            'help': 'Archivo Excel con datos de gastos (cod_oficina, tipo gasto, sub canal, gasto, modelo atencion, agrupa costo)'
        },
        'facturas': {
            'label': '🧾 Carga aquí tus AFO de Facturas',
            'help': 'Archivo Excel con datos de facturas (cod_cliente, agente, num_facturas)'
        },
        'universo_directa': {
            'label': '📦 Carga aquí maestra de clientes directa',
            'help': 'Archivo Excel con maestra de clientes directa (cod_cliente, func_in, Num visitas)'
        },
        'universo_indirecta': {
            'label': '👥 Carga archivo universo de clientes Indirecta',
            'help': 'Archivo Excel con datos de clientes indirecta (cod_agente, cod_cliente, cod_vendedor, num_vistas)'
        },
        'costo_por_minuto': {
            'label': '⏱️ Carga archivo de costo por minuto',
            'help': 'Archivo Excel con datos de costo por minuto (cod_oficina, modelo_atencion, num_vendedores, tiempo_prom_atencion, tiempo_prom_entre_cliente)'
        },
        'costo_merc_vend': {
            'label': '💰 Carga costo mercancia vendida',
            'help': 'Archivo AFO costo mercancia vendida (cod_oficina, cod_ramo, ingresos_totales)'
        }
    }
    
    # TAB 1: Carga manual de archivos
    with tab1:    
        st.subheader("📁 Carga Manual de Archivos")
        # Crear sección para cada archivo
        for file_key, file_info in file_configs.items():
            with st.expander(file_info['label'], expanded=False):
                uploaded_file = st.file_uploader(
                    f"Selecciona el archivo",
                    type=['xlsx', 'xls'],
                    key=f"file_{file_key}",
                    help=file_info['help']
                    )
                    
                if uploaded_file is not None:
                    # Guardar archivo temporalmente
                    temp_path = f"temp_{file_key}.xlsx"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    is_valid, message, processed_df = procesar_archivo(file_key, temp_path)
                                           
                    # Mostrar el resultado
                    if is_valid:
                        st.success(message)
                        st.session_state.dataframes[file_key] = processed_df
                        st.session_state.validation_status[file_key] = True
                        # Reset estados al cargar nuevos archivos
                        st.session_state.archivos_validados = False
                        st.session_state.calculo_completado = False
                        st.session_state.mostrar_resultado = False
                        
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
                else:
                    st.session_state.validation_status[file_key] = False
                    if file_key in st.session_state.dataframes:
                        del st.session_state.dataframes[file_key]
         
          
            
        # Mostrar resumen
        loaded_count = sum(st.session_state.validation_status.values())
        total_count = len(file_configs)
            
        st.metric(
            label="Archivos Cargados",
            value=f"{loaded_count}/{total_count}",
            delta=f"{(loaded_count/total_count)*100:.0f}% completado"
        )
        
    # TAB 2: Carga desde carpeta
    with tab2:
        st.subheader("📂 Carga Automática desde Carpeta")
        st.info("Sube una carpeta con archivos Excel y el sistema intentará cargarlos automáticamente según sus nombres.")
        
        # Crear uploader de múltiples archivos
        uploaded_files = st.file_uploader(
            "Selecciona múltiples archivos Excel desde una carpeta",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            key="folder_files"
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🚀 Cargar Archivos Automáticamente", disabled=not uploaded_files, type="primary"):
                if uploaded_files:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Mapeo de nombres de archivos a tipos
                    file_mapping = {}
                    
                    # Patrones para identificar archivos
                    patterns = {
                        'ventas': ['venta', 'afo_venta', 'afoventas'],
                        'gastos': ['gasto', 'expense'],
                        'facturas': ['factura', 'afo_factura', 'afofacturas', 'invoice'],
                        'universo_directa': ['universo_directa', 'cliente_directa', 'maestra_directa', 'directa'],
                        'universo_indirecta': ['universo_indirecta', 'cliente_indirecta', 'maestra_indirecta', 'indirecta'],
                        'costo_por_minuto': ['costo_minuto', 'cost_minute', 'minuto'],
                        'costo_merc_vend': ['costo_mercancia', 'cost_merchandise', 'cmv', 'mercancia']
                    }
                    
                    # Identificar archivos
                    for uploaded_file in uploaded_files:
                        filename = uploaded_file.name.lower()
                        for file_type, file_patterns in patterns.items():
                            if any(pattern in filename for pattern in file_patterns):
                                file_mapping[file_type] = uploaded_file
                                break
                    
                    # Procesar archivos identificados
                    total_files = len(file_mapping)
                    processed_files = 0
                    
                    for file_key, uploaded_file in file_mapping.items():
                        status_text.text(f"Procesando: {file_key.replace('_', ' ').title()}...")
                        
                        # Guardar archivo temporalmente
                        temp_path = f"temp_{file_key}.xlsx"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        is_valid, message, processed_df = procesar_archivo(file_key, temp_path)
                        
                        # Limpiar archivo temporal
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        
                        if is_valid:
                            st.session_state.dataframes[file_key] = processed_df
                            st.session_state.validation_status[file_key] = True
                            st.success(f"✅ {file_key.replace('_', ' ').title()}: {message}")
                        else:
                            st.session_state.validation_status[file_key] = False
                            st.error(f"❌ {file_key.replace('_', ' ').title()}: {message}")
                        
                        processed_files += 1
                        progress_bar.progress(processed_files / total_files)
                    
                    status_text.text("¡Carga completada!")
                    
                    # Reset estados al cargar nuevos archivos
                    st.session_state.archivos_validados = False
                    st.session_state.calculo_completado = False
                    st.session_state.mostrar_resultado = False
                    
                    # Mostrar resumen
                    loaded_count = sum(st.session_state.validation_status.values())
                    st.success(f"Proceso completado: {loaded_count} de {len(file_configs)} archivos cargados correctamente")
        
        with col2:
            if uploaded_files:
                st.write("**Archivos seleccionados:**")
                for file in uploaded_files:
                    st.write(f"📄 {file.name}")
    
    # TAB 3: Configuración
    with tab3:
        mostrar_editor_parametros()
    
    # ÁREA PRINCIPAL PARA MOSTRAR RESULTADOS
    if st.session_state.mostrar_resultado and st.session_state.resultado_calculo is not None:
        st.markdown("---")
        st.header("📊 Resultados del Análisis Breakeven")
        
        resultado = st.session_state.resultado_calculo
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Filas Procesadas", f"{len(resultado):,}")
        with col2:
            st.metric("Columnas Generadas", len(resultado.columns))
        with col3:
            if 'ventas_acumuladas' in resultado.columns:
                total_ventas = resultado['ventas_acumuladas'].sum()
                st.metric("Total Ventas", f"${total_ventas:,.2f}")
        with col4:
            if 'ventas_promedio' in resultado.columns:
                promedio_ventas = resultado['ventas_promedio'].mean()
                st.metric("Promedio Ventas", f"${promedio_ventas:,.2f}")
        
        # Pestañas para organizar los resultados
        result_tab1, result_tab2, result_tab3 = st.tabs(["📈 Vista Previa", "📊 Estadísticas", "💾 Descarga"])
        
        with result_tab1:
            st.subheader("Vista Previa de Datos Procesados")
            st.dataframe(resultado.head(20), use_container_width=True)
        
        with result_tab2:
            st.subheader("Estadísticas Generales")
            if 'ventas_acumuladas' in resultado.columns:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write("**Resumen de Ventas:**")
                    st.write(resultado['ventas_acumuladas'].describe())
                with col_b:
                    if 'modelo_atencion' in resultado.columns:
                        st.write("**Distribución por Modelo de Atención:**")
                        distribucion = resultado['modelo_atencion'].value_counts()
                        st.write(distribucion)
        
        with result_tab3:
            st.subheader("Descargar Resultados")
            st.info("💡 Los resultados están listos para descarga en formato Excel")
            
            # Crear archivo Excel en memoria
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                resultado.to_excel(writer, sheet_name='Resultado_Breakeven', index=False)
            
            output.seek(0)
            
            # Botón de descarga principal
            st.download_button(
                label="📥 Descargar Resultado Excel",
                data=output.getvalue(),
                file_name=f"resultado_breakeven_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )
            
            st.success("✅ Archivo preparado para descarga")
    
    # Panel lateral con estado general y botones de control
    with st.sidebar:
        st.header("📊 Panel de Control")
        
        # Estado general
        loaded_count = sum(st.session_state.validation_status.values())
        total_count = len(file_configs)
              
        st.metric(
            label="Estado General",
            value=f"{loaded_count}/{total_count}",
            delta=f"{(loaded_count/total_count)*100:.0f}% completado"
        )
        
        # Lista de archivos cargados
        st.write("**Estado de Archivos:**")
        for file_key, file_info in file_configs.items():
            status = st.session_state.validation_status.get(file_key, False)
            icon = "✅" if status else "❌"
            st.write(f"{icon} {file_key.replace('_', ' ').title()}")
        
        st.markdown("---")        
        # Botón de validación inicial
        
        # Botón de cálculo (independiente del de validación)
        calculo_disponible = 'ventas' in st.session_state.dataframes
        
        if st.button(
            "🧮 Realizar Cálculos",
            disabled=not calculo_disponible or st.session_state.calculo_completado,
            use_container_width=True,
            type="primary" if calculo_disponible and not st.session_state.calculo_completado else "secondary"
        ):
            if calculo_disponible:
                try:
                    # Mostrar proceso de cálculo con status
                    with st.status("⚙️ Realizando cálculos...", expanded=True) as status:
                        st.write("Preparando datos de ventas...")
                        time.sleep(0.8)
                        st.write("Aplicando transformaciones AFO...")

                        # Aquí se realiza el cálculo real
                        data_ventas_ajustada = ajustar_archivo_afo(
                            st.session_state.dataframes['ventas'],
                            config,
                            parametros['anio_mes']
                        )                     
                        st.session_state.resultado_calculo = data_ventas_ajustada

                        st.write("Calculando métricas de negocio...")
                        time.sleep(0.8)
                        st.write("Procesando análisis temporal...")
                        time.sleep(0.8)
                        st.write("Generando resultados finales...")
                        time.sleep(0.8)

                        status.update(label="✅ Cálculos completados exitosamente!", state="complete", expanded=False)

                    st.session_state.calculo_completado = True
                    st.session_state.mostrar_resultado = True

                    st.success("🎉 Cálculos completados correctamente")
                    st.info("📊 Los resultados se muestran en el área principal arriba")

                    time.sleep(1)
                    #st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error durante el cálculo: {str(e)}")
                    st.session_state.calculo_completado = False
        
        # Mostrar estado del cálculo
        if st.session_state.calculo_completado:
            st.success("✅ Cálculos completados")
        elif st.session_state.archivos_validados:
            st.info("💡 Listo para realizar cálculos")     
        else:
            st.warning("⚠️ Carga todos los archivos requeridos")

        st.markdown("---")
        
        # Botón para limpiar datos
        if st.button("🗑️ Limpiar Todos los Datos", use_container_width=True):
            st.session_state.dataframes = {}
            st.session_state.validation_status = {}
            st.session_state.archivos_validados = False
            st.session_state.calculo_completado = False
            st.session_state.resultado_calculo = None
            st.session_state.mostrar_resultado = False
            st.success("Datos limpiados correctamente")
            st.rerun()

if __name__ == "__main__":
    main()