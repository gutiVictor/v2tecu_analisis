"""
Dashboard de Análisis de Despachos TECU Aura
Versión refactorizada a MVC - Controlador
"""

import streamlit as st
import logging
from datetime import datetime
import os

from models.data_loader import cargar_y_procesar
from views.sidebar_view import sidebar_filtros
from views.kpis_view import mostrar_kpis
from views.charts_view import mostrar_graficos
from views.components_view import (
    generar_alertas, 
    mostrar_alertas, 
    mostrar_recomendaciones, 
    mostrar_tabla_detalle, 
    generate_report_advanced
)

# ──────────────────────────────────────────────────────────────────────────
# ⚙️ CONFIGURACIÓN DE LOGGING
# ──────────────────────────────────────────────────────────────────────────
try:
    os.makedirs("logs", exist_ok=True)
except Exception as e:
    print(f"⚠️ No se pudo crear carpeta logs: {e}")

try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                f"logs/tecu_dashboard_{datetime.now().strftime('%Y%m%d')}.log",
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )
except Exception as e:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    print(f"⚠️ Logging en archivo falló, usando solo consola: {e}")

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────
# 🎨 CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TECU – Análisis de Despachos",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cargar estilos CSS externos
try:
    with open("estilos/styles.css", "r", encoding="utf-8") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    logger.warning("Archivo CSS no encontrado. Cargando sin estilos personalizados.")

# ──────────────────────────────────────────────────────────────────────────
# 🚀 FUNCIÓN PRINCIPAL ORQUESTADORA
# ──────────────────────────────────────────────────────────────────────────
def main():
    st.sidebar.markdown("### 📂 Cargar Archivo")
    uploaded = st.sidebar.file_uploader(
        "Archivo Excel (.xlsx / .xls)",
        type=['xlsx', 'xls'],
        help="Sube el archivo de Seguimiento de Despachos TECU con las columnas esperadas"
    )

    if uploaded is None:
        st.markdown("# 📦 TECU – Análisis de Despachos")
        st.markdown("---")

        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            st.info("**📅 SLA por ciudad**\n\n"
                    "- **3 días hábiles** → Bogotá, Medellín, Cali\n"
                    "- **5 días hábiles** → Otras ciudades")
        with col_i2:
            st.info("**📊 Métricas calculadas**\n\n"
                    "- % Cumplimiento NNS\n"
                    "- Desvíos despacho & entrega\n"
                    "- Área responsable\n"
                    "- **NUEVO**: KPIs financieros y análisis por categoría")
        with col_i3:
            st.info("**🔍 Filtros disponibles**\n\n"
                    "- Por Mes, Transportadora, Ciudad\n"
                    "- **NUEVO**: Categoría, Concepto, Rango de Valor\n"
                    "- Drill-down interactivo en gráficos")

        st.markdown("\n#### 👆 Sube el archivo Excel en el panel izquierdo para comenzar.")
        st.markdown("> 💡 **Tip**: Los datos se procesan localmente en tu navegador. Ninguna información sale de tu computadora.")
        return

    st.sidebar.markdown("### ⚙️ Configuración SLA")
    sl_alm = st.sidebar.slider("Límite Almacén (días)", 1, 5, 1)
    sl_pri = st.sidebar.slider("SLA Ciudades Principales (días)", 1, 3, 3)
    sl_otr = st.sidebar.slider("SLA Otras Ciudades (días)", 3, 5, 5)
    st.sidebar.markdown("---")

    with st.spinner("⏳ Procesando datos..."):
        processor, df_procesado, hoja = cargar_y_procesar(uploaded, sl_alm, sl_pri, sl_otr)

    if processor is None or df_procesado is None:
        st.error("❌ No se pudo procesar el archivo. Verifica que tenga el formato esperado.")
        return

    df_filtrado, debug_mode = sidebar_filtros(df_procesado)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Reportes")
    try:
        ind_global = processor.get_indicadores(df_procesado)
        ind_filtrado = processor.get_indicadores(df_filtrado)
        
        if ind_filtrado:
            btn_label = "📥 Descargar Reporte Filtrado" if len(df_filtrado) < len(df_procesado) else "📥 Descargar Mega Reporte"
            mega_buf = generate_report_advanced(df_filtrado, ind_filtrado, ind_global, processor)
            st.sidebar.download_button(
                btn_label,
                data=mega_buf,
                file_name=f"Reporte_TECU_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        st.sidebar.error(f"⚠️ Error generando reporte: {e}")

    st.markdown("# 📊 Dashboard de Despachos TECU Aura `MVC` 🚀")
    
    if len(df_filtrado) < len(df_procesado):
        st.info(f"💡 Filtro Activo: Viendo {len(df_filtrado)} de {len(df_procesado)} registros.")
    
    st.caption(
        f"**Archivo:** `{uploaded.name}` &nbsp;|&nbsp; "
        f"**Hoja:** `{hoja}` &nbsp;|&nbsp; "
        f"**Registros seleccionados:** {len(df_filtrado):,} / {len(df_procesado):,}"
    )
    st.markdown("---")

    ind_global = processor.get_indicadores(df_procesado)
    indicadores = processor.get_indicadores(df_filtrado)

    if indicadores is None or indicadores.get('total_pedidos', 0) == 0:
        st.warning("⚠️ No hay pedidos con status 'Entregado' en el rango seleccionado.")
        st.dataframe(df_filtrado.head(20), use_container_width=True)
        return

    es_global = len(df_filtrado) == len(df_procesado)
    etiqueta = "Total General con filtros" if es_global else "Selección Actual"
    
    mostrar_kpis(ind_global, indicadores, etiqueta)
    st.markdown("---")

    mostrar_graficos(processor, df_filtrado, debug_mode)
    st.markdown("---")

    st.markdown("### 🚨 Alertas Automáticas")
    alertas = generar_alertas(df_filtrado, indicadores)
    mostrar_alertas(alertas)
    st.markdown("---")

    mostrar_recomendaciones(processor, df_filtrado)
    st.markdown("---")

    mostrar_tabla_detalle(processor, df_filtrado)

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    logger.info("🚀 Aplicación TECU Dashboard iniciada")
    main()