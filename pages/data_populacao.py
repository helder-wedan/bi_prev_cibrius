from app import *

from dash_bootstrap_templates import load_figure_template

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, current_user
from dash.exceptions import PreventUpdate

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, ClientsideFunction, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import pandas as pd
from dateutil.relativedelta import relativedelta
import datetime as dt
from babel.numbers import format_currency
import openpyxl
path = 'database' 

#load_figure_template(["flatly"])

balancete_pivot_test = pd.read_csv(path+'/balancete_pivot.csv',encoding='latin-1')
balancete_pivot_test.competencia = pd.to_datetime(
    balancete_pivot_test.competencia, dayfirst=False, errors="coerce", format="%Y-%m-%d"
)

rent_meta_tx = pd.read_csv(path+'/rentabilidade_meta.csv',encoding='latin-1')
rent_meta_tx.competencia = pd.to_datetime(
    rent_meta_tx.competencia, dayfirst=False, errors="coerce", format="%Y-%m-%d"
)

base_dados_ativos = pd.read_excel(path+'/BASES_ativos.xlsx')
base_dados_assistidos = pd.read_excel(path+'/BASES_assistidos.xlsx')

lista_bases = list(base_dados_ativos.Base.unique())#.extend(list(base_dados_assistidos.Base.unique()))
lista_bases = lista_bases + list(base_dados_assistidos.Base.unique())
lista_bases = sorted(list(set(lista_bases)))

#anos = list(balancete_pivot_test.ANO.unique())
anos = balancete_pivot_test.competencia.drop_duplicates().sort_values(ascending=False).dt.strftime('%m-%Y').drop_duplicates().tolist()
#anos.sort(reverse=True)

planos = list(balancete_pivot_test.PLANO.unique())
planos.sort(reverse=False)

#===============
ativo_total = '1'
exigivel_operacional = '2.01'
exigivel_contingencial = '2.02'
patrimonio_social =  '2.03'
patrimonio_cobertura =  '2.03.01'
provisoes_matematicas = '2.03.01.01'
provisoes_constituir =  '2.03.01.01.03'

for i in [exigivel_operacional,
exigivel_contingencial,
patrimonio_social,
patrimonio_cobertura,
provisoes_matematicas,
'prov_concedidos_bd',
'prov_concedidos_cd',
'prov_conceder_bd',
'prov_conceder_cd',
]:
    balancete_pivot_test[i] = balancete_pivot_test[i] * -1

colunas = [
    'solvencia_seca',
    'solvencia_gerencial',
    'solvencia_liquida',
    'resultado_operacional',
    'maturiade_atuarial',
    'solvencia_financeira',
    'risco_legal',
    'provisoes_cd',
    'passivo_integralizar',
    'provisoes_bd',
    ativo_total,
    exigivel_operacional,
    exigivel_contingencial,
    patrimonio_social,
    patrimonio_cobertura,
    provisoes_matematicas,
    'resultado',
]

colunas_indicadores = [
    'Solvência Seca',
    'Solvência Gerencial',
    'Solvência Líquida',
    'Resultado Operacional',
    'Maturidade Atuarial',
    'Solvência Financeira',
    'Risco Legal',
    'Provisões CD',
    'Passivo a Integralizar',
    'Provisões BD',
    'Ativo Total',
    'Exigível Operacional',
    'Exigível Contingencial',
    'Patrimônio Social',
    'Patrimônio Líq. de Cobertura',
    'Provisões Matemáticas',
    'Resultado',
]

contabil = [
    ativo_total,
    exigivel_operacional,
    exigivel_contingencial,
    patrimonio_social,
    patrimonio_cobertura,
    provisoes_matematicas,
    'resultado',]

porcentagem = [
    'risco_legal',
    'provisoes_cd',
    'passivo_integralizar',
    'provisoes_bd',
]

ipca = pd.json_normalize(requests.get("http://ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='PRECOS12_IPCAG12')").json()['value'])
ipca.VALDATA = pd.to_datetime(ipca.VALDATA.str[:10])

def variacao(coluna,mes,mes_anterior,plano):
    #mes_anterior = pd.to_datetime(mes) - relativedelta(months = 1)
    variacao = balancete_pivot_test[(balancete_pivot_test.PLANO == plano)&(balancete_pivot_test.competencia == mes)][coluna].values / balancete_pivot_test[(balancete_pivot_test.PLANO == plano)&(balancete_pivot_test.competencia == mes_anterior)][coluna].values - 1
    if np.isnan(variacao):
        return "-"
    else:
        return "{:.2%}".format(variacao[0]).replace(".",",")

def montante(coluna,mes,plano):
    montante = balancete_pivot_test[(balancete_pivot_test.PLANO == plano)&(balancete_pivot_test.competencia == mes)][coluna].values[0]
    return format_currency(montante + 0.0, "BRL", locale="pt_BR")

