import streamlit as st
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def sidebar_filtros(df_procesado: pd.DataFrame) -> tuple:
    """
    Renderiza sidebar con filtros globales y retorna DataFrame filtrado.
    
    Args:
        df_procesado: DataFrame original procesado
        
    Returns:
        Tupla (df_filtrado, debug_mode) con datos aplicando filtros y flag de debug
    """
    st.sidebar.markdown("## 📦 TECU Despachos")
    st.sidebar.markdown("---")

    df_f = df_procesado.copy() if df_procesado is not None else None
    total_rows = len(df_procesado) if df_procesado is not None else 0

    if df_procesado is None or total_rows == 0:
        return df_f, False

    st.sidebar.markdown("### 🔍 Filtros Globales")

    # ── 📅 FILTRO POR MES (con mapeo seguro para orden cronológico) ──
    if 'Mes_Sort' in df_f.columns and 'Mes_Label' in df_f.columns:
        df_meses = df_f[['Mes_Sort', 'Mes_Label']].dropna().drop_duplicates().sort_values('Mes_Sort')
        mapa_mes = dict(zip(df_meses['Mes_Sort'].astype(str), df_meses['Mes_Label'].astype(str)))
        opciones_mes = list(mapa_mes.values())
    else:
        opciones_mes = []

    sel_mes = st.sidebar.multiselect(
        "📅 Mes",
        options=['Todos'] + opciones_mes,
        default=['Todos'],
        key='ms_filtro_mes',
        help="Selecciona uno o varios meses para filtrar los datos"
    )

    # ── 🚚 FILTRO POR TRANSPORTADORA ──
    if 'Transportadora' in df_f.columns:
        opciones_transp = sorted(df_f['Transportadora'].dropna().unique().astype(str).tolist())
    else:
        opciones_transp = []
    sel_transp = st.sidebar.multiselect(
        "🚚 Transportadora",
        options=['Todas'] + opciones_transp,
        default=['Todas'],
        key='ms_filtro_transp',
        help="Filtra por empresa de transporte"
    )

    # ── 📍 FILTRO POR CIUDAD ──
    if 'Ciudad' in df_f.columns:
        opciones_ciudad = sorted(df_f['Ciudad'].dropna().unique().astype(str).tolist())
    else:
        opciones_ciudad = []
    sel_ciudad = st.sidebar.multiselect(
        "📍 Ciudad",
        options=['Todas'] + opciones_ciudad,
        default=['Todas'],
        key='ms_filtro_ciudad',
        help="Filtra por ciudad de destino"
    )

    # ── 📦 NUEVO: FILTRO POR CATEGORÍA DE PRODUCTO ──
    if 'Categoria' in df_f.columns:
        opciones_cat = sorted(df_f['Categoria'].dropna().unique().astype(str).tolist())
        sel_cat = st.sidebar.multiselect(
            "📦 Categoría",
            options=['Todas'] + opciones_cat,
            default=['Todas'],
            key='ms_filtro_categoria',
            help="Filtra por tipo de producto (Superficie, Standing Desk, etc.)"
        )
    else:
        sel_cat = ['Todas']  # Fallback si columna no existe

    # ── 🏷️ NUEVO: FILTRO POR CONCEPTO (Venta vs Novedad) ──
    if 'Concepto' in df_f.columns:
        opciones_concepto = sorted(df_f['Concepto'].dropna().unique().astype(str).tolist())
        sel_concepto = st.sidebar.multiselect(
            "🏷️ Concepto",
            options=['Todos'] + opciones_concepto,
            default=['Todos'],
            key='ms_filtro_concepto',
            help="Filtra por tipo de transacción: Venta normal o Novedad"
        )
    else:
        sel_concepto = ['Todos']

    # ── 💰 NUEVO: FILTRO POR RANGO DE VALOR DESPACHO ──
    rango_valor = (0, float('inf'))
    if 'Valor despacho' in df_f.columns:
        # Limpiar y convertir valores monetarios a numéricos
        df_f['Valor_num'] = pd.to_numeric(
            df_f['Valor despacho'].astype(str).str.replace(r'[^\d.]', '', regex=True), 
            errors='coerce'
        ).fillna(0)
        
        if len(df_f) > 0:
            min_val, max_val = df_f['Valor_num'].min(), df_f['Valor_num'].max()
            if max_val > 0:
                rango_valor = st.sidebar.slider(
                    "💰 Rango Valor Despacho (COP)",
                    min_value=float(min_val), 
                    max_value=float(max_val),
                    value=(float(min_val), float(max_val)),
                    key='slider_valor',
                    help="Filtra por monto del despacho en pesos colombianos"
                )

    # ── 🔄 APLICAR TODOS LOS FILTROS AL DATAFRAME ──
    if 'Todos' not in sel_mes and len(sel_mes) > 0 and 'Mes_Label' in df_f.columns:
        df_f = df_f[df_f['Mes_Label'].astype(str).isin(sel_mes)]

    if 'Todas' not in sel_transp and len(sel_transp) > 0 and 'Transportadora' in df_f.columns:
        df_f = df_f[df_f['Transportadora'].astype(str).isin(sel_transp)]

    if 'Todas' not in sel_ciudad and len(sel_ciudad) > 0 and 'Ciudad' in df_f.columns:
        df_f = df_f[df_f['Ciudad'].astype(str).isin(sel_ciudad)]

    if 'Todas' not in sel_cat and len(sel_cat) > 0 and 'Categoria' in df_f.columns:
        df_f = df_f[df_f['Categoria'].astype(str).isin(sel_cat)]

    if 'Todos' not in sel_concepto and len(sel_concepto) > 0 and 'Concepto' in df_f.columns:
        df_f = df_f[df_f['Concepto'].astype(str).isin(sel_concepto)]

    if 'Valor_num' in df_f.columns and rango_valor[1] < float('inf'):
        df_f = df_f[
            (df_f['Valor_num'] >= rango_valor[0]) & 
            (df_f['Valor_num'] <= rango_valor[1])
        ]

    # ── 🛠️ HERRAMIENTAS DE DESARROLLO Y UTILIDAD ──
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛠️ Herramientas")
    
    # Checkbox para modo debug: muestra eventos de selección en consola
    debug_mode = st.sidebar.checkbox(
        "Modo Debug (Ver Eventos)", 
        value=False,
        help="Activa logs detallados de interacciones con gráficos"
    )
    
    # Contador de registros filtrados vs totales
    curr_rows = len(df_f)
    st.sidebar.caption(f"📊 Registros: {curr_rows:,} / {total_rows:,}")
    
    # Botón para limpiar cache y recargar app (útil en desarrollo)
    if st.sidebar.button("🔄 Reiniciar App (Borrar Caché)"):
        st.cache_data.clear()
        logger.info("Cache limpiado por usuario - App reiniciada")
        st.rerun()

    return df_f, debug_mode
