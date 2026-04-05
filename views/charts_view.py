import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict
from views.constants import COLOR_CUMPLE, COLOR_NO_CUMPLE, COLOR_PTE, COLOR_PRIMARY, PLOTLY_TEMPLATE
from views.components_view import mostrar_datos_fuente

# --- DICCIONARIO DE COORDENADAS (APROXIMADAS) PARA CIUDADES DE COLOMBIA ---
COORDENADAS_CIUDADES = {
    'bogota': {'lat': 4.7110, 'lon': -74.0721}, 'bogotá': {'lat': 4.7110, 'lon': -74.0721},
    'medellin': {'lat': 6.2442, 'lon': -75.5812}, 'medellín': {'lat': 6.2442, 'lon': -75.5812},
    'cali': {'lat': 3.4516, 'lon': -76.5320},
    'barranquilla': {'lat': 10.9685, 'lon': -74.7813},
    'cartagena': {'lat': 10.3910, 'lon': -75.4794},
    'bucaramanga': {'lat': 7.1193, 'lon': -73.1227},
    'pereira': {'lat': 4.8133, 'lon': -75.6961},
    'manizales': {'lat': 5.0689, 'lon': -75.5174},
    'cucuta': {'lat': 7.8939, 'lon': -72.5078}, 'cúcuta': {'lat': 7.8939, 'lon': -72.5078},
    'ibague': {'lat': 4.4389, 'lon': -75.2322}, 'ibagué': {'lat': 4.4389, 'lon': -75.2322},
    'villavicencio': {'lat': 4.1420, 'lon': -73.6266},
    'santa marta': {'lat': 11.2408, 'lon': -74.1990},
    'valledupar': {'lat': 10.4631, 'lon': -73.2532},
    'monteria': {'lat': 8.7480, 'lon': -75.8814}, 'montería': {'lat': 8.7480, 'lon': -75.8814},
    'pasto': {'lat': 1.2136, 'lon': -77.2811},
    'armenia': {'lat': 4.5339, 'lon': -75.6811},
    'popayan': {'lat': 2.4382, 'lon': -76.6132}, 'popayán': {'lat': 2.4382, 'lon': -76.6132},
    'sincelejo': {'lat': 9.3047, 'lon': -75.3978},
    'floridablanca': {'lat': 7.0622, 'lon': -73.0864},
    'palmira': {'lat': 3.5394, 'lon': -76.3036},
    'neiva': {'lat': 2.9273, 'lon': -75.2819},
    'soledad': {'lat': 10.9184, 'lon': -74.7646},
    'soacha': {'lat': 4.5781, 'lon': -74.2144},
    'bello': {'lat': 6.3373, 'lon': -75.5580},
    'tulua': {'lat': 4.0846, 'lon': -76.1953}, 'tuluá': {'lat': 4.0846, 'lon': -76.1953},
    'envigado': {'lat': 6.1759, 'lon': -75.5917},
    'yumbo': {'lat': 3.5828, 'lon': -76.4939},
}

def get_coord(ciudad, coord_type):
    import unicodedata
    if pd.isna(ciudad): return None
    # Eliminar acentos y caracteres especiales usando librería estándar en vez de unidecode
    c_str = str(ciudad).lower()
    c_lower = ''.join(c for c in unicodedata.normalize('NFD', c_str) if unicodedata.category(c) != 'Mn')
    
    # Buscar coincidencia exacta primero
    if c_lower in COORDENADAS_CIUDADES:
        return COORDENADAS_CIUDADES[c_lower][coord_type]
    # Buscar parcial
    for main_c, coords in COORDENADAS_CIUDADES.items():
        if main_c in c_lower:
            return coords[coord_type]
    return None

def fig_base() -> Dict:
    """Retorna configuración base para gráficos Plotly en modo oscuro."""
    return {
        'template': PLOTLY_TEMPLATE,           # Tema oscuro de Plotly
        'paper_bgcolor': 'rgba(0,0,0,0)',      # Fondo transparente
        'plot_bgcolor': 'rgba(0,0,0,0)',       # Área de gráfico transparente
        'font': {'color': '#e8ecf4', 'family': 'Inter, sans-serif'},  # Tipografía
        'margin': {'l': 20, 'r': 20, 't': 40, 'b': 40},  # Márgenes compactos
    }