def grafico(visualizacao,col,title,tickformat = 'n'):

    fig1 = go.Figure(layout={"template": "plotly_white"})
    x = visualizacao.competencia
    y = round(visualizacao[col],2)

    hover = "%{x|%b, %Y} <br>" + title + ": %{y}"

    fig1.add_trace(
        go.Scatter(
            x=x, 
            y=y,
            name="",
            hovertemplate=hover,
            line = dict(color='#003e4c', width=4)))

    fig1.update_layout(
        separators=',.',
        height=360,
        width=560,
        margin=dict(l=60, r=40, b=40, t=60),
        title={
            "text":'<b>'+title+'</b>',
            "font": dict(size=14),
            "y": 0.9,
            'x': 0.55,
            'xanchor': 'left',
            "yanchor": "top",
        },
        xaxis=dict(
            rangeselector=dict(
                buttons=list([

                    dict(count=6,
                        label="6m",
                        step="month",
                        stepmode="backward"),
                    dict(count=1,
                        label="12m",
                        step="year",
                        stepmode="backward"),
                    dict(count=1,
                        label="Ano atual",
                        step="year",
                        stepmode="todate"),
                    dict(label='Completo',
                         step="all")
                ])
            ),
            rangeslider=dict(
                visible=False
            ),
            type="date"
        ),
    )

    if tickformat == 's':
        fig1.update_layout(yaxis=dict(tickformat = 'p'))

    fig1.update_yaxes(mirror=True, showline=True, linewidth=2, showspikes=True,fixedrange=False) #rangemode="tozero"
    fig1.update_xaxes(mirror=True, showline=True, linewidth=2)

    return fig1

def card(name,id):
    cardbody = dbc.Card([dbc.CardBody([
                                    html.Span(name, className="card-text"),
                                    html.H6(#style={"color": "#5d8aa7"}, 
                                            id=id),
                                    ])
                                ], id=id+"_card", color="#003e4c", outline=True,inverse=True, style={"margin-top": "20px",#"margin-left": "10px",
                                        "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                        #"color": "#FFFFFF"
                                        #"width": "16rem",
                                        })
    return cardbody

def header():
    header_geral = html.Div([
        html.Div([
            dbc.Row([
                dbc.Col(
                    html.H3(
                        dbc.Badge(
                            "BI-Prev",
                            color="#a50000",
                            className="me-1",
                                    )
                        )
                    ),
                    dbc.Col([
                        html.Img(
                            id="logo",
                            src=app.get_asset_url("logo.png"),
                            height=50,
                            )
                        ],style={"textAlign": "right"},),
                    ]),
                ],style={
                    "background-color": "#003e4c",  # 003e4c",
                    "margin": "0px",
                    "padding": "20px",
                    },
        ),
        html.Div([
            dbc.Nav([
                dbc.Navbar(
                    dbc.Container(
                        children=[
                            dbc.NavItem(
                                dbc.NavLink(
                                    "Indicadores   ",
                                    href="/indicadores",
                                    className="nav-link",
                                    ),
                                    style={
                                        "margin": "-20px",
                                        "margin-left": "20px",
                                    },
                                ),
                            dbc.NavItem(
                                dbc.NavLink('',#'População   ',
                                             href='/populacao', 
                                             className="nav-link"),
                                             style={"margin": "-20px",
                                                    "margin-left": "20px"},),
                            dbc.NavItem(
                                dbc.NavLink('',#'Menu 3   ',
                                             href='/beneficiarios', 
                                             className="nav-link"),
                                             style={"margin": "-20px",
                                                    "margin-left": "20px"},),
                                dbc.NavItem(
                                dbc.NavLink(
                                        dbc.Button("Logout", id="logout_button", style={"background-color": "#a50000"}),
                                    style={"padding": "20px", "justify-content": "end", "display": "flex",
                                           "margin": "-20px","margin-left": "20px"})
                                ),
                                    ],
                            fluid=True,
                        ),
                        color="light",
                        dark=False,
                        # class_name='collapse navbar-collapse',
                    )
                ],class_name="navbar navbar-light bg-light",),
                # ]),
            ]),
    ])

    return header_geral

