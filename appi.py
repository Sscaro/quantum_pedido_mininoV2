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
            return lectura_archivos.dfarchivoAFO(columnas_facturas, hoja_nombre='AFO', n=1, types=config[file_key]['columns'])
        
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
    
    # Crear tabs para organizar la interfaz
    tab1, tab2, tab3 = st.tabs(["📁 Carga de Archivos", "📂 Carga desde Carpeta", "⚙️ Configuración"])
    
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
            'help': 'Archivo Excel con maestra de clientes directa (codigo_producto, nombre_producto, categoria, stock_actual, precio_compra, precio_venta)'
        },
        'universo_indirecta': {
            'label': '👥 Carga archivo universo de clientes Indirecta',
            'help': 'Archivo Excel con datos de clientes indirecta (id_empleado, nombre_completo, departamento, salario, fecha_ingreso)'
        },
        'costo_por_minuto': {
            'label': '⏱️ Carga archivo de costo por minuto',
            'help': 'Archivo Excel con datos de costo por minuto (id_empleado, nombre_completo, departamento, salario, fecha_ingreso)'
        },
        'costo_merc_vend': {
            'label': '💰 Carga costo mercancia vendida',
            'help': 'Archivo AFO costo mercancia vendida (id_empleado, nombre_completo, departamento, salario, fecha_ingreso)'
        }
    }
    
    # TAB 1: Carga manual de archivos
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
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
        
        with col2:
            st.subheader("✅ Lista de Chequeo")
            
            # Mostrar estado de cada archivo
            all_valid = True
            for file_key, file_info in file_configs.items():
                status = st.session_state.validation_status.get(file_key, False)
                if status:
                    st.success(f"✅ {file_key.replace('_', ' ').title()}")
                else:
                    st.error(f"❌ {file_key.replace('_', ' ').title()}")
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
    
    # Panel lateral con estado general y botón de cálculo
    with st.sidebar:
        st.header("📊 Panel de Control")
        
        # Estado general
        loaded_count = sum(st.session_state.validation_status.values())
        total_count = len(file_configs)
        all_valid = loaded_count == total_count
        
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
        
        # Botón de cálculo mejorado
        if st.button(
            "🚀 Iniciar Cálculo",
            disabled=not all_valid,
            use_container_width=True,
            type="primary" if all_valid else "secondary"
        ):
            if all_valid:
                # Mostrar proceso de cálculo
                st.success("¡Iniciando proceso de cálculo!")
                
                # Barra de progreso simulada
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Simular proceso de cálculo
                steps = [
                    "Validando datos de entrada...",
                    "Procesando archivo de ventas...",
                    "Analizando gastos...",
                    "Calculando facturas...",
                    "Procesando universo de clientes...",
                    "Calculando costos por minuto...",
                    "Generando análisis de breakeven...",
                    "Finalizando cálculos..."
                ]
                
                for i, step in enumerate(steps):
                    status_text.text(f"⏳ {step}")
                    time.sleep(0.5)  # Simular tiempo de procesamiento
                    progress_bar.progress((i + 1) / len(steps))
                
                status_text.text("✅ ¡Proceso completado!")
                st.balloons()
                
                # Mostrar información de los DataFrames procesados
                with st.expander("📊 Resumen de Datos Procesados", expanded=True):
                    for file_key, df in st.session_state.dataframes.items():
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(f"{file_key.replace('_', ' ').title()}", f"{len(df):,}", "filas")
                        with col2:
                            st.metric("Columnas", len(df.columns))
                        with col3:
                            memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024
                            st.metric("Memoria", f"{memory_usage:.1f} MB")
            else:
                st.warning("⚠️ Completa la carga de todos los archivos para continuar")
        
        # Botón para limpiar datos
        if st.button("🗑️ Limpiar Todos los Datos", use_container_width=True):
            st.session_state.dataframes = {}
            st.session_state.validation_status = {}
            st.success("Datos limpiados correctamente")
            st.rerun()


if __name__ == "__main__":
    main()