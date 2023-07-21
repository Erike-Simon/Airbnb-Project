# cálculo de distâncias entre coordenadas
# Problama de renderização com os plots

import streamlit as st
import numpy as np
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO
#from geopy.distance import geodesic
from geopy import distance
import geopandas as gpd
from shapely.geometry import Point
import requests
from bs4 import BeautifulSoup
import urllib

# 1 - Carregar os datasets
df_rec = pd.read_csv('df_rec.csv')
df_mercado = pd.read_csv('mercados.csv')
df_museu = pd.read_csv('museu.csv', sep=',')
df_teatro = pd.read_csv('teatros.csv')

#TIMES = df.clube.unique()

# Imagem de recife
response = requests.get('https://imagens.portalzuk.com.br/blog/568/6334ed026329d.jpg')
image_rec = Image.open(BytesIO(response.content))

# 2 - Definição de interface do dashboard
st.set_page_config(page_title="Dash Airbnb")

header = st.container()
msidebar = st.sidebar
box1 = st.container()
#box2 = st.container()

# Descrição dos elementos de interface

with header:
    # elemento de titulo
    st.title("Encontre as Melhores Hospedagens em Recife")
    st.image(image_rec, use_column_width=True) 

with msidebar:
    # editar a sidebar
    option_tour = st.multiselect('Tipo de turismo:', ['Mercado', 'Museu', 'Teatro', 'Praia']) 
    st.title(" ")
    guest_number = st.selectbox('Número de hóspedes:', 
                                list(df_rec.numberOfGuests.sort_values().unique())[:-1]) #-1 para excluir o 16
    st.title(" ")

    print('Opções de turismo: ', option_tour)
    print('N hóspedes: ', guest_number)

with box1:
    st.subheader('Localizações dos pontos turísticos e hospedagens')
    
    # Scattermap das localizações 
    #___________________________________________________________________________________
    # Filtra os dados com base nos números de hóspedes selecionados
    df_rec1 = df_rec[df_rec['numberOfGuests'] == guest_number]

    # em km
    min_dist = 3

    # Crie uma lista vazia para armazenar as coordenadas filtradas
    coordenadas_filtradas = []

    # Calcule a distância entre as coordenadas do trace1 e dos outros traces
    for coordenada_rec1 in zip(df_rec1['location/lat'], df_rec1['location/lng']):
        # Inicialize uma variável para verificar se a distância é menor que a distância mínima
        low_dist = False
    
        if 'Museu' in option_tour:
            for coordenada_museu in zip(df_museu['latitude'], df_museu['longitude']):
                # Calcule a distância entre as coordenadas do de df_rec1 e df_museu
                dist = distance.distance(coordenada_rec1, coordenada_museu).kilometers

                # Verifique se a distância é menor que a distância mínima
                if dist < min_dist:
                    low_dist = True
                    break # Não é necessário continuar verificando outras coordenadas

        if 'Mercado' in option_tour:
            for coordenada_mercado in zip(df_mercado['latitude'], df_mercado['longitude']):
                dist = distance.distance(coordenada_rec1, coordenada_mercado).kilometers
                if dist < min_dist:
                    low_dist = True
                    break

        if 'Teatro' in option_tour:
            for coordenada_teatro in zip(df_teatro['latitude'], df_teatro['longitude']):
                dist = distance.distance(coordenada_rec1, coordenada_teatro).kilometers
                if dist < min_dist:
                    low_dist = True
                    break
    
        # Se a distância for menor que a distância mínima em relação a todos os traces,
        # adicione as coordenadas filtradas à lista
        if low_dist:
            coordenadas_filtradas.append(coordenada_rec1)

    # Cria um novo GeoDataFrame com as coordenadas filtradas
    geometry = [Point(coord[1], coord[0]) for coord in coordenadas_filtradas]
    df_rec2 = gpd.GeoDataFrame(geometry=geometry) # rec2
    df_rec2.crs = 'EPSG:4326'

    # Define the maximum and minimum sizes for the markers
    max_size = 12
    min_size = 5

    prices = df_rec1['price per night'] 

    # Scale the prices to fit within the desired size range
    scaled_sizes = [
        (price - min(prices)) / (max(prices) - min(prices)) * (max_size - min_size) + min_size
        for price in prices
    ]

    # Create the first scattermapbox trace
    trace1 = go.Scattermapbox(
        lat = df_rec2['geometry'].y,
        lon = df_rec2['geometry'].x,
        mode='markers',
        marker=dict(
            size=scaled_sizes,
            sizemode='diameter',
            sizeref=0.6,  # Controls the scaling of marker sizes 
            color='blue',
            opacity=0.6
        ),
        hovertext=[
            f"{nome}<br>Preço por noite: {preco} R$<br>Hóspedes: {hosp}"
            for nome, preco, hosp in zip(df_rec1['name'], df_rec1['price per night'], 
                                         df_rec1['numberOfGuests'])
        ],
        name='Hospedagens'
    )

    traces = [trace1] # para armazenamento dos plots

    # Verificações condicionais para adicionar os traces selecionados no multiselect
    if 'Museu' in option_tour:
        trace2 = go.Scattermapbox(
            lat=df_museu['latitude'],
            lon=df_museu['longitude'],
            mode='markers',
            marker=dict(
                size=10,
                color='red',
                opacity=0.7
            ),
            hovertext=[
                f"{nome}<br>Site: <a href='{site}'>{site}</a>"
                for nome, site in zip(df_museu['nome'], df_museu['site'])
            ],
            name='Museus'
        )
        traces.append(trace2)
        

    if 'Mercado' in option_tour:
        trace3 = go.Scattermapbox(
            lat=df_mercado['latitude'],
            lon=df_mercado['longitude'],
            mode='markers',
            marker=dict(
                size=10,
                color='green',
                opacity=0.7
            ),
            hovertext=df_mercado['nome'],
            name='Mercados'
        )
        traces.append(trace3)

    if 'Teatro' in option_tour:
        trace4 = go.Scattermapbox(
            lat=df_teatro['latitude'],
            lon=df_teatro['longitude'],
            mode='markers',
            marker=dict(
                size=10,
                color='purple',
                opacity=0.8
            ),
            hovertext=[
                f"{nome}<br>Fone: {fone}"
                for nome, fone in zip(df_teatro['nome'], df_teatro['Telefone'])
            ],
            name='Teatros'
        )
        traces.append(trace4)

    # Create the layout for the map
    layout = go.Layout(
        margin=dict(l=0, r=0, t=0, b=0),
        mapbox=dict(
            style = 'open-street-map',
            center=dict(lat=df_rec1['location/lat'].mean(), lon=df_rec1['location/lng'].mean()),
            zoom=11
        ),
        showlegend=True
    )

    fig = go.Figure(data=traces, layout=layout)

    st.plotly_chart(fig, use_container_width=True, height=700)

    #___________________________________________________________________________________

#with box2:
#    st.header('Tipo de gol')
#    dfs = dff.loc[(dff['rodata']>= rodada[0]) & (dff['rodata'] <= rodada[1])]
#    fig2 = px.bar(dfs, x="tipo_de_gol") #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#    st.plotly_chart(fig2, use_container_width=True)