tela_indicadores = html.Div(children=[
            header(),
            dbc.Row([
                dbc.Col([
                    html.H5(
                        dbc.Badge(
                            "Selecionar a Base:",
                            color="#5d8aa7",
                            className="me-1",
                            style={
                                "margin-left": "30px",#"25px",
                                "margin-top": "10px",
                                },
                                    )
                            ),
                        dcc.Dropdown(
                            id="select-base",
                            #value=lista_bases[0],
                            multi=False,
                            options=[
                                {
                                    "label": i,
                                    "value": i,
                                }
                                for i in lista_bases
                            ],
                            placeholder="Selecione o Base",
                            style={
                                #"width": "60%",
                                #'padding': '3px',
                                "margin-left": "15px",#"15px",
                                #'font-size':'18px',
                                "textAlign": "center",
                            },
                            ),
                            ],width=True),# xs = 2, sm=2, md=2, lg=2),# width=2),

                dbc.Col([
                    html.H5(
                        dbc.Badge(
                            "Selecionar competência:",
                            color="#5d8aa7",
                            className="me-1",
                            style={
                                "margin-left": "35px",
                                "margin-top": "10px",
                                },
                                    )
                            ),
                        dcc.Dropdown(
                            id="select-ano-base",
                            #value=anos[0],
                            placeholder="Selecione o mês",
                            style={
                                #"width": "60%",
                                #'padding': '3px',
                                "margin-left": "15px",
                                #'font-size':'18px',
                                "textAlign": "center",
                            },
                            ),

                        ], width=True),#xs = 2, sm=2, md=2, lg=2),#width=2),
                                    dbc.Col([
                    html.H5(
                        dbc.Badge(
                            "Selecionar competência anterior:",
                            color="#5d8aa7",
                            className="me-1",
                            style={
                                #"margin-left": "30px",
                                "margin-top": "10px",
                                },
                                    )
                            ),
                        dcc.Dropdown(
                            id="select-ano-base-anterior",
                            #value=anos[1],
                            placeholder="Selecione o mês a comparar",
                            style={
                                #"width": "80%",
                                #'padding': '3px',
                                #"margin-left": "15px",
                                #'font-size':'18px',
                                "textAlign": "center",
                            },
                            ),

                        ], width=True),#xs = 2, sm=2, md=2, lg=2),#width=2),                                 
            dbc.Row([

                html.Div([], id='tabela_populacao',
                         className="col-4"),
                
            ], justify="center",),

]),
        dbc.Row([
                dbc.Col([
                    html.H5(
                        dbc.Badge(
                            "Selecionar competência:",
                            color="#5d8aa7",
                            className="me-1",
                            style={
                                "margin-left": "35px",
                                "margin-top": "10px",
                                },
                                    )
                            ),
                        dcc.Dropdown(
                            id="select-ano",
                            value=anos[0],
                            options=[
                                {
                                    "label": i,
                                    "value": i,
                                }
                                for i in anos
                            ],
                            placeholder="Selecione o mês",
                            style={
                                #"width": "60%",
                                #'padding': '3px',
                                "margin-left": "15px",
                                #'font-size':'18px',
                                "textAlign": "center",
                            },
                            ),

                        ], width=True),#xs = 2, sm=2, md=2, lg=2),#width=2),
                                    dbc.Col([
                    html.H5(
                        dbc.Badge(
                            "Selecionar competência anterior:",
                            color="#5d8aa7",
                            className="me-1",
                            style={
                                "margin-left": "30px",
                                "margin-top": "10px",
                                },
                                    )
                            ),
                        dcc.Dropdown(
                            id="select-ano-anterior",
                            #value=anos[1],
                            placeholder="Selecione o mês a comparar",
                            style={
                                #"width": "80%",
                                #'padding': '3px',
                                "margin-left": "15px",
                                #'font-size':'18px',
                                "textAlign": "center",
                            },
                            ),

                        ], width=True),#xs = 2, sm=2, md=2, lg=2),#width=2),
        
                    dbc.Col([
                    html.H5(
                        dbc.Badge(
                            "Selecionar o Plano:",
                            color="#5d8aa7",
                            className="me-1",
                            style={
                                "margin-left": "0px",#"25px",
                                "margin-top": "10px",
                                },
                                    )
                            ),
                        dcc.Dropdown(
                            id="select-plano",
                            value=planos[0],
                            multi=False,
                            options=[
                                {
                                    "label": i,
                                    "value": i,
                                }
                                for i in planos
                            ],
                            placeholder="Selecione o Plano",
                            style={
                                #"width": "60%",
                                #'padding': '3px',
                                "margin-left": "0px",#"15px",
                                #'font-size':'18px',
                                "textAlign": "center",
                            },
                            ),
                            ],width=True),# xs = 2, sm=2, md=2, lg=2),# width=2),
                            
]),
            dbc.Row([
                dbc.Col([
                        dbc.Row([ 
                            
                            card("Solvência Seca","solvencia_seca"),                
                            dbc.Tooltip(
                                "(Patrimônio de Cobertura + Fundos Previdenciais) / Provisões Matemáticas." +
                                " Quando maior do que 1, tem-se que o plano é atuarial e economicamente solvente, com parcela do Patrimônio Social equivalente ao Fundo Previdencial constituído para cobertura de riscos.",
                                target="solvencia_seca"+"_card",
                                ),
                            

                            card("Solvência Gerencial","solvencia_gerencial"),
                            dbc.Tooltip(
                                "Patrimônio de Cobertura / Provisões Matemáticas."+
                                 ' Quando é maior do que 1, tem-se que o plano é atuarial e economicamente solvente.',
                                target="solvencia_gerencial"+"_card",
                                ),
                            

                            card("Solvência Líquida","solvencia_liquida"),
                            dbc.Tooltip(
                                "(Patrimônio de Cobertura + Provisões a Constituir) / Provisões Matemáticas."+
                                ' Quando é maior do que 1, tem-se que o plano possui solvência líquida, atuarial e economicamente, isto é, as obrigações estão devidamente integralizadas.',
                                target="solvencia_liquida"+"_card",
                                ),
                            

                            card("Resultado Operacional","resultado_operacional"),
                            dbc.Tooltip(
                                "Adições / Deduções. Maduro se < 1.",
                                target="resultado_operacional"+"_card",
                                ),
                            

                            card("Maturidade Atuarial",'maturiade_atuarial'),
                            dbc.Tooltip(
                                "Benefícios a Conceder / Benefícios Concedidos. Quando é menor do que 1, tem-se que o plano vai adquirido maturidade atuarial.",
                                target="maturiade_atuarial"+"_card",
                                ),
                            

                            card("Solvência Financeira",'solvencia_financeira'),
                            dbc.Tooltip(
                                "(Adições + Fluxo dos Investimentos) / Deduções. Insolvente se < 1.",
                                target="solvencia_financeira"+"_card",
                                ),
                            

                            card("Risco Legal",'risco_legal'),
                            dbc.Tooltip(
                                "Exigível Contingencial / Patrimônio Social",
                                target="risco_legal"+"_card",
                                ),
                            

                            card("Provisões em CD",'provisoes_cd'),
                            dbc.Tooltip(
                                "(Benefícios Concedidos em CD + Benefícios a Conceder em CD) / Provisões Matemáticas. CD = Contribuição Definida",
                                target="provisoes_cd"+"_card",
                                ),
                            

                            card("Passivo a Integralizar",'passivo_integralizar'),
                            dbc.Tooltip(
                                "Provisões a Constituir / Provisões Matemáticas.",
                                target="passivo_integralizar"+"_card",
                                ),

                            
                            card("Provisões em BD",'provisoes_bd'),
                            dbc.Tooltip(
                                "1 - (Provisões em CD + Passivo a Integralizar)",
                                target="provisoes_bd"+"_card",
                                ),
                            

                            card("Ativo Total",'ativo'),
                            dbc.Tooltip(
                                "Conta '1' do balancete",
                                target="ativo"+"_card",
                                ),
                            

                            card("Exigível Operacional",'exig_operacional'),
                            dbc.Tooltip(
                                "Conta '2.01' do balancete",
                                target="exig_operacional"+"_card",
                                ),                            
                            

                            card("Exigível Contingencial",'exig_contingencial'),
                            dbc.Tooltip(
                                "Conta '2.02' do balancete",
                                target="exig_contingencial"+"_card",
                                ),                            
                            

                            card("Patrimônio Social",'patrimonio_social'),
                            dbc.Tooltip(
                                "Conta '2.03' do balancete",
                                target="patrimonio_social"+"_card",
                                ),                            
                          
                            
                            card("Patrimônio Líquido de Cobertura",'plc'),
                            dbc.Tooltip(
                                "Conta '2.03.01' do balancete",
                                target="plc"+"_card",
                                ),                            
                            

                            card("Provisões Matemáticas",'provisoes'),
                            dbc.Tooltip(
                                "Conta '2.03.01.01' do balancete",
                                target="provisoes"+"_card",
                                ),
                            

                            card("Resultado",'resultado'),
                            dbc.Tooltip(
                                "Patrimônio de Cobertura - Provisões Matemáticas. Superávit se > 0. Equilíbrio se = 0. Déficit se < 0.",
                                target="resultado"+"_card",
                                ),

                        ],style={"margin-left": "25px",},),
                        ],xs = 7, sm=7, md=5, lg=2),# width=True),# 'One of six columns'),#xs = 2, sm=2, md=2, lg=2),# width=2),

                    dbc.Col([
                       html.Div([], id='tabela_provisoes'),
                       dcc.Loading(
                            id="loading-1",
                            type="dot",
                            ),
                       dcc.Loading(
                            id="loading-2",
                            type="dot",
                            ),                        
                 dbc.Row([
                    
                      dbc.Col([html.Div([dcc.Graph(id="rentabilidade_graph"),],"One of two columns")], align="start"),
                      dbc.Col([html.Div([dcc.Graph(id="provisoes_graph"),],"One of two columns")], align="end"),                             
                        ],style={"margin-left": "0px",
                         "margin-top": "30px",},),

                 dbc.Row([
                    dbc.Col([html.Div([dcc.Graph(id="solvencia_seca_graph")],"One of four columns")], align="start"),
                    dbc.Col([html.Div([dcc.Graph(id="solvencia_liquida_graph")],"One of four columns")],align="end"),
                        ],style={"margin-left": "0px",
                         "margin-top": "30px",},),
                dbc.Row([
                      dbc.Col([html.Div([dcc.Graph(id="maturidade_atuarial_graph"),],"One of two columns")], align="start"),
                      dbc.Col([html.Div([dcc.Graph(id="risco_legal_graph"),],"One of two columns")], align="end"),
                      ],style={"margin-left": "0px",
                         "margin-top": "30px",},),
                dbc.Row([
                      dbc.Col([html.Div([dcc.Graph(id="passivo_integralizar_graph"),],"One of two columns")], align="start"),                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
                      dbc.Col([html.Div([dcc.Graph(id="ativo_graph"),],"One of two columns")], align="end"),
                    ],style={"margin-left": "0px",
                         "margin-top": "30px",},),
                dbc.Row([
                      dbc.Col([html.Div([dcc.Graph(id="ex_cont_graph"),],"One of two columns")], align="start"),
                      dbc.Col([html.Div([dcc.Graph(id="plc_graph"),],"One of two columns")], align="end"),
                    ],style={"margin-left": "0px",
                         "margin-top": "30px",},),
                dbc.Row([
                      dbc.Col([html.Div([dcc.Graph(id="solvencia_gerencial_graph"),],"One of two columns")], align="start"),
                      dbc.Col([html.Div([dcc.Graph(id="resultado_operacional_graph"),],"One of two columns")], align="end"),
                    ],style={"margin-left": "0px",
                         "margin-top": "30px",},),
                dbc.Row([
                      dbc.Col([html.Div([dcc.Graph(id="solvencia_financeira_graph"),],"One of two columns")], align="start"),
                      dbc.Col([html.Div([dcc.Graph(id="provisoes_cd_graph"),],"One of two columns")], align="end"),
                    ],style={"margin-left": "0px",
                         "margin-top": "30px",},),
                dbc.Row([
                      dbc.Col([html.Div([dcc.Graph(id="provisoes_bd_graph_graph"),],"One of two columns")], align="start"),
                      dbc.Col([html.Div([dcc.Graph(id="ex_opera_graph"),],"One of two columns")], align="end"),
                    ],style={"margin-left": "0px",
                         "margin-top": "30px",},),
                dbc.Row([
                      dbc.Col([html.Div([dcc.Graph(id="patrimonio_social_graph"),],"One of two columns")], align="start"),
                      dbc.Col([html.Div([dcc.Graph(id="resultado_graph"),],"One of two columns")], align="end"),
                    ],style={"margin-left": "0px",
                         "margin-top": "30px",},),
                
                ],style={"margin-left": "0px",
                         "margin-top": "15px",}, 
                #width=True
                ),
                        ]),
                
                dcc.Location(id="data-url"), 
                ],style={
                    "background-color": '#f7f7f7'# "#F8F8FB",
                    },
            )

