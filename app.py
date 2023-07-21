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


# Imagem de recife
response = requests.get('https://imagens.portalzuk.com.br/blog/568/6334ed026329d.jpg')
image_rec = Image.open(BytesIO(response.content))

# 2 - Definição de interface do dashboard
st.set_page_config(page_title="Dash Airbnb")

header = st.container()
msidebar = st.sidebar
box1 = st.container()

# Descrição dos elementos de interface

with header:
    # elemento de titulo
    st.title("Encontre as Melhores Hospedagens em Recife")
    st.image(image_rec, use_column_width=True) 

with msidebar:
    # seleção do interesse turístico
    option_tour = st.multiselect('Tipo de turismo:', ['Mercado', 'Museu', 'Teatro']) 
    st.title(" ")
    # seleção do número de hóspedes
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

    # Define os máximos e mínimos tamanhos para os marcadores
    max_size = 12
    min_size = 5

    prices = df_rec1['price per night'] 

    # Escala os preços para ajustar a um tamanho proporcional
    scaled_sizes = [
        (price - min(prices)) / (max(prices) - min(prices)) * (max_size - min_size) + min_size
        for price in prices
    ]

    # Criação dos gráficos (traces)
    trace1 = go.Scattermapbox(
        lat = df_rec1['location/lat'],
        lon = df_rec1['location/lng'],
        mode='markers',
        marker=dict(
            size=scaled_sizes,
            sizemode='diameter',
            sizeref=0.6,  # Controla a escala dos tamanhos dos marcadores
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

    layout = go.Layout(
        margin=dict(l=0, r=0, t=0, b=0),
        mapbox=dict(
            style = 'open-street-map',
            center=dict(lat=df_rec1['location/lat'].mean(), lon=df_rec1['location/lng'].mean()),
            zoom=10.7
        ),
        showlegend=True
    )

    fig = go.Figure(data=traces, layout=layout)

    st.plotly_chart(fig, use_container_width=True)

    #___________________________________________________________________________________

    # Cria um DataFrame contendo as informações das hospedagens que serão exibidas na tabela
    df_hospedagens = df_rec1[['name','price per night','stars','score']]

    # Reseta os índices começando de 1
    df_hospedagens.reset_index(drop=True, inplace=True)
    df_hospedagens.index = df_hospedagens.index + 1

    # Renomeia a coluna de índices 
    df_hospedagens = df_hospedagens.rename_axis('Ranking')

    # Exibe a tabela com as informações das hospedagens
    st.dataframe(df_hospedagens,
                 width=None, # largura da coluna se ajusta automaticamente
                 column_config={
                    "name": "Hospedagem",
                    "price per night":st.column_config.NumberColumn(
                        "Preço por Noite", 
                        format="%f R$"
                    ),
                    "stars":st.column_config.NumberColumn(
                        "Avaliação", 
                        format="%f ⭐"
                    ),
                    "score":"Pontuação"
                 })