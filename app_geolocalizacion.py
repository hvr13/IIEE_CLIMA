# pip install pandas folium plotly streamlit streamlit-folium requests

import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import requests
from datetime import datetime
import os

# Configuración inicial
RUTA_EXCEL = 'MONITOREO DE II.EE PRIORIZADAS.xlsx'
HOJA_TRABAJO = 'II.EE_COORDENADAS'
API_KEY = "ef684be92b56a57fae457479b54ebdd6"  # API Key de OpenWeatherMap

def obtener_clima(lat, lon):
    """Obtiene datos meteorológicos de OpenWeatherMap API"""
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': lat,
        'lon': lon,
        'appid': API_KEY,
        'units': 'metric',  # Para obtener temperaturas en Celsius
        'lang': 'es'       # Para obtener descripciones en español
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if response.status_code == 200:
            return {
                'temperatura': data['main']['temp'],
                'humedad': data['main']['humidity'],
                'descripcion': data['weather'][0]['description'].capitalize(),
                'icono': data['weather'][0]['icon'],
                'viento': data['wind']['speed'],
                'sensacion_termica': data['main']['feels_like'],
                'amanecer': datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M'),
                'atardecer': datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M'),
                'presion': data['main']['pressure'],
                'nubosidad': data['clouds']['all'] if 'clouds' in data else 'N/A',
                'visibilidad': data.get('visibility', 'N/A')
            }
        else:
            st.warning(f"No se pudo obtener datos del clima: {data.get('message', 'Error desconocido')}")
            return None
    except Exception as e:
        st.error(f"Error al conectarse a la API del clima: {str(e)}")
        return None

def crear_popup(row, clima=None):
    """Crea el contenido HTML para el popup del marcador"""
    popup_content = f"""
    <div style="width: 250px;">
        <h4 style="margin-bottom: 5px; color: #1E3F66;">{row['Nombre de SS.EE.']}</h4>
        <p style="margin: 2px 0;"><b>Nivel:</b> {row['Nivel / Modalidad']}</p>
        <p style="margin: 2px 0;"><b>Dirección:</b> {row['Dirección']}</p>
    """
    
    if clima:
        popup_content += f"""
        <hr style="margin: 8px 0; border-color: #eee;">
        <div style="display: flex; align-items: center;">
            <div>
                <img src="https://openweathermap.org/img/wn/{clima['icono']}.png" 
                     style="width: 40px; height: 40px;">
            </div>
            <div style="margin-left: 10px;">
                <p style="margin: 2px 0; font-size: 16px;"><b>{clima['temperatura']}°C</b> | {clima['descripcion']}</p>
                <p style="margin: 2px 0; font-size: 12px;">Sensación: {clima['sensacion_termica']}°C</p>
                <p style="margin: 2px 0; font-size: 12px;">Humedad: {clima['humedad']}% | Viento: {clima['viento']} m/s</p>
            </div>
        </div>
        """
    
    popup_content += "</div>"
    return popup_content

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Geolocalización de II.EE con Clima",
    page_icon="🌦️",
    layout='wide',
    initial_sidebar_state="expanded"
)

# Título y descripción
st.title("🌍 Geolocalización de Instituciones Educativas")
st.markdown("""
Visualización de instituciones educativas con información meteorológica en tiempo real.
Datos climáticos proporcionados por OpenWeatherMap.
""")