##### Tela 2 ####


# =========  Layout  =========== #
def render_layout(username):
    template = tela_indicadores
    return template 

# =========  Callbacks Page1  =========== #
# CALLBACKS =====
@app.callback(
    Output("select-ano-base", "options"),
    #Output("select-ano-base", "value"),],
    Input("select-base", "value")
)
def update_dropdown_meses_bases(base):
    if base is None:
        return []
    
    elif 'ASSISTIDOS' in base.upper():
        dados = base_dados_assistidos

    else:
        dados = base_dados_ativos

    competencias = list(dados[dados.Base == base]['Competência'].sort_values(ascending=False).dt.strftime('%m-%Y').unique())

    return competencias#,competencias[0]

@app.callback(
    Output("select-ano-base-anterior", "options"),
    #Output("select-ano-anterior", "value"),],
    [Input("select-base", "value"),
    Input("select-ano-base", "value")]
)
def update_dropdown_meses_anteriores_bases(base , mes_ano_selecionado):
    if base is None:
        return []
    
    elif 'ASSISTIDOS' in base.upper():
        dados = base_dados_assistidos

    else:
        dados = base_dados_ativos

    competencias = list(dados[dados.Base == base]['Competência'].sort_values(ascending=False).dt.strftime('%m-%Y').unique())

    if mes_ano_selecionado is not None:
        index_mes_selecionado = competencias.index(mes_ano_selecionado)
        meses_anteriores = [
            {"label": mes_ano, "value": mes_ano}
            for mes_ano in competencias[index_mes_selecionado+1:]
        ]

        return meses_anteriores
    else:
        return []

