import streamlit as st
import pandas as pd
from typing import Dict

def _fila_kpis(indicadores: Dict, label_prefix: str = "") -> None:
    """
    Renderiza una fila horizontal con 5 métricas KPI usando st.columns.
    """
    cols = st.columns(5)  # Crear 5 columnas de igual ancho
    
    # Definir datos de cada KPI: (etiqueta, valor, delta, help_text)
    datos = [
        ("📦 Total Pedidos", indicadores.get('total_pedidos', 0),
         None, "Pedidos con status Entregado"),
        ("✅ % Cumplimiento NNS", f"{indicadores.get('pct_cumplimiento', 0)}%",
         f"{indicadores.get('cumplen_nns', 0)} cumplen", "Porcentaje dentro del SLA"),
        ("⚠️ Desvío Despacho", indicadores.get('con_desvio_despacho', 0),
         f"Prom: {indicadores.get('promedio_desvio_despacho', 0)}d", "Pedidos con retraso en despacho"),
        ("🔴 Desvío Entrega", indicadores.get('con_desvio_entrega', 0),
         f"Prom: {indicadores.get('promedio_desvio_entrega', 0)}d", "Pedidos fuera de SLA"),
        ("⏳ Pendientes (PTE)", indicadores.get('pendientes', 0),
         None, "Sin fecha de entrega registrada"),
    ]
    
    # Renderizar cada KPI en su columna correspondiente
    for col, (label, val, delta, help_txt) in zip(cols, datos):
        with col:
            st.metric(f"{label_prefix}{label}", val, delta, help=help_txt)


def _fila_kpis_financieros(df_filtrado: pd.DataFrame) -> None:
    """
    Renderiza fila adicional con KPIs financieros (NUEVA FUNCIÓN).
    """
    if 'Valor despacho' not in df_filtrado.columns:
        return  # Saltar si columna financiera no existe
    
    # Limpiar y convertir valores monetarios a numéricos para cálculos
    valores = pd.to_numeric(
        df_filtrado['Valor despacho'].astype(str).str.replace(r'[^\d.]', '', regex=True), 
        errors='coerce'
    ).fillna(0)
    
    total_valor = valores.sum()
    ticket_promedio = valores.mean() if len(valores) > 0 else 0
    
    # Calcular desvío de costos si columna existe
    desvio_costo = 0
    if 'Diferencia valor real vs Estimado' in df_filtrado.columns:
        desvios = pd.to_numeric(
            df_filtrado['Diferencia valor real vs Estimado'].astype(str).str.replace(r'[^\d.-]', '', regex=True), 
            errors='coerce'
        ).fillna(0)
        desvio_costo = desvios.abs().sum()
    
    cols = st.columns(4)  # 4 columnas para KPIs financieros
    
    datos = [
        ("💰 Total Despachos", f"${total_valor:,.0f}", None, "Valor total de despachos filtrados"),
        ("📈 Ticket Promedio", f"${ticket_promedio:,.0f}", None, "Valor promedio por pedido"),
        ("⚠️ Desvío Costo", f"${desvio_costo:,.0f}", None, "Diferencia acumulada real vs estimado"),
        ("🎯 Pedidos Altos", f"{len(valores[valores > ticket_promedio*1.5]):,}", 
         None, f"Pedidos > 150% del promedio (${ticket_promedio*1.5:,.0f})"),
    ]
    
    for col, (label, val, delta, help_txt) in zip(cols, datos):
        with col:
            st.metric(label, val, delta, help=help_txt)


def mostrar_kpis(ind_global: Dict, ind_filtrado: Dict, etiqueta_filtro: str = "Selección") -> None:
    """
    Muestra KPIs en dos bloques comparativos: Global (sin filtros) vs Filtrado.
    """
    if not ind_global or not ind_filtrado:
        return

    # ── BLOQUE GLOBAL: Métricas del dataset completo (referencia base) ──
    st.markdown(
        "<p style='margin:0 0 6px 0; color:#8b9dc3; font-size:0.78rem; "
        "text-transform:uppercase; letter-spacing:0.06em;'>🌐 Total General (sin filtros)</p>",
        unsafe_allow_html=True
    )
    _fila_kpis(ind_global)

    st.markdown("<hr class='kpi-separator'>", unsafe_allow_html=True)

    # ── BLOQUE FILTRADO: Métricas aplicando filtros del usuario ──
    # Calcular diferencia de cumplimiento para mostrar variación vs global
    delta_pct = round(ind_filtrado.get('pct_cumplimiento', 0) - ind_global.get('pct_cumplimiento', 0), 1)
    delta_str = f"({'+' if delta_pct >= 0 else ''}{delta_pct}% vs global)"
    color_delta = "#22c55e" if delta_pct >= 0 else "#ef4444"  # Verde si mejora, rojo si empeora

    st.markdown(
        f"<p style='margin:0 0 6px 0; color:#8b9dc3; font-size:0.78rem; "
        f"text-transform:uppercase; letter-spacing:0.06em;'>"
        f"🔍 {etiqueta_filtro} "
        f"<span style='color:{color_delta}; font-weight:700'>{delta_str}</span></p>",
        unsafe_allow_html=True
    )
    _fila_kpis(ind_filtrado)
    
    # ── NUEVO: Fila de KPIs Financieros (solo si hay datos monetarios) ──
    if 'Valor despacho' in st.session_state.get('df_filtrado_actual', pd.DataFrame()).columns:
        st.markdown("<hr class='kpi-separator'>", unsafe_allow_html=True)
        _fila_kpis_financieros(st.session_state.df_filtrado_actual)
