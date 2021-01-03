import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import requests
import json
from pandas.io.json import json_normalize
from functools import reduce
import datetime
from dash.dash import no_update


user_data = pd.read_csv('drewdata.csv')

#CHANGED THEME TO DARK ******
external_stylesheets = [dbc.themes.DARKLY]
app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

'''Tab one content changed:
- added title and description
- added extra DIV to house background image
- changed height'''
#

#Replace DBC.Tab with two DIVS
#inner div contains all of the content
#outer div contains nothing but the inner div
#update their styles accordingly
#most html elements had style elements added!
tab1_content = html.Div([
                    html.Div([
                        html.Br(),
                        html.Br(),
                        #these two H2 and H5 are new (and the breaks)
                        html.H2("ONE. YEAR. GREATER.",style={"text-align":"center"}),
                        html.H5("You worked hard this year. Own it. Use this web application to see your Peloton Stats for 2020.",style={"text-align":"center"}),
                        html.Br(),
                        html.Div([
                            dbc.Button("Enter Account Info", id="open-centered"),
                            dbc.Modal([dbc.ModalHeader("Enter your Information Below"),dbc.ModalBody(
                                html.Div([
                                    dbc.Input(id="input", placeholder="username...", type="text"),
                                    html.Br(),
                                    dbc.Input(id="password", placeholder="password...", type="text")]
                                    )
                                ),
                            dbc.ModalFooter(
                                dbc.Button("Submit", id="close-centered", className="ml-auto")
                                )],id="modal-centered",centered=True),
                        html.Div(html.P(id="message")),
                        html.Div(html.P(id="password_viewer")),
                        html.Div(
                            dbc.Button("Calculate My Year", id="example-button", className="mr-2")),
                            dbc.Spinner(html.Div(id="loading-output")),
                            html.Br(),
                            html.P(id="confirmation_message")],style={"text-align":"center"})],
                    style={"width": "100%","height": "100%"})],
                style={"width": "100%","height": "600px","background-image":'url("https://peloton.shorthandstories.com/how-hiit-hits-different-on-the-bike--tread-and-floor/assets/RNqFtnNyb0/olivia_hiit-ride_oz.gif")'})


#Nothing much changed here just changed the width of the cards so the stats are bigger than the pie chart
#added an H3 to the pie chart as a title bc plotly titles are ugly :)
tab2_content = dbc.Card(
    dbc.CardBody([
    html.Div(html.H2("WOW! You killed this year... Let's look closer at what you achieved.",id="Title")),
        html.Br(),
         dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Br(),
                    html.Div(html.H4(id="total_rides")),
                    html.Br(),
                    html.Div(html.H4(id="total_calories")),
                    html.Br(),
                    html.Div(html.H4(id="fave_workout"))],outline=True),width=7),
            dbc.Col(dbc.Card([html.Br(),html.H3("Your Workout Types of 2020"),dcc.Graph(id="workout_pie")]),width=5)
            ])
         ])
    )

#added this as a holder not important
tab3_content = html.Div([html.P("this will be the third tab!")])

#updated this you can jsut copy and paste the whole thing
app.layout = html.Div(children=[
    html.Div([
        html.Div(html.Img(
            src="https://from128.com/images/peloton-logo-trans.png",style={'height':'7%', 'width':'7%','padding': '10px 0px 12px 0px'}),
            style={'width': '10%', 'display': 'inline'}),
        html.Div(html.H1(children='PELOTON YEAR IN REVIEW'),style={'width': '90%', 'display': 'inline-block','text-align':'left','padding': '0px 0px 10px 0px','vertical-align':'bottom'}),
        ]),
    html.Div([
        dbc.Tabs([
            dbc.Tab(tab1_content,label="Get Started", tab_id="tab-1"),
            dbc.Tab(tab2_content,label="Reviewing 2020", tab_id="tab-2"),
            dbc.Tab(tab3_content,label="line chart",tab_id="tab-3")],
            id="card-tabs",
            card=False,
            active_tab="tab-1")]
        )]
    )