@app.callback(
    
        Output('tabela_populacao','children')
    ,    
    [
        Input('select-ano-base', 'value'),
        Input('select-base', 'value'),
        Input("select-ano-base-anterior", 'value'),
    ],
)
def update_table(mes,base,mes_anterior):

    if base is None:
        return []
    
    elif 'ASSISTIDOS' in base.upper():
        dados = base_dados_assistidos

    else:
        dados = base_dados_ativos

    if mes is None:
        return []

    if mes_anterior is not None:

        base_filtrada = dados[(dados.Base == base)&(dados['Competência'].dt.strftime('%m-%Y') == mes)].copy()
        base_filtrada_anterior = dados[(dados.Base == base)&(dados['Competência'].dt.strftime('%m-%Y') == mes_anterior)].copy()

        base_filtrada['Competência'] = base_filtrada['Competência'].dt.strftime("%m/%Y")
        base_filtrada_anterior['Competência'] = base_filtrada_anterior['Competência'].dt.strftime("%m/%Y")
        base_filtrada.set_index('Competência',inplace=True)
        base_filtrada_anterior.set_index('Competência',inplace=True)

        base_filtrada = base_filtrada.T
        base_filtrada_anterior = base_filtrada_anterior.T

        tabela = pd.concat([base_filtrada,#.rename(columns={base_filtrada.columns[0]:data1}),
                            base_filtrada_anterior,#.rename(columns={base_filtrada_anterior.columns[0]:data2})
                            ],axis=1).reset_index(names=base)
        
        tabela['Var (%)'] = tabela.iloc[1:,1] / tabela.iloc[1:,2] - 1
        
        tabela = tabela.iloc[1:,:]

        tabela['Var (%)'] = tabela['Var (%)'].astype(float).map('{:.2%}'.format)
        tabela['Var (%)'] = tabela['Var (%)'].astype(str).replace(".",",")


        print(tabela)

        tabela_dash = dash_table.DataTable(
        columns=[
            {"name": i,
                "id": i,
                "deletable": False,
                }
            for i in tabela.columns
        ],
        data=tabela.to_dict("records"),
        style_as_list_view=True,
        style_header={
            "backgroundColor": "#003e4c",
            "color": "white",
            "fontWeight": "bold",
            "text-align": "center",
            "fontSize": 14,
        },
    #    style_data_conditional=[
    #        {"if": {"column_id": tabela.columns[0]},
    #            "textAlign": "left",#}, 
    #        {"if": {"row_index": 0}, 
    #           "fontWeight": "bold",},
    #      {"if": {"row_index": 1},
    #         "fontWeight": "bold",},
        #    {"if": {"row_index": len(tabela_df) - 2},
        #       "fontWeight": "bold",},
        #  {"if": {"row_index": len(tabela_df) - 1},
        #     "fontWeight": "bold"
                #}],

        style_cell={
            "padding": "8px",
            "font-family": "Helvetica",
            "fontSize": 13,
            "color": "#5d8aa7",
            "fontWeight": "bold",
        },
        fill_width=False,
    )
        return tabela_dash
    
    else:
        return []
        



