import pandas as pd
import io
import logging
import streamlit as st
from models.data_processor import DataProcessor

logger = logging.getLogger(__name__)

@st.cache_data(show_spinner=False, ttl=3600)  # Cache por 1 hora para evitar reprocesar
def _cargar_df_nuclear_v7(
    archivo_bytes: bytes, 
    nombre_archivo: str, 
    sla_almacen: int = 1, 
    sla_principal: int = 3, 
    sla_otras: int = 5
) -> tuple:
    """
    Función interna con cache para cargar y procesar archivo Excel.
    
    Args:
        archivo_bytes: Contenido binario del archivo subido
        nombre_archivo: Nombre original del archivo (para logs)
        sla_almacen: Días máximos para despacho desde almacén
        sla_principal: SLA para ciudades principales (Bogotá, Medellín, Cali)
        sla_otras: SLA para otras ciudades
        
    Returns:
        Tupla (DataFrame procesado, nombre de hoja usada) o (None, None) si error
    """
    logger.info(f"Iniciando carga de archivo: {nombre_archivo}")
    
    try:
        # Leer archivo Excel desde bytes en memoria
        xl = pd.ExcelFile(io.BytesIO(archivo_bytes))

        # 🔍 Detectar automáticamente la hoja con datos (flexible a nombres variados)
        hoja = None
        for h in xl.sheet_names:
            if any(kw in h.lower() for kw in ['venta', 'base', 'despacho']):
                hoja = h
                logger.info(f"Hoja detectada: {hoja}")
                break
        if hoja is None:
            hoja = xl.sheet_names[0]  # Fallback: usar primera hoja
            logger.warning(f"Usando hoja por defecto: {hoja}")

        # 🔍 Detectar fila de encabezado dinámicamente (robusto a formatos)
        df_raw = pd.read_excel(
            io.BytesIO(archivo_bytes), 
            sheet_name=hoja, 
            header=None, 
            nrows=10  # Leer solo primeras 10 filas para detectar header
        )
        header_row = 0
        for i in range(len(df_raw)):
            # Buscar palabras clave que indiquen fila de encabezado
            row_vals = ' '.join([str(v).lower() for v in df_raw.iloc[i].values])
            if any(kw in row_vals for kw in ['fecha', 'cliente', 'ciudad', 'no orden']):
                header_row = i
                logger.info(f"Fila de encabezado detectada: {header_row}")
                break

        # Leer DataFrame completo con encabezado detectado
        df = pd.read_excel(
            io.BytesIO(archivo_bytes), 
            sheet_name=hoja, 
            header=header_row
        )
        logger.info(f"DataFrame cargado: {len(df)} filas, {len(df.columns)} columnas")

        # 🔄 Procesar datos con parámetros de SLA configurados
        p = DataProcessor(df)
        df_procesado = p.procesar(sla_almacen, sla_principal, sla_otras)
        logger.info(f"Procesamiento completado: {len(df_procesado)} registros válidos")
        
        return df_procesado, hoja

    except Exception as e:
        logger.error(f"Error crítico al cargar archivo: {str(e)}", exc_info=True)
        st.error(f"❌ Error al procesar el archivo: {e}")
        return None, None


def cargar_y_procesar(
    uploaded_file, 
    sla_almacen: int = 1, 
    sla_principal: int = 3, 
    sla_otras: int = 5
) -> tuple:
    """
    Wrapper público para cargar y procesar archivo con parámetros SLA.
    
    Args:
        uploaded_file: Objeto file_uploader de Streamlit
        sla_almacen, sla_principal, sla_otras: Parámetros de configuración SLA
        
    Returns:
        Tupla (processor, df_procesado, hoja) o (None, None, None) si error
    """
    if uploaded_file is None:
        return None, None, None
        
    archivo_bytes = uploaded_file.getvalue()  # Convertir a bytes para cache
    df_procesado, hoja = _cargar_df_nuclear_v7(
        archivo_bytes, uploaded_file.name, sla_almacen, sla_principal, sla_otras
    )
    
    if df_procesado is None:
        return None, None, None
    
    # Crear instancia fresca de DataProcessor con datos ya procesados
    processor = DataProcessor(df_procesado)
    processor.df_procesado = df_procesado  # Asignar para acceso directo
    
    return processor, df_procesado, hoja
