# import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import glob
from prophet import Prophet
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="Net0thon App",
    page_icon=":four_leaf_clover:",
    layout="wide",
    initial_sidebar_state="collapsed",  #expanded
    menu_items={'Get help':'mailto:obai.shaikh@gmail.com',
                'Report a Bug':'mailto:obai.shaikh@gmail.com',
                'About':"The Green Guardian's team effort in Net0thon to combat climate change."}
)

def co2_map(color_by):
    # Read files
    fnames = glob.glob('./data/by_sector/*.csv')

    df_list = []
    for f in fnames:
        df_list.append(pd.read_csv(f, index_col=False))

    df = pd.concat(df_list)
    # df.drop(inplace=True, columns=['Primary Fuel', 'Unit Type'], errors='ignore')

    # st.markdown("<h1 style='text-align: center; color: white;'>CO2 Emissions</h1>", unsafe_allow_html=True)

    order = {'Sector': ['Electricity', 'Desalination', 'Petrochemicals', 'Refinery', 'Cement', 'Steel']}
    colors = ['red', 'blue', 'yellow', 'green', 'cyan', 'purple', 'orange']

    fig = px.scatter_mapbox(df, lat="Latitude", lon="Longitude", hover_name="City",
                            hover_data=["Sector", "CO2 emission (Mton/yr)"],
                            size="CO2 emission (Mton/yr)",
                            size_max=30,
                            category_orders=order,
                            color=color_by,
                            color_discrete_sequence=colors,
                            zoom=5,
                            # width=450,
                            height=900)
    fig.update_layout(
        # title_text="2020 Saudi Arabia's CO2 Emissions",
        mapbox_style="carto-positron")  # carto-positron
    fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})

    return fig


def annual_prophecy(d, ys, growth='linear', forecast_period=5):
    '''
    prophecy - FORECAST FUTURE STOCK PRICE

    Inputs:
    d                  Price history DataFrame (yfinance)
    forecast_period    Number of minutes of future forecast to predict

    '''
    d.index.names = ['ds']  # rename index to ds
    d = d.tz_localize(None)  # make timezone naive, for prophet
    ds = d.reset_index()  # make index (ds) a column

    for y in ys:
        ds_temp = ds.loc[:, ['ds', y]].rename(columns={y: 'y'})

        # Make the prophet model and fit on the data
        gm_prophet = Prophet(
            growth=growth,
            changepoints=None,
            n_changepoints=len(ds),
            changepoint_range=.92,
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            holidays=None,
            seasonality_mode='additive',
            seasonality_prior_scale=0,  # yhat zigzag
            holidays_prior_scale=0,
            changepoint_prior_scale=.45, #  .25,  # yhat slope, largefr == steeper
            mcmc_samples=0,
            interval_width=.8,
            uncertainty_samples=1000,
            stan_backend=None
        )

        gm_prophet.fit(ds_temp)
        # predict:
        # Make a future dataframe
        gm_forecast = gm_prophet.make_future_dataframe(periods=forecast_period, freq='Y')
        # Make predictions
        gm_forecast = gm_prophet.predict(gm_forecast)
        # gm_forecast
        gm_forecast = gm_forecast.set_index(gm_forecast.ds).loc[:, ['yhat', 'yhat_lower', 'yhat_upper',
                                                                    'trend', 'trend_lower', 'trend_upper']]
        # merge
        d = gm_forecast.merge(d, how='outer', on='ds')

    return d