@app.callback(
    [Output("select-ano-anterior", "options"),
    Output("select-ano-anterior", "value"),],
    Input("select-ano", "value")
)
def update_dropdown_meses_anteriores(mes_ano_selecionado):
    if mes_ano_selecionado is None:
        return []

    index_mes_selecionado = anos.index(mes_ano_selecionado)
    meses_anteriores = [
        {"label": mes_ano, "value": mes_ano}
        for mes_ano in anos[index_mes_selecionado+1:]
    ]

    selecao=None

    return meses_anteriores,selecao


@app.callback(
    [   Output("loading-1", "children"),
        Output("solvencia_seca", 'children'),
        Output("solvencia_gerencial", 'children'),
        Output("solvencia_liquida", 'children'),
        Output("resultado_operacional", 'children'),
        Output('maturiade_atuarial', 'children'),
        Output('solvencia_financeira', 'children'),
        Output('risco_legal', 'children'),
        Output('provisoes_cd', 'children'),
        Output('passivo_integralizar', 'children'),
        Output('provisoes_bd', 'children'),
        Output('ativo', 'children'),
        Output('exig_operacional', 'children'),
        Output('exig_contingencial', 'children'),
        Output('patrimonio_social', 'children'),
        Output('plc', 'children'),
        Output('provisoes', 'children'),
        Output('resultado', 'children'),
    ],
    [
        Input('select-ano', 'value'),
        Input('select-plano', 'value'),
    ],
)
def update_cards(ano, plano):

    base_filtrada = balancete_pivot_test[(balancete_pivot_test.PLANO == plano) & (balancete_pivot_test.competencia == ano)].copy()

    if len(base_filtrada) == 0:
        return ['-' for i in colunas]
    
    else:
        valores = base_filtrada[colunas].copy()

    #    for i in contabil:
    #        valores[i] = format_currency(valores[i].fillna(0), "BRL", locale="pt_BR")
        for i in porcentagem:
            valores.loc[:,i] = ((round(valores[i] * 100 + 0.0,2)).astype(str) + ' %').str.replace('.',',',regex=False)
#            valores.loc[:,i] = valores.loc[:,i].str.replace('-0,0 %','0,0 %', regex=False)
    #        valores[i] = (str(round(valores[i]*100,2))+'%').replace(".", ",")

        for i in valores[contabil]:
            valores[i] = [format_currency(v + 0.0, "BRL", locale="pt_BR") for v in valores[i]]
            #valores[i] = valores[i].str.replace('-R$ 0,00','R$ 0,00', regex=False)

        for i in valores[valores.columns[:6]]:
            valores[i] = round(valores[i] + 0.0,4).astype(str).str.replace('.',',',regex=False)
            valores[i] = valores[i].str.replace(r'[-+]?\binf\b', '',regex=True)
        
        outputs = ['']
        [outputs.append(i) for i in valores.values[0]]
    
        return [i for i in outputs]