def mostrar_graficos(processor, df_filtrado: pd.DataFrame, debug_mode: bool = False) -> None:
    """Renderiza todos los gráficos interactivos del dashboard en layout responsivo."""
    st.session_state.df_filtrado_actual = df_filtrado
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Cumplimiento NNS")
        counts = df_filtrado['Cumple_NNS'].value_counts().reset_index()
        counts.columns = ['Categoria', 'Cantidad']
        
        fig = px.pie(
            counts, names='Categoria', values='Cantidad',
            hole=0.55,
            color='Categoria',
            color_discrete_map={
                'Cumple': COLOR_CUMPLE, 
                'No cumple': COLOR_NO_CUMPLE, 
                'PTE': COLOR_PTE
            },
            template=PLOTLY_TEMPLATE,
            custom_data=['Categoria']
        )
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), showlegend=True)
        sel_nns = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="chart_nns_v5")
        
        if sel_nns and 'selection' in sel_nns:
            mostrar_datos_fuente(df_filtrado, sel_nns['selection'], 
                                [('Cumple_NNS', 'Categoria')], 
                                titulo_seccion="🎯 Detalle de Pedidos por Cumplimiento")
        else:
            st.caption("💡 Haz clic en una rodaja para ver el detalle")

    with col2:
        st.markdown("### 📊 Desvíos en Despacho vs Entrega")
        ind = processor.get_indicadores(df_filtrado)
        total_e = ind['total_pedidos'] if ind else 0
        
        v_desp = ind.get('con_desvio_despacho', 0)
        v_ent = ind.get('con_desvio_entrega', 0)
        # Aproximación de perfectos (Nota: matemáticamente un pedido puede tener ambos desvíos)
        v_sin = max(0, total_e - max(v_desp, v_ent))
        
        categorias = ['Sin Desvío', 'Desvío Despacho', 'Desvío Entrega']
        valores = [v_sin, v_desp, v_ent]
        colores = [COLOR_CUMPLE, COLOR_PTE, COLOR_NO_CUMPLE]
        
        fig2 = go.Figure(go.Bar(
            x=categorias, y=valores,
            marker_color=colores,
            text=valores, textposition='outside',
        ))
        fig2.update_layout(**fig_base(), yaxis_title='Pedidos', showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Texto explicativo dinámico para presentaciones
        st.info(
            f"🗣️ **Líneas para exponer:** De los **{total_e:,}** pedidos totales en pantalla:\n"
            f"- **{v_sin:,}** cajas fueron perfectas.\n"
            f"- **{v_desp:,}** cajas se estancaron dentro de Bodega.\n"
            f"- **{v_ent:,}** cajas se las demoró la Transportadora."
        )


    # ── NUEVA SECCIÓN BI: MATRIZ DE CUADRANTES DE TIEMPO Y MAPA GEOGRÁFICO ──
    st.markdown("---")
    st.markdown("## 🗺️ Análisis Geográfico y Tiempos de Operación (NUEVO BI)")
    col_map, col_scatter = st.columns(2)

    with col_map:
        st.markdown("### 🌎 Mapa de Calor de Demoras por Ciudad")
        # El mapa muestra las ciudades en rojo (muy demoradas) o verde (perfectas).
        if 'Ciudad' in df_filtrado.columns and len(df_filtrado) > 0:
            df_map = df_filtrado.copy()
            # Mapear latitudes y longitudes
            df_map['lat'] = df_map['Ciudad'].apply(lambda c: get_coord(c, 'lat'))
            df_map['lon'] = df_map['Ciudad'].apply(lambda c: get_coord(c, 'lon'))
            
            # Agrupar las que sí encontraron coordenadas
            df_map_valid = df_map.dropna(subset=['lat', 'lon'])
            if len(df_map_valid) > 0:
                map_agg = df_map_valid.groupby(['Ciudad', 'lat', 'lon']).agg(
                    Pedidos=('Cumple_NNS', 'count'),
                    Incumplidos=('Cumple_NNS', lambda x: (x == 'No cumple').sum()),
                    Desvio_Prom=('Desvio_Entrega', 'mean')
                ).reset_index()
                
                map_agg['Pct_Incumplimiento'] = (map_agg['Incumplidos'] / map_agg['Pedidos'] * 100).round(1)

                fig_geo = px.scatter_mapbox(
                    map_agg, lat='lat', lon='lon',
                    size='Pedidos', color='Pct_Incumplimiento',
                    hover_name='Ciudad',
                    hover_data={'lat':False, 'lon':False, 'Incumplidos':True, 'Desvio_Prom':True},
                    color_continuous_scale=['#22c55e', '#f59e0b', '#ef4444'], # Verde a Rojo
                    center=dict(lat=4.5709, lon=-74.2973), zoom=4.5, # Centro en Colombia
                    mapbox_style="carto-darkmatter", # Mapa realista oscuro sin token
                    template=PLOTLY_TEMPLATE,
                    title="Zonas Rojas de Incumplimiento"
                )
                geo_layout = fig_base()
                geo_layout['margin'] = {"r":0,"t":40,"l":0,"b":0}
                fig_geo.update_layout(**geo_layout)
                st.plotly_chart(fig_geo, use_container_width=True)
                st.caption("💡 Zonas rojas o burbujas grandes alertan alta accidentalidad operativa.")
            else:
                st.info("ℹ️ No hay ciudades válidas en el set de datos para mapear.")

    with col_scatter:
        st.markdown("### ⚔️ Matriz Operacional (Bodega vs Transporte)")
        # Un scatter plot cruzando Desvío de Almacén vs Desvío de Transporte, agrupado por pedido
        if 'Desvio_Despacho' in df_filtrado.columns and 'Desvio_Entrega' in df_filtrado.columns:
            # Quitamos los que no tienen desvío para ver a los ofensores más claramente
            df_scat = df_filtrado[(df_filtrado['Desvio_Despacho'] > 0) | (df_filtrado['Desvio_Entrega'] > 0)].copy()
            
            if len(df_scat) > 0:
                fig_scatter = px.scatter(
                    df_scat,
                    x='Desvio_Despacho', y='Desvio_Entrega',
                    color='Transportadora' if 'Transportadora' in df_scat.columns else None,
                    hover_data=['No_Orden', 'Ciudad', 'Cliente'] if 'Cliente' in df_scat.columns else [],
                    template=PLOTLY_TEMPLATE,
                    title="Aislamiento del Origen de la Culpa",
                    labels={'Desvio_Despacho': 'Días de Retraso BODEGA (X)', 'Desvio_Entrega': 'Días de Retraso RUTA (Y)'}
                )
                fig_scatter.add_hline(y=0, line_dash='dash', line_color='#ef4444', annotation_text='Retraso de Transporte')
                fig_scatter.add_vline(x=0, line_dash='dash', line_color='#f59e0b', annotation_text='Retraso de Bodega')
                fig_scatter.update_layout(**fig_base())
                st.plotly_chart(fig_scatter, use_container_width=True)
                st.caption("💡 Todo a la DERECHA = Culpa de Almacén. Todo ARRIBA = Culpa de Transporte.")
            else:
                st.success("🎉 Ningún pedido con desvío, la matriz operacional está limpia.")


    # ── NUEVA SECCIÓN BI: MAPA DE CALOR SEMANAL Y TENDENCIA SEMANAL ──
    st.markdown("---")
    st.markdown("## 📅 Comportamiento Temporal Avanzado (NUEVO BI)")
    col_heat, col_week = st.columns(2)

    with col_heat:
        st.markdown("### 🔥 Calor Operacional (Días vs Impacto)")
        # Heatmap de retrasos agrupando por Día de la Semana
        if 'Dia_Semana' in df_filtrado.columns and 'Desvio_Entrega' in df_filtrado.columns:
            df_heat = df_filtrado[df_filtrado['Cumple_NNS'] == 'No cumple'].copy()
            if len(df_heat) > 0:
                heatmap_data = df_heat.groupby(['Dia_Semana_Num', 'Dia_Semana']).agg(
                    Total_Incumplidos=('Cumple_NNS', 'count'),
                    Valor_en_Riesgo=('Valor_num', 'sum') if 'Valor_num' in df_heat.columns else ('Cumple_NNS', 'count')
                ).reset_index()
                
                # Orden lógico de los días
                heatmap_data = heatmap_data.sort_values('Dia_Semana_Num')
                
                fig_heat = px.density_heatmap(
                    heatmap_data, 
                    x='Dia_Semana', y='Total_Incumplidos', z='Valor_en_Riesgo',
                    histfunc='avg', template=PLOTLY_TEMPLATE,
                    color_continuous_scale='Reds',
                    labels={'Total_Incumplidos': 'Volumen de Retrasos', 'Dia_Semana': 'Día Modificado/Vendido', 'Valor_en_Riesgo': 'Dinero / Peso'},
                    title="Densidad de Riesgo Financiero por Día Operativo"
                )
                fig_heat.update_layout(**fig_base())
                st.plotly_chart(fig_heat, use_container_width=True)
                st.caption("💡 El color rojo oscuro indica qué día de la semana concentra la mayor pérdida operativa.")
            else:
                st.success("🎉 No hay incumplimientos para el mapa de calor.")

    with col_week:
        st.markdown("### 📈 Tendencia Semanal (Reacción Rápida)")
        # En vez de ver solo un punto al mes, ver semana a semana en el año
        if 'Semana' in df_filtrado.columns:
            analisis_s = df_filtrado.groupby(['Semana']).agg(
                Total=('Cumple_NNS', 'count'),
                Cumplen=('Cumple_NNS', lambda x: (x == 'Cumple').sum())
            ).reset_index()
            analisis_s['Pct_Cumplimiento'] = (analisis_s['Cumplen'] / analisis_s['Total'] * 100).round(1)
            
            fig_week = px.area(
                analisis_s, x='Semana', y='Pct_Cumplimiento',
                title="Monitoreo de Pulso Semanal",
                template=PLOTLY_TEMPLATE,
                labels={'Semana': 'N° Semana del Año', 'Pct_Cumplimiento': '% Exitoso'},
                color_discrete_sequence=['#3b82f6']  # Azul eléctrico
            )
            fig_week.add_hline(y=95, line_dash='dash', line_color=COLOR_PTE, annotation_text='Meta 95%')
            fig_week.update_layout(**fig_base(), yaxis_range=[0, 115])
            st.plotly_chart(fig_week, use_container_width=True)
            st.caption("💡 Las métricas semanales te permiten advertir la caída antes de cerrar mes.")



    # El resto de las métricas clásicas
    st.markdown("---")
    st.markdown("## 🏭 Detalles Generales Operativos")

    st.markdown("### 📍 Cumplimiento por Ciudad (Top 12)")
    analisis_c = processor.get_analisis_ciudad(df_filtrado)
    if analisis_c is not None and len(analisis_c) > 0:
        top_c = analisis_c.head(12).copy()
        fig3 = px.bar(
            top_c, x='Ciudad', y='Pct_Cumplimiento',
            color='Pct_Cumplimiento',
            color_continuous_scale=['#ef4444', '#f59e0b', '#22c55e'],
            text='Pct_Cumplimiento',
            custom_data=['Ciudad', 'Total'],
            template=PLOTLY_TEMPLATE,
            hover_data=['Total', 'No_Cumplen']
        )
        fig3.update_traces(texttemplate='%{text}%', textposition='outside')
        fig3.add_hline(y=95, line_dash='dash', line_color=COLOR_PTE)
        fig3.update_layout(**fig_base(), yaxis_title='% Cumplimiento', yaxis_range=[0, 115])
        st.plotly_chart(fig3, use_container_width=True)

    col5, col6 = st.columns(2)
    with col5:
        st.markdown("### 🚚 Desempeño por Transportadora")
        analisis_t = processor.get_analisis_transportadora(df_filtrado)
        if analisis_t is not None and len(analisis_t) > 0:
            top_t = analisis_t.head(8).copy()
            fig4 = px.bar(
                top_t, x='Transportadora', y='Pct_Cumplimiento',
                color='Desvio_Prom', color_continuous_scale=['#22c55e', '#f59e0b', '#ef4444'],
                text='Pct_Cumplimiento', template=PLOTLY_TEMPLATE,
            )
            fig4.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig4.update_layout(**fig_base(), yaxis_title='% Cumplimiento', yaxis_range=[0, 115])
            fig4.add_hline(y=95, line_dash='dash', line_color=COLOR_PTE)
            st.plotly_chart(fig4, use_container_width=True)

    with col6:
        st.markdown("### 🏢 Responsabilidad del Incumplimiento")
        inc = processor.get_pedidos_incumplimiento(df_filtrado)
        if inc is not None and len(inc) > 0 and 'Area_Incumple' in inc.columns:
            areas = inc['Area_Incumple'].value_counts().reset_index()
            areas.columns = ['Area', 'Cantidad']
            fig5 = px.pie(areas, names='Area', values='Cantidad', hole=0.45, template=PLOTLY_TEMPLATE)
            fig5.update_layout(**fig_base())
            st.plotly_chart(fig5, use_container_width=True)

    st.markdown("### 🎯 Análisis de Causas Raíz (Principio de Pareto)")
    if 'Causal de Incumplimiento' in df_filtrado.columns:
        df_inc = df_filtrado[df_filtrado['Cumple_NNS'] == 'No cumple'].copy()
        if len(df_inc) > 0:
            causas = df_inc['Causal de Incumplimiento'].value_counts().reset_index()
            causas.columns = ['Causal', 'Frecuencia']
            causas['Porcentaje'] = (causas['Frecuencia'] / causas['Frecuencia'].sum() * 100).round(1)
            causas['Porcentaje Acum'] = causas['Porcentaje'].cumsum()
            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(x=causas['Causal'], y=causas['Frecuencia'], name='Frecuencia', marker_color=COLOR_NO_CUMPLE, text=causas['Frecuencia'], textposition='outside'))
            fig_pareto.add_trace(go.Scatter(x=causas['Causal'], y=causas['Porcentaje Acum'], name='% Acumulado', line=dict(color=COLOR_PRIMARY, width=3), mode='lines+markers+text', text=[f"{v}%" for v in causas['Porcentaje Acum']], yaxis='y2'))
            fig_pareto.update_layout(**fig_base(), yaxis=dict(title='Frecuencia', side='left'), yaxis2=dict(title='% Acumulado', overlaying='y', side='right', range=[0, 110]))
            st.plotly_chart(fig_pareto, use_container_width=True)