#my get data is out of date
def getdata(value1,value2):
    s = requests.Session()
    user=value1
    pw = value2
    payload = {'username_or_email': user, 'password':pw}
    s.post('https://api.onepeloton.com/auth/login', json=payload)


    me_url = 'https://api.onepeloton.com/api/me'
    response = s.get(me_url)
    apidata = s.get(me_url).json()

    #Flatten API response into a temporary dataframe
    df_my_id = json_normalize(apidata, 'id', ['id'])
    df_my_id_clean = df_my_id.iloc[0]
    my_id = (df_my_id_clean.drop([0])).values.tolist()
 
    url = 'https://api.onepeloton.com/api/user/{}/workouts?joins=ride,ride.instructor&limit=250&page=0'.format(*my_id)
    response = s.get(url)
    data = s.get(url).json()
    df_workouts_raw = json_normalize(data['data'])

    '''Third API Call - GET Workout Metrics''' 
    #Create Dataframe of Workout IDs to run through our Loop
    df_workout_ids = df_workouts_raw.filter(['id'], axis=1)

    #Define the imputs for the for loop
    workout_ids = df_workout_ids.values.tolist()
    workout_ids2 = [i[0] for i in workout_ids]

    #Create empty dataframes to write iterations to
    df_tot_metrics = pd.DataFrame([])
    df_avg_metrics = pd.DataFrame([])

    for workout_id in workout_ids2:
         response2 = s.get('https://api.onepeloton.com/api/workout/{}/performance_graph?every_n=300'.format(workout_id))
         data2 = response2.json()
         #Flatten API response into a temporary dataframe - exception handling because each workout type has a 
         #different structure to the API response, with different metrics.  Additionally, this call also generates
         #a number of rows so we have to transpose and flatten the dataframe.
         try:
              df_avg_raw = json_normalize(data2['average_summaries'])
         except:
              pass
         else:
              df_avg_raw = json_normalize(data2['average_summaries'])
              df_avg_stg = df_avg_raw.T
         try:
              df_avg_stg.columns = df_avg_stg.iloc[0]
         except:
              pass
         else:
              df_avg_stg.columns = df_avg_stg.iloc[0]
              df_avg = df_avg_stg.drop(['display_name', 'slug', 'display_unit'])
              df_avg['id'] = workout_id
         try:
              df_tot_raw = json_normalize(data2['summaries'])
         except:
              pass
         else:
              df_tot_raw = json_normalize(data2['summaries'])
              df_tot_stg = df_tot_raw.T
         try:
              df_tot_stg.columns = df_tot_stg.iloc[0]
         except:
              pass
         else:
              df_tot_stg.columns = df_tot_stg.iloc[0]
              df_tot = df_tot_stg.drop(['display_name', 'slug', 'display_unit'])
              df_tot['id'] = workout_id
         #Append each run through the loop to the dataframe
         df_tot_metrics = df_tot_metrics.append(df_tot, sort=False)
         try:
              df_avg_metrics = df_avg_metrics.append(df_avg, sort=False)
         except:
              pass
         else:
              df_avg_metrics = df_avg_metrics.append(df_avg, sort=False)

    df_tot_metrics_clean = df_tot_metrics.drop_duplicates()
    df_avg_metrics_clean = df_avg_metrics.drop_duplicates()
    df_workout_metrics = df_avg_metrics_clean.merge(df_tot_metrics_clean, left_on='id', right_on='id', how='right')

    df_peloton_final_stg = df_workouts_raw.merge(df_workout_metrics, left_on='id', right_on='id', how='left')

    def convert_timestamps(row):
        mili = row['created_at']
        ts = datetime.datetime.fromtimestamp(mili).strftime('%Y-%m-%d %H:%M:%S')
        return ts

    def convert_timestamps2(row):
        mili = row['start_time']
        ts = datetime.datetime.fromtimestamp(mili).strftime('%Y-%m-%d %H:%M:%S')
        return ts

    def convert_timestamps3(row):
        mili = row['end_time']
        ts = datetime.datetime.fromtimestamp(mili).strftime('%Y-%m-%d %H:%M:%S')
        return ts

    df_peloton_final_stg['fixed_created_at'] = df_peloton_final_stg.apply(lambda row: convert_timestamps(row), axis=1)
    df_peloton_final_stg['fixed_start_time'] = df_peloton_final_stg.apply(lambda row: convert_timestamps2(row), axis=1)
    df_peloton_final_stg['fixed_end_time'] = df_peloton_final_stg.apply(lambda row: convert_timestamps3(row), axis=1)
    #df_peloton_final_stg[['ride.length']]



    return(df_peloton_final_stg,"Successfully got data! Let's take a look at your year!")


@app.callback(
    Output("modal-centered", "is_open"),
    [Input("open-centered", "n_clicks"), Input("close-centered", "n_clicks")],
    [State("modal-centered", "is_open")])

def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    [Output("confirmation_message", "children"),Output("total_rides","children"),Output("total_calories","children"),Output("fave_workout","children"),Output("loading-output", "children"),Output("workout_pie","figure")],
    [Input("example-button", "n_clicks"),Input("input", "value"),Input("password", "value")]
)
def on_button_click(n, value1, value2):
    if n is None:
        return no_update
    else:
        total_rides_message = get_total_rides(user_data)
        total_cals_message = get_total_calories(user_data)
        fave_message = get_fave_workout(user_data)
        pie = make_pie(user_data)
        return('Year has been generated! Check out your Peloton Year In Review using the tabs.', total_rides_message, total_cals_message,fave_message,"",pie)

def get_total_rides(data):
    total_rides = len(data)
    total_rides_message = "You rode " + str(total_rides) + " rides this year, you were on FIRE!"
    return total_rides_message

def get_total_calories(data):
    total_cals = data['Calories'].sum()
    total_cals_message = "You burned " + str(total_cals) + " calories in 2020."
    return total_cals_message

def get_fave_workout(data):
    fave = data['workout_type'].value_counts().idxmax()
    fave_message = "Your favorite workout type was " + str(fave) + ". Good choice :-)"
    return fave_message

def make_pie(data):
    fig = px.pie(data,values=data['fitness_discipline'].value_counts(), names=data.fitness_discipline.unique(), color_discrete_sequence=px.colors.sequential.RdBu)
    fig.update_traces(textposition='inside', textinfo='label')
    fig.update_layout(showlegend=False,paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)')
    fig.update_layout(
    font_color="white",
    title_font_color="white")
    #303030
    most = data['fitness_discipline'].value_counts().idxmax()
    most_message = "sensing a " +str(most)+ " buff over here....."
    fig.add_annotation(x=.5, y=-.2,
            text=str("sensing a "+ str(most)+ " buff over here....."),
            showarrow=False,font=dict(size=16))
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)