@app.callback(
    [   Output("loading-2", "children"),
        Output("solvencia_seca_graph",'figure'),
        Output("solvencia_liquida_graph",'figure'),
        Output("maturidade_atuarial_graph",'figure'),
        Output("risco_legal_graph",'figure'),
        Output("passivo_integralizar_graph",'figure'),                                                                                                                                                                    
        Output("ativo_graph",'figure'),
        Output("ex_cont_graph",'figure'),
        Output("plc_graph",'figure'),                                                                      
        Output("resultado_graph",'figure'),                                                                      
        Output("solvencia_gerencial_graph",'figure'),
        Output("resultado_operacional_graph",'figure'),
        Output("solvencia_financeira_graph",'figure'),
        Output("provisoes_cd_graph",'figure'),
        Output("provisoes_bd_graph_graph",'figure'),
        Output("ex_opera_graph",'figure'),
        Output("patrimonio_social_graph",'figure'),
        Output("provisoes_graph",'figure'),
    ],
    [
        Input('select-ano', 'value'),
        Input('select-plano', 'value'),
    ],
)
def update_graphs(ano, plano):
    base_grafico = balancete_pivot_test[(balancete_pivot_test.PLANO == plano)].copy().sort_values(by='competencia')

    lista_graficos=['']

    for col,ind in zip(colunas,colunas_indicadores):
        tickf = 's' if col in porcentagem else 'n'
        
        lista_graficos.append(grafico(
        base_grafico,
        col,
        ind,
        tickf,
        ))


    return [i for i in lista_graficos]
    #

@app.callback(
    
        Output('tabela_provisoes','children')
    ,    
    [
        Input('select-ano', 'value'),
        Input('select-plano', 'value'),
        Input("select-ano-anterior", 'value'),
    ],
)
def update_table(mes,plano,mes_anterior):
    mes = pd.to_datetime(mes)
    periodo =  str(mes.strftime("%m/%Y"))
    if mes_anterior is None:
        mes_anterior = mes - relativedelta(months = mes.month)
    else:
        mes_anterior = pd.to_datetime(mes_anterior)


    #mes_anterior = mes - relativedelta(months = 1)
    #ipca_filtro1 = mes_anterior if plano =='BD-01' else mes
    ipca_filtro2 = pd.to_datetime(mes) - relativedelta(months = 1) if plano == 'BD-01' else mes

    tabela = {'Conceitos':
    [  'Patrimônio Líquido de Cobertura',
        'Provisões Matemáticas',
        'Provisões Matemáticas - Benefícios Concedidos - BD',
        'Provisões Matemáticas - Benefícios Concedidos - CD',

        'Provisões Matemáticas - Benefícios a Conceder - BD',
        'Provisões Matemáticas - Benefícios a Conceder - CD',

        'Provisões a Constituir',
        'Resultado',
        f'Inflação do período {periodo} (t-1)' if plano =='BD-01' else f'Inflação do período {periodo} (t)',
        f'Taxa de Juros a.a. em {mes.year}',
        f'Meta Atuarial em {periodo}',
        f'Rentabilidade em {periodo}',
        ],
    str(mes)[:7]:
    [   montante(patrimonio_cobertura,mes,plano),
        montante(provisoes_matematicas,mes,plano),
        montante('prov_concedidos_bd',mes,plano),
        montante('prov_concedidos_cd',mes,plano),
        montante('prov_conceder_bd',mes,plano),
        montante('prov_conceder_cd',mes,plano),
        montante(provisoes_constituir,mes,plano),
        montante('resultado',mes,plano),
        "{:.2f}%".format(ipca[ipca.VALDATA == ipca_filtro2].VALVALOR.values[0]).replace(".",","),
        '{:.2f}%'.format(rent_meta_tx[(rent_meta_tx.competencia == mes)&(rent_meta_tx.PLANO == plano)]['taxa_juros'].values[0]).replace(".",","),        
        '{:.2f}%'.format(rent_meta_tx[(rent_meta_tx.competencia == mes)&(rent_meta_tx.PLANO == plano)]['meta_atuarial'].values[0]).replace(".",","),
        '{:.2f}%'.format(rent_meta_tx[(rent_meta_tx.competencia == mes)&(rent_meta_tx.PLANO == plano)]['rent_perc'].values[0]).replace(".",","),
    ],

    
    str(mes_anterior)[:7]:
    [   montante(patrimonio_cobertura,mes_anterior,plano),
        montante(provisoes_matematicas,mes_anterior,plano),
        montante('prov_concedidos_bd',mes_anterior,plano),
        montante('prov_concedidos_cd',mes_anterior,plano),
        montante('prov_conceder_bd',mes_anterior,plano),
        montante('prov_conceder_cd',mes_anterior,plano),
        montante(provisoes_constituir,mes_anterior,plano),
        montante('resultado',mes_anterior,plano),                
     '',
     '',
     '',
     '',
    ],
    'Var.':
    [   variacao(patrimonio_cobertura,mes,mes_anterior,plano),
        variacao(provisoes_matematicas,mes,mes_anterior,plano),
        variacao('prov_concedidos_bd',mes,mes_anterior,plano),
        variacao('prov_concedidos_cd',mes,mes_anterior,plano),
        variacao('prov_conceder_bd',mes,mes_anterior,plano),
        variacao('prov_conceder_cd',mes,mes_anterior,plano),
        variacao(provisoes_constituir,mes,mes_anterior,plano),
        variacao('resultado',mes,mes_anterior,plano),                
        '',
        '',
        '',
        '',

        ]
        
        }
    tabela_df = pd.DataFrame.from_dict(tabela).fillna('-')

    tabela_dash = dash_table.DataTable(
    columns=[
        {"name": i,
            "id": i,
            "deletable": False,
            }
        for i in tabela_df.columns
    ],
    data=tabela_df.to_dict("records"),
    style_as_list_view=True,
    style_header={
        "backgroundColor": "#003e4c",
        "color": "white",
        "fontWeight": "bold",
        "text-align": "center",
        "fontSize": 14,
    },
    style_data_conditional=[
        {"if": {"column_id": tabela_df.columns[0]},
            "textAlign": "left",#}, 
#        {"if": {"row_index": 0}, 
 #           "fontWeight": "bold",},
  #      {"if": {"row_index": 1},
   #         "fontWeight": "bold",},
    #    {"if": {"row_index": len(tabela_df) - 2},
     #       "fontWeight": "bold",},
      #  {"if": {"row_index": len(tabela_df) - 1},
       #     "fontWeight": "bold"
            }],

    style_cell={
        "padding": "8px",
        "font-family": "Helvetica",
        "fontSize": 13,
        "color": "#5d8aa7",
        "fontWeight": "bold",
    },
    fill_width=False,
)

    return tabela_dash