def prophet(d):
    color = 'lime'  # if current_price >= open else 'rgb(255, 49, 49)'
    x = d.index.to_list()
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # plot actual (CO2)
    fig.add_trace(go.Scatter(mode='lines', x=x, y=d.co2_mt,
                             line=dict(color=color, width=2),
                             hovertemplate='<i>CO2</i>: %{y:.2f} million ton' +
                                           '<br><i>Year</i>: %{x|%Y}<br><extra></extra>',
                             name='CO2',
                             showlegend=True),
                  secondary_y=False)

    # plot yhat (CO2)
    fig.add_trace(go.Scatter(mode='lines', x=x, y=d.yhat_y,
                             line=dict(color=color, width=2, dash='dash'),
                             hovertemplate='<i>CO2</i>: %{y:.2f} million ton' +
                                           '<br><i>Year</i>: %{x|%Y}<br><extra></extra>',
                             name='CO2 Forecast',
                             showlegend=True),
                  secondary_y=False)

    # plot pop
    fig.add_trace(go.Scatter(mode='lines', x=x, y=d.yhat_x / 1e6,
                             line=dict(color='magenta', width=1),
                             hovertemplate='<i>Population</i>: %{y:.2f}' +
                                           '<br><i>Year</i>: %{x|%Y}<br><extra></extra>',
                             name='Population',
                             showlegend=True),
                  secondary_y=True)

    #     # plot volume bars
    #     fig.add_trace(go.Bar(x=x, y=d["pop"]/1e6, opacity=.65,
    #                          marker={
    #                              "color": "magenta",  # "#0FCFFF"
    #                          },
    #                          hovertemplate='<i>population</i>: %{y:,}<extra></extra>'
    #                          ), secondary_y=True)

    #     # plot trend error bands
    #     upper = d.trend_upper.to_list()
    #     lower = d.trend_lower.to_list()

    #     fig.add_trace(go.Scatter(x=x + x[::-1],
    #                              y=upper + lower[::-1],
    #                              fill='toself',
    #                              fillcolor='rgba(255,255,255,.25)',
    #                              line=dict(color='rgba(255,255,255,1)'),
    #                              hoverinfo='skip',
    #                              showlegend=False),
    #                   secondary_y=True)

    #     # plot price
    #     fig.add_trace(go.Scatter(mode="lines", x=x, y=d['co2_mt'],
    #                              line={"color": color,  # limegreen, lime, #E1FF00, #ccff00
    #                                    "width": 2,
    #                                    },
    #                              hovertemplate='<i>CO2</i>: $%{y:.2f}'
    #                                            + '<br><i>Time</i>: %{x| %H:%M}'
    #                                            + '<br><i>Date</i>: %{x|%a, %d %b %y}<extra></extra>',
    #                              ),
    #                   secondary_y=True)

    fig.update_layout(
        title_text="Saudi Arabia's CO2 & Population Forecast",
        hovermode="closest",
        hoverlabel=dict(align="left", bgcolor="rgba(0,0,0,0)"),
        template="plotly_dark",
        margin=dict(t=30, b=10, l=10, r=10),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        yaxis=dict(showgrid=False, title={"font": dict(size=24), "text": "CO2 (million ton)", "standoff": 10}),
        yaxis2=dict(showgrid=False, title={"font": dict(size=24), "text": "Population (million)", "standoff": 10}),
        xaxis=dict(showline=False)
    )
    return fig


def co2_ml():
    fnames = glob.glob('./data/*.csv')
    # kt of co2
    df_list = []
    for f in fnames:
        df = pd.read_csv(f).T.dropna()
        df_list.append(df)

    df = pd.concat(df_list, axis=1)
    df.rename(columns={0: 'co2_kt', 1: 'pop'}, inplace=True)
    df['co2_mt'] = df.loc[:, 'co2_kt'] / 1000
    df.index = pd.to_datetime(df.index)

    cols = ['co2_mt', 'pop']

    df = annual_prophecy(df, cols, forecast_period=15)

    fig = prophet(df)

    return fig

####################################################################################
####################################################################################
####################################################################################
####################################################################################
####################################################################################
st.title('Green Guardians :four_leaf_clover:')
st.markdown('Net0thon 2023')
st.markdown('KFUPM - Dhahran - Saudi Arabia')
'---'
title = "2020 Saudi Arabia's CO2 Emissions"
st.markdown(f"<h1 style='text-align: center; color: white;'>{title}</h1>", unsafe_allow_html=True)
# st.markdown(f"<h1 style='text-align: center; color: white; font-size: medium'>{title}</h1>", unsafe_allow_html=True)

#TODO:
# forecast in dashed lines
# add source paper
# add co2 data from other paris accord countries

# Display KSA CO2 map
with st.container():
    cols = st.columns(3)
    color_by = cols[2].selectbox('Color by:', ['Sector','Province', 'Primary Fuel','Unit Type'], 0)
    st.plotly_chart(co2_map(color_by), use_container_width=True)   # USE COLUMN WIDTH OF CONTAINER

'---'
st.markdown("<h1 style='text-align: center; color: white;'>Smart Dashboard</h1>", unsafe_allow_html=True)

# CO2 ML prediction
with st.container():
    st.plotly_chart(co2_ml(), use_container_width=True)   # USE COLUMN WIDTH OF CONTAINER


'---'
# fig = go.Figure(go.Scattermapbox(
#     fill = "toself",
#     lon = [-74, -70, -70, -74], lat = [47, 47, 45, 45],
#     marker = { 'size': 10, 'color': "orange" }))
#
# fig.update_layout(
#     mapbox = {
#         'style': "open-street-map", #stamen-terrain",
#         'center': {'lon': -73, 'lat': 46 },
#         'zoom': 5},
#     showlegend = False)
#
# st.plotly_chart(fig)


'---'

