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
    
    # --- DEPARTAMENTOS / REGIONES (para cuando el dato indica el departamento) ---
    'antioquia': {'lat': 6.2442, 'lon': -75.5812},  # Medellín ref
    'cesar': {'lat': 10.4631, 'lon': -73.2532},     # Valledupar ref
    'meta': {'lat': 4.1420, 'lon': -73.6266},       # Villavicencio ref
    'quindio': {'lat': 4.5339, 'lon': -75.6811},    # Armenia ref
    'cundinamarca': {'lat': 4.7110, 'lon': -74.0721},
    'valle del cauca': {'lat': 3.4516, 'lon': -76.5320},
    'valle': {'lat': 3.4516, 'lon': -76.5320},
    'atlantico': {'lat': 10.9685, 'lon': -74.7813},
    'bolivar': {'lat': 10.3910, 'lon': -75.4794},
    'santander': {'lat': 7.1193, 'lon': -73.1227},
    'risaralda': {'lat': 4.8133, 'lon': -75.6961},
    'caldas': {'lat': 5.0689, 'lon': -75.5174},
    'norte de santander': {'lat': 7.8939, 'lon': -72.5078},
    'tolima': {'lat': 4.4389, 'lon': -75.2322},
    'magdalena': {'lat': 11.2408, 'lon': -74.1990},
    'cordoba': {'lat': 8.7480, 'lon': -75.8814},
    'narino': {'lat': 1.2136, 'lon': -77.2811},
    'cauca': {'lat': 2.4382, 'lon': -76.6132},
    'sucre': {'lat': 9.3047, 'lon': -75.3978},
    'huila': {'lat': 2.9273, 'lon': -75.2819},
    'boyaca': {'lat': 5.5353, 'lon': -73.3678},      # Tunja ref
    'la guajira': {'lat': 11.5444, 'lon': -72.9072}, # Riohacha ref
    'guajira': {'lat': 11.5444, 'lon': -72.9072},
    'choco': {'lat': 5.6919, 'lon': -76.6583},       # Quibdó ref
    'casanare': {'lat': 5.3377, 'lon': -72.3959},    # Yopal ref
    'putumayo': {'lat': 1.1444, 'lon': -76.6481},    # Mocoa ref
}

def _normalizar_ciudad(ciudad: str) -> str:
    """Normaliza el nombre de ciudad: minúsculas y sin acentos."""
    import unicodedata
    c = str(ciudad).lower().strip()
    return ''.join(ch for ch in unicodedata.normalize('NFD', c) if unicodedata.category(ch) != 'Mn')


def get_coord(ciudad, coord_type):
    """Busca coordenadas en el dict estático (rápido, sin internet)."""
    if pd.isna(ciudad):
        return None
    c_lower = _normalizar_ciudad(ciudad)
    if c_lower in COORDENADAS_CIUDADES:
        return COORDENADAS_CIUDADES[c_lower][coord_type]
    for main_c, coords in COORDENADAS_CIUDADES.items():
        if main_c in c_lower:
            return coords[coord_type]
    return None


def geocodificar_ciudades(ciudades_unicas: list) -> dict:
    """
    Geocodifica un listado de ciudades usando:
    1. Diccionario estático (instantáneo)
    2. Nominatim / OpenStreetMap para las desconocidas  (requiere internet)
    Resultados cacheados en st.session_state['geo_cache'] para evitar
    llamadas repetidas entre reruns de Streamlit.
    """
    import time
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

    # Inicializar caché en sesión si no existe
    if 'geo_cache' not in st.session_state:
        st.session_state['geo_cache'] = {}

    cache = st.session_state['geo_cache']
    resultado = {}  # ciudad_normalizada -> {'lat': ..., 'lon': ...}

    pendientes = []  # ciudades que necesitan geocodificación externa

    for ciudad in ciudades_unicas:
        if pd.isna(ciudad):
            continue
        c_norm = _normalizar_ciudad(ciudad)
        c_orig = str(ciudad).strip()

        # 1) Buscar en dict estático
        lat = get_coord(ciudad, 'lat')
        lon = get_coord(ciudad, 'lon')
        if lat is not None and lon is not None:
            resultado[c_orig] = {'lat': lat, 'lon': lon}
            continue

        # 2) Buscar en caché de sesión
        if c_norm in cache:
            resultado[c_orig] = cache[c_norm]
            continue

        pendientes.append((c_orig, c_norm))

    # 3) Geocodificar con Nominatim los que faltan
    if pendientes:
        try:
            geolocator = Nominatim(
                user_agent="tecu_dashboard_v2",
                timeout=5
            )
            for c_orig, c_norm in pendientes:
                try:
                    query = f"{c_orig}, Colombia"
                    location = geolocator.geocode(query)
                    if location:
                        coords = {'lat': location.latitude, 'lon': location.longitude}
                        resultado[c_orig] = coords
                        cache[c_norm] = coords  # guardar en caché
                    else:
                        cache[c_norm] = None  # marcar como no encontrado
                    time.sleep(1)  # respetar el rate-limit de Nominatim (1 req/s)
                except (GeocoderTimedOut, GeocoderUnavailable):
                    cache[c_norm] = None
        except Exception:
            pass  # sin internet o sin geopy instalado: mostramos lo que ya tenemos

    return resultado