@app.callback(
    #[   Output("loading-2", "children"),
        Output("rentabilidade_graph",'figure'),
    #],
    [
        Input('select-ano', 'value'),
        Input('select-plano', 'value'),
    ],
)
def update_rentabilidade(competencia, plano):
    ano=pd.to_datetime(competencia).year
    base_rentabilidade = rent_meta_tx[(rent_meta_tx.PLANO == plano)&(rent_meta_tx.competencia.dt.year == ano)].copy()
    base_rentabilidade['Rentabilidade'] = ((1 + base_rentabilidade['rent_perc'] /100).cumprod() - 1)*100
    base_rentabilidade['Meta Atuarial'] = ((1 + base_rentabilidade['meta_atuarial'] /100).cumprod() - 1)*100

    fig1 = go.Figure(layout={"template": "plotly_white"})
    x = base_rentabilidade.competencia
    y1 = round(base_rentabilidade['Rentabilidade'],2)
    y2 = round(base_rentabilidade['Meta Atuarial'],2)

    hover = "%{x|%b, %Y} <br>" + plano + ": %{y}"

    fig1.add_trace(
        go.Scatter(
            x=x, 
            y=y1,
            name=y1.name,
            #fill='tozeroy',
            hovertemplate=hover,
            line = dict(color='#003e4c', width=4)))

    fig1.add_trace(
        go.Scatter(
            x=x, 
            y=y2,
            name=y2.name,
            #fill='tonexty',
            hovertemplate=hover,
            line = dict(color='#a50000', 
                        width=4)))

    fig1.update_layout(
        separators=',.',
        height=360,
        width=560,
        margin=dict(l=60, r=40, b=40, t=60),
        title={
            "text":'<b>'+f'{plano} - Rentabilidade x Meta Atuarial - {ano}'+'</b>',
            "font": dict(size=14),
            "y": 0.9,
            'x': 0.5,
            'xanchor': 'center',
            "yanchor": "top",
        },
        legend=dict(
            #yanchor="top",
            #y=0.8,
            xanchor="center",
            x=0.5,
            orientation="h"
        )
    )

    fig1.update_yaxes(mirror=True, showline=True, linewidth=2, 
                      showspikes=True,fixedrange=False,
                      ticksuffix= "%")  #rangemode="tozero"
    fig1.update_xaxes(mirror=True, showline=True, linewidth=2)

    return fig1


@app.callback(
    Output('data-url', 'pathname'),
    Input('logout_button', 'n_clicks'),
    )
def successful(n_clicks):
    if n_clicks == None:
        raise PreventUpdate
    
    if current_user.is_authenticated:
        logout_user()
        return '/login'
    else: 
        return '/login'