# Barra lateral para información
with st.sidebar:
    st.header("Información del Sistema")
    st.success("✅ API Key de OpenWeatherMap configurada correctamente")
    st.markdown("---")
    st.markdown("""
    **Datos meteorológicos incluidos:**
    - Temperatura actual
    - Sensación térmica
    - Humedad
    - Velocidad del viento
    - Condiciones climáticas
    - Horarios de amanecer/atardecer
    """)
    st.markdown("---")
    st.markdown(f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Carga de datos
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel(RUTA_EXCEL, sheet_name=HOJA_TRABAJO)
        df['Código Centro Poblado'] = df['Código Centro Poblado'].fillna(1)
        
        # Limpieza básica de datos
        df['Latitud'] = pd.to_numeric(df['Latitud'], errors='coerce')
        df['Longitud'] = pd.to_numeric(df['Longitud'], errors='coerce')
        df = df.dropna(subset=['Latitud', 'Longitud'])
        
        return df
    except Exception as e:
        st.error(f"Error al cargar los datos: {str(e)}")
        return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.error("No se pudieron cargar los datos. Verifica el archivo Excel y la hoja especificada.")
    st.stop()

# Pestañas principales
tab1, tab2, tab3, tab4 = st.tabs(['📊 Mapa Plotly', '🗺️ Mapa Interactivo', '📋 Datos', '🌦️ Clima Detallado'])

with tab1:
    st.header("Visualización con Plotly")
    
    # Configuración del mapa
    col1, col2 = st.columns([3, 1])
    
    with col1:
        parMapa = st.selectbox(
            "Estilo de Mapa:",
            options=["open-street-map", "carto-positron", "carto-darkmatter", "stamen-terrain"],
            index=0
        )
    
    with col2:
        color_por = st.selectbox(
            "Color por:",
            options=["Nivel / Modalidad", "Departamento", "Provincia"],
            index=0
        )
    
    # Crear el mapa
    fig = px.scatter_mapbox(
        df, 
        lat='Latitud', 
        lon='Longitud',
        color=color_por,
        hover_name='Nombre de SS.EE.',
        hover_data={
            'Latitud': True,
            'Longitud': True,
            'Dirección': True,
            'Departamento': True,
            'Provincia': True,
            'Distrito': True,
            'Nivel / Modalidad': True
        },
        zoom=9,
        height=700,
        title="Distribución de Instituciones Educativas"
    )
    
    fig.update_layout(
        mapbox_style=parMapa,
        margin={"r":0,"t":40,"l":0,"b":0},
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Mapa Interactivo con Datos Climáticos")
    
    # Configuración del mapa
    col1, col2 = st.columns([2, 1])
    
    with col1:
        parTipoMapa = st.radio(
            'Visualización:',
            options=['Agrupado (Cluster)', 'Marcadores Individuales'], 
            horizontal=True,
            index=0
        )
    
    with col2:
        mapa_base = st.selectbox(
            'Mapa base:',
            options=['OpenStreetMap', 'CartoDB Positron', 'Stamen Terrain'],
            index=0
        )
    
    # Crear mapa base
    mapa_center = [df['Latitud'].mean(), df['Longitud'].mean()]
    
    if mapa_base == 'OpenStreetMap':
        m = folium.Map(location=mapa_center, zoom_start=10)
    elif mapa_base == 'CartoDB Positron':
        m = folium.Map(location=mapa_center, zoom_start=10, tiles='CartoDB Positron')
    else:
        m = folium.Map(location=mapa_center, zoom_start=10, tiles='Stamen Terrain')
    
    # Configurar cluster si es necesario
    if 'Agrupado' in parTipoMapa:
        marker_cluster = MarkerCluster().add_to(m)

    # Progreso de carga
    progress_bar = st.progress(0)
    total_markers = len(df)
    
    # Añadir marcadores
    for index, row in df.iterrows():
        progress_bar.progress((index + 1) / total_markers)
        
        # Obtener datos del clima
        clima = obtener_clima(row['Latitud'], row['Longitud'])
        
        # Crear popup
        popup_content = crear_popup(row, clima)
        iframe = folium.IFrame(popup_content, width=300, height=200 if clima else 150)
        popup = folium.Popup(iframe, max_width=300)
        
        # Color del marcador según nivel educativo
        nivel = row['Nivel / Modalidad']
        if 'Inicial' in nivel:
            icon_color = 'blue'
            icono = 'child'
        elif 'Primaria' in nivel:
            icon_color = 'green'
            icono = 'pencil'
        elif 'Secundaria' in nivel:
            icon_color = 'orange'
            icono = 'graduation-cap'
        else:
            icon_color = 'red'
            icono = 'info-circle'
        
        # Crear marcador
        marker = folium.Marker(
            location=[row['Latitud'], row['Longitud']],
            popup=popup,
            icon=folium.Icon(color=icon_color, icon=icono, prefix='fa')
        )
        
        if 'Agrupado' in parTipoMapa:
            marker.add_to(marker_cluster)
        else:
            marker.add_to(m)

    # Añadir controles al mapa
    folium.plugins.Fullscreen(
        position="topright",
        title="Pantalla completa",
        title_cancel="Salir",
        force_separate_button=True
    ).add_to(m)
    
    folium.plugins.MousePosition(
        position="bottomleft",
        separator=" | ",
        empty_string="Coordenadas no disponibles",
        lng_first=True,
        num_digits=6
    ).add_to(m)
    
    folium.plugins.MeasureControl(
        position="bottomleft",
        primary_length_unit="meters",
        secondary_length_unit="kilometers"
    ).add_to(m)
    
    # Mostrar mapa
    st_data = st_folium(m, height=700, use_container_width=True)
    
    # Mostrar información del marcador seleccionado
    if st_data.get('last_object_clicked_popup'):
        st.subheader("Institución seleccionada")
        st.markdown(st_data['last_object_clicked_popup'], unsafe_allow_html=True)

with tab3:
    st.header("Datos de las Instituciones Educativas")
    
    # Filtros
    st.subheader("Filtros")
    cols = st.columns(4)
    
    with cols[0]:
        departamento = st.multiselect(
            'Departamento',
            options=df['Departamento'].unique(),
            default=df['Departamento'].unique()[0] if len(df['Departamento'].unique()) > 0 else None
        )
    
    with cols[1]:
        provincia = st.multiselect(
            'Provincia',
            options=df['Provincia'].unique(),
            default=df['Provincia'].unique()[0] if len(df['Provincia'].unique()) > 0 else None
        )
    
    with cols[2]:
        distrito = st.multiselect(
            'Distrito',
            options=df['Distrito'].unique(),
            default=df['Distrito'].unique()[0] if len(df['Distrito'].unique()) > 0 else None
        )
    
    with cols[3]:
        nivel = st.multiselect(
            'Nivel/Modalidad',
            options=df['Nivel / Modalidad'].unique(),
            default=df['Nivel / Modalidad'].unique()[0] if len(df['Nivel / Modalidad'].unique()) > 0 else None
        )
    
    # Aplicar filtros
    filtered_df = df.copy()
    
    if departamento:
        filtered_df = filtered_df[filtered_df['Departamento'].isin(departamento)]
    if provincia:
        filtered_df = filtered_df[filtered_df['Provincia'].isin(provincia)]
    if distrito:
        filtered_df = filtered_df[filtered_df['Distrito'].isin(distrito)]
    if nivel:
        filtered_df = filtered_df[filtered_df['Nivel / Modalidad'].isin(nivel)]
    
    # Mostrar datos
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config={
            "Latitud": st.column_config.NumberColumn(format="%.6f"),
            "Longitud": st.column_config.NumberColumn(format="%.6f"),
            "Código Modular": st.column_config.NumberColumn(format="%d")
        },
        hide_index=True
    )
    
    # Estadísticas
    st.subheader("Estadísticas")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Instituciones", len(filtered_df))
    
    with col2:
        st.metric("Niveles Educativos", filtered_df['Nivel / Modalidad'].nunique())
    
    with col3:
        st.metric("Distritos Cubiertos", filtered_df['Distrito'].nunique())
    
    with col4:
        st.metric("Provincias", filtered_df['Provincia'].nunique())

with tab4:
    st.header("Información Meteorológica Detallada")
    
    # Seleccionar ubicación
    selected_index = st.selectbox(
        "Selecciona una institución educativa:",
        options=df.index,
        format_func=lambda x: f"{df.loc[x, 'Nombre de SS.EE.']} - {df.loc[x, 'Distrito']}",
        index=0
    )
    
    selected_row = df.loc[selected_index]
    
    # Mostrar información básica
    st.subheader("Información de la Institución")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Nombre:** {selected_row['Nombre de SS.EE.']}  
        **Código Modular:** {selected_row['Código Modular']}  
        **Nivel/Modalidad:** {selected_row['Nivel / Modalidad']}  
        **Departamento:** {selected_row['Departamento']}
        """)
    
    with col2:
        st.markdown(f"""
        **Provincia:** {selected_row['Provincia']}  
        **Distrito:** {selected_row['Distrito']}  
        **Centro Poblado:** {selected_row['Centro Poblado']}  
        **Ubicación:** {selected_row['Latitud']:.6f}, {selected_row['Longitud']:.6f}
        """)
    
    # Obtener datos del clima
    st.subheader("Condiciones Meteorológicas Actuales")
    
    with st.spinner("Obteniendo datos meteorológicos..."):
        clima = obtener_clima(selected_row['Latitud'], selected_row['Longitud'])
    
    if clima:
        # Mostrar datos principales
        st.markdown("""
        <style>
        .big-font {
            font-size:18px !important;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<p class="big-font">🌡️ Temperatura</p>', unsafe_allow_html=True)
            st.markdown(f"**Actual:** {clima['temperatura']}°C")
            st.markdown(f"**Sensación térmica:** {clima['sensacion_termica']}°C")
        
        with col2:
            st.markdown('<p class="big-font">💧 Humedad</p>', unsafe_allow_html=True)
            st.markdown(f"**Humedad relativa:** {clima['humedad']}%")
            st.markdown(f"**Presión atmosférica:** {clima['presion']} hPa")
        
        with col3:
            st.markdown('<p class="big-font">🌬️ Viento</p>', unsafe_allow_html=True)
            st.markdown(f"**Velocidad:** {clima['viento']} m/s")
            st.markdown(f"**Visibilidad:** {clima['visibilidad'] if clima['visibilidad'] != 'N/A' else 'N/A'} m")
        
        # Icono y descripción
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.image(f"https://openweathermap.org/img/wn/{clima['icono']}@4x.png", width=150)
        
        with col2:
            st.markdown(f'<p style="font-size: 24px; margin-top: 20px;">{clima["descripcion"]}</p>', unsafe_allow_html=True)
            st.markdown(f"**Nubosidad:** {clima['nubosidad']}%")
        
        # Horarios
        st.markdown("---")
        st.subheader("Horarios")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**🌅 Amanecer:** {clima['amanecer']}")
        
        with col2:
            st.markdown(f"**🌇 Atardecer:** {clima['atardecer']}")
        
        # Mapa de ubicación
        st.markdown("---")
        st.subheader("Ubicación Exacta")
        
        m_mini = folium.Map(
            location=[selected_row['Latitud'], selected_row['Longitud']], 
            zoom_start=14,
            width='100%',
            height=400
        )
        
        folium.Marker(
            location=[selected_row['Latitud'], selected_row['Longitud']],
            popup=selected_row['Nombre de SS.EE.'],
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m_mini)
        
        folium.CircleMarker(
            location=[selected_row['Latitud'], selected_row['Longitud']],
            radius=50,
            color='#3186cc',
            fill=True,
            fill_color='#3186cc'
        ).add_to(m_mini)
        
        st_folium(m_mini, height=400, use_container_width=True)
    else:
        st.error("No se pudieron obtener los datos meteorológicos para esta ubicación.")

# Pie de página
st.markdown("---")
st.markdown("""
**Sistema de Geolocalización con Datos Climáticos**  
Desarrollado para el monitoreo de instituciones educativas  
Datos meteorológicos proporcionados por [OpenWeatherMap](https://openweathermap.org/)
""")