def fig_base() -> Dict:
    """Retorna configuración base para gráficos Plotly en modo oscuro."""
    return {
        'template': PLOTLY_TEMPLATE,           # Tema oscuro de Plotly
        'paper_bgcolor': 'rgba(0,0,0,0)',      # Fondo transparente
        'plot_bgcolor': 'rgba(0,0,0,0)',       # Área de gráfico transparente
        'font': {'color': '#e8ecf4', 'family': 'Funnel Display, sans-serif'},  # Tipografía
        'margin': {'l': 20, 'r': 20, 't': 40, 'b': 40},  # Márgenes compactos
    }

def mostrar_graficos(processor, df_filtrado: pd.DataFrame, debug_mode: bool = False) -> None:
    """Renderiza todos los gráficos interactivos del dashboard en layout responsivo."""
    st.session_state.df_filtrado_actual = df_filtrado
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Cumplimiento NNS")

        # ── Separar INSTALACION usando Categoria, igual que el KPI ────────
        if 'Categoria' in df_filtrado.columns:
            mask_inst = df_filtrado['Categoria'].astype(str).str.strip().str.lower() == 'instalación'
        else:
            mask_inst = pd.Series([False] * len(df_filtrado), index=df_filtrado.index)
        df_nns  = df_filtrado[~mask_inst]   # sin instalaciones → para la gráfica
        df_inst = df_filtrado[mask_inst]    # solo instalaciones → tabla aparte

        counts = df_nns['Cumple_NNS'].value_counts().reset_index()
        counts.columns = ['Categoria', 'Cantidad']
        # Garantizar que PTE siempre aparezca (aunque sea 0)
        for cat in ['Cumple', 'No cumple', 'PTE']:
            if cat not in counts['Categoria'].values:
                counts = pd.concat(
                    [counts, pd.DataFrame({'Categoria': [cat], 'Cantidad': [0]})],
                    ignore_index=True
                )
        cat_order = ['Cumple', 'No cumple', 'PTE']
        counts['_ord'] = counts['Categoria'].map(lambda c: cat_order.index(c) if c in cat_order else 99)
        counts = counts.sort_values('_ord').drop(columns='_ord').reset_index(drop=True)

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
            mostrar_datos_fuente(df_nns, sel_nns['selection'],
                                [('Cumple_NNS', 'Categoria')],
                                titulo_seccion="🎯 Detalle de Pedidos por Cumplimiento")
        else:
            st.caption("💡 Haz clic en una rodaja para ver el detalle")

        # ── Tabla 1: resumen NNS (sin Instalación) ─────────────────────────
        st.markdown("#### 📋 Detalle Resumen — Cumplimiento NNS")
        st.dataframe(counts, use_container_width=True, hide_index=True)

        # ── Tabla 2: Instalación (NO cuenta como pendiente) ────────────────
        st.markdown("#### 🔧 Instalación *(no suma a pendientes)*")
        if len(df_inst) > 0:
            pte_inst = int((df_inst['Cumple_NNS'] == 'PTE').sum()) if 'Cumple_NNS' in df_inst.columns else 0
            df_resumen_inst = pd.DataFrame({
                'Categoría': ['Instalación (total)'],
                'Cantidad':  [len(df_inst)]
            })
            st.dataframe(df_resumen_inst, use_container_width=True, hide_index=True)
            st.caption("📦 Estos registros se contabilizan por separado y NO se suman a PTE.")
        else:
            st.info("ℹ️ No hay registros de Instalación en el filtro actual.")
         

    with col2:
        st.markdown("### 🏢 Responsables vs Causales")
        if 'Area_Incumple' in df_filtrado.columns and 'Causal_Incumplimiento' in df_filtrado.columns:
            fig5 = px.histogram(
                df_filtrado, x='Area_Incumple', color='Causal_Incumplimiento',
                barmode='stack', text_auto=True, template=PLOTLY_TEMPLATE,
                labels={'Area_Incumple': 'Responsable', 'Causal_Incumplimiento': 'Causal'}
            )
            fig5.update_layout(**fig_base(), xaxis_title='Responsable', yaxis_title='Cantidad', showlegend=True, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig5, use_container_width=True)
            
            st.markdown("#### 📋 Detalle Resumen")
            resumen = df_filtrado.groupby(['Area_Incumple', 'Causal_Incumplimiento']).size().reset_index(name='Cantidad')
            resumen = resumen.sort_values(by=['Area_Incumple', 'Cantidad'], ascending=[True, False])
            st.dataframe(resumen, use_container_width=True, hide_index=True)

    

    # ── NUEVA SECCIÓN BI: MATRIZ DE CUADRANTES DE TIEMPO Y MAPA GEOGRÁFICO ──
    st.markdown("---")
    st.markdown("## 🗺️ Análisis Geográfico y Tiempos de Operación ")
    col_map = st.container()

    with col_map:
        st.markdown("### 🌎 Mapa de Calor de Demoras por Ciudad")
        if 'Ciudad' in df_filtrado.columns and len(df_filtrado) > 0:
            df_map = df_filtrado.copy()

            # Obtener ciudades únicas presentes en los datos filtrados
            ciudades_unicas = df_map['Ciudad'].dropna().unique().tolist()

            # Geocodificar: dict estático + Nominatim para las desconocidas
            n_sin_cache = sum(
                1 for c in ciudades_unicas
                if _normalizar_ciudad(c) not in st.session_state.get('geo_cache', {})
                and get_coord(c, 'lat') is None
            )
            if n_sin_cache > 0:
                with st.spinner(f"🌐 Geocodificando {n_sin_cache} ciudad(es) nueva(s)... (puede tardar ~{n_sin_cache}s)"):
                    coords_map = geocodificar_ciudades(ciudades_unicas)
            else:
                coords_map = geocodificar_ciudades(ciudades_unicas)

            # Aplicar coordenadas al DataFrame
            df_map['lat'] = df_map['Ciudad'].apply(
                lambda c: coords_map.get(str(c).strip(), {}).get('lat') if pd.notna(c) else None
            )
            df_map['lon'] = df_map['Ciudad'].apply(
                lambda c: coords_map.get(str(c).strip(), {}).get('lon') if pd.notna(c) else None
            )

            df_map_valid = df_map.dropna(subset=['lat', 'lon'])

            # Ciudades sin coordenadas (para informar al usuario)
            sin_coord = set(ciudades_unicas) - set(df_map_valid['Ciudad'].unique())

            if len(df_map_valid) > 0:
                map_agg = df_map_valid.groupby(['Ciudad', 'lat', 'lon']).agg(
                    Pedidos=('Cumple_NNS', 'count'),
                    Incumplidos=('Cumple_NNS', lambda x: (x == 'No cumple').sum()),
                    Desvio_Prom=('Desvio_Entrega', 'mean')
                ).reset_index()

                map_agg['Pct_Incumplimiento'] = (
                    map_agg['Incumplidos'] / map_agg['Pedidos'] * 100
                ).round(1)
                map_agg['Desvio_Prom'] = map_agg['Desvio_Prom'].round(1)

                fig_geo = px.scatter_mapbox(
                    map_agg, lat='lat', lon='lon',
                    size='Pedidos', color='Pct_Incumplimiento',
                    hover_name='Ciudad',
                    hover_data={
                        'lat': False, 'lon': False,
                        'Pedidos': True,
                        'Incumplidos': True,
                        'Desvio_Prom': True,
                        'Pct_Incumplimiento': True
                    },
                    color_continuous_scale=['#00bfff', '#FF3B00', '#FF0C00'],
                    center=dict(lat=4.5709, lon=-74.2973), zoom=4.5,
                    mapbox_style="carto-darkmatter",
                    template=PLOTLY_TEMPLATE,
                    title=f"Mapa de Cumplimiento — {len(map_agg)} ciudad(es)"
                )
                geo_layout = fig_base()
                geo_layout['margin'] = {"r": 0, "t": 40, "l": 0, "b": 0}
                fig_geo.update_layout(**geo_layout)
                st.plotly_chart(fig_geo, use_container_width=True)
                st.caption(
                    f"🟢 Verde = sin incumplimiento · 🟡 Amarillo = parcial · 🔴 Rojo = crítico. "
                    f"El tamaño del círculo indica el volumen de pedidos."
                )
                st.markdown("#### 📋 Detalle Resumen")
                df_resumen_geo = map_agg[['Ciudad', 'Pedidos', 'Incumplidos', 'Pct_Incumplimiento', 'Desvio_Prom']].sort_values('Pedidos', ascending=False)
                st.dataframe(df_resumen_geo.head(15), use_container_width=True, hide_index=True)
                if sin_coord:
                    st.warning(
                        f"⚠️ {len(sin_coord)} ciudad(es) sin coordenadas (no se pudieron geocodificar): "
                        f"{', '.join(sorted(sin_coord))}"
                    )
            else:
                st.info("ℹ️ No se encontraron coordenadas para ninguna ciudad del set filtrado.")


 


    # El resto de las métricas clásicas
    st.markdown("---")
    st.markdown("## 🏭 Detalles Generales Operativos")

    st.markdown("### 📍 Cumplimiento por Ciudad ")
    analisis_c = processor.get_analisis_ciudad(df_filtrado)
    if analisis_c is not None and len(analisis_c) > 0:
        top_c = analisis_c.head(12).copy()
        fig3 = px.bar(
            top_c, x='Ciudad', y='Pct_Cumplimiento',
            color='Pct_Cumplimiento',
            color_continuous_scale=['#FF0C00', '#FF3B00', '#00bfff'],
            text='Pct_Cumplimiento',
            custom_data=['Ciudad', 'Total'],
            template=PLOTLY_TEMPLATE,
            hover_data=['Total', 'No_Cumplen']
        )
        fig3.update_traces(texttemplate='%{text}%', textposition='outside')
        fig3.add_hline(y=95, line_dash='dash', line_color=COLOR_PTE)
        fig3.update_layout(**fig_base(), yaxis_title='% Cumplimiento', yaxis_range=[0, 115])
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("#### 📋 Detalle Resumen")
        st.dataframe(top_c[['Ciudad', 'Total', 'Cumplen', 'No_Cumplen', 'Pct_Cumplimiento']], use_container_width=True, hide_index=True)

    # col5 = st.container()
    # with col5:
    #     st.markdown("### 🚚 Desempeño por Transportadora")
    #     analisis_t = processor.get_analisis_transportadora(df_filtrado)
    #     if analisis_t is not None and len(analisis_t) > 0:
    #         top_t = analisis_t.head(8).copy()
    #         fig4 = px.bar(
    #             top_t, x='Transportadora', y='Pct_Cumplimiento',
    #             color='Desvio_Prom', color_continuous_scale=['#00bfff', '#FF3B00', '#FF0C00'],
    #             text='Pct_Cumplimiento', template=PLOTLY_TEMPLATE,
    #         )
    #         fig4.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    #         fig4.update_layout(**fig_base(), yaxis_title='% Cumplimiento', yaxis_range=[0, 115])
    #         fig4.add_hline(y=95, line_dash='dash', line_color=COLOR_PTE)
    #         st.plotly_chart(fig4, use_container_width=True)
    #         st.markdown("#### 📋 Detalle Resumen")
    #         st.dataframe(top_t[['Transportadora', 'Total', 'Cumplen', 'Pct_Cumplimiento', 'Desvio_Prom']], use_container_width=True, hide_index=True)

 

    st.markdown("### 🎯 Análisis de Causas Raíz (Principio de Pareto)")
    if 'Causal_Incumplimiento' in df_filtrado.columns:
        df_inc = df_filtrado[df_filtrado['Cumple_NNS'] == 'No cumple'].copy()
        if len(df_inc) > 0:
            causas = df_inc['Causal_Incumplimiento'].value_counts().reset_index()
            causas.columns = ['Causal', 'Frecuencia']
            causas['Porcentaje'] = (causas['Frecuencia'] / causas['Frecuencia'].sum() * 100).round(1)
            causas['Porcentaje Acum'] = causas['Porcentaje'].cumsum()
            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(x=causas['Causal'], y=causas['Frecuencia'], name='Frecuencia', marker_color=COLOR_NO_CUMPLE, text=causas['Frecuencia'], textposition='outside'))
            fig_pareto.add_trace(go.Scatter(x=causas['Causal'], y=causas['Porcentaje Acum'], name='% Acumulado', line=dict(color=COLOR_PRIMARY, width=3), mode='lines+markers+text', text=[f"{v}%" for v in causas['Porcentaje Acum']], yaxis='y2'))
            fig_pareto.update_layout(**fig_base(), yaxis=dict(title='Frecuencia', side='left'), yaxis2=dict(title='% Acumulado', overlaying='y', side='right', range=[0, 110]))
            st.plotly_chart(fig_pareto, use_container_width=True)
            st.markdown("#### 📋 Detalle Resumen")
            st.dataframe(causas[['Causal', 'Frecuencia', 'Porcentaje', 'Porcentaje Acum']], use_container_width=True, hide_index=True)

    # ── NUEVA SECCIÓN BI: MAPA DE CALOR SEMANAL Y TENDENCIA SEMANAL ──
    st.markdown("---")
    st.markdown("## 📅 Comportamiento Temporal Avanzado ")
    col_week = st.container()

    with col_week:
        st.markdown("### 📈 Tendencia Semanal")
        if 'Semana' in df_filtrado.columns:
            # Agrupar asegurando el orden si existe Semana_Sort
            cols_grupo = ['Semana_Sort', 'Semana'] if 'Semana_Sort' in df_filtrado.columns else ['Semana']
            analisis_s = df_filtrado.groupby(cols_grupo).agg(
                Total_Ingresados=('No_Orden', 'count'),
                Cumplen=('Cumple_NNS', lambda x: (x == 'Cumple').sum())
            ).reset_index()
            if 'Semana_Sort' in df_filtrado.columns:
                analisis_s = analisis_s.sort_values('Semana_Sort')
            else:
                analisis_s = analisis_s.sort_values('Semana')
                
            analisis_s['Pct_Cumplimiento'] = (analisis_s['Cumplen'] / analisis_s['Total_Ingresados'] * 100).round(1).fillna(0)
            
            fig_week = go.Figure()
            # Volumen de pedidos (Barras)
            fig_week.add_trace(
                go.Bar(
                    x=analisis_s['Semana'], y=analisis_s['Total_Ingresados'],
                    name='Pedidos Ingresados', marker_color='rgba(130, 130, 130, 0.4)',
                    text=analisis_s['Total_Ingresados'], textposition='auto', yaxis='y'
                )
            )
            # % Cumplimiento (Línea)
            fig_week.add_trace(
                go.Scatter(
                    x=analisis_s['Semana'], y=analisis_s['Pct_Cumplimiento'],
                    name='% Cumplimiento', mode='lines+markers+text',
                    text=analisis_s['Pct_Cumplimiento'].apply(lambda x: f"{x}%"),
                    textposition='top center', line=dict(color='#00bfff', width=3),
                    fill='tozeroy', fillcolor='rgba(0, 191, 255, 0.1)', yaxis='y2'
                )
            )
            
            fig_week.update_layout(
                **fig_base(), title="Ingreso de Pedidos vs % Cumplimiento Semanal",
                hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(title='Total Ingresados', side='left', showgrid=False),
                yaxis2=dict(title='% Cumplimiento', side='right', overlaying='y', range=[0, 115], showgrid=True)
            )
            fig_week.add_hline(y=95, line_dash='dash', line_color=COLOR_PTE, annotation_text='Meta 95%', yref='y2')
            
            st.plotly_chart(fig_week, use_container_width=True)
            st.caption("💡 Las barras indican la cantidad de pedidos que ingresaron en la semana. La línea indica qué porcentaje de ellos cumplieron la meta NNS.")
            st.markdown("#### 📋 Detalle Resumen")
            st.dataframe(analisis_s[['Semana', 'Total_Ingresados', 'Cumplen', 'Pct_Cumplimiento']], use_container_width=True, hide_index=True)



 
