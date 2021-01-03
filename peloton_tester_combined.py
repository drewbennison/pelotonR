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


#user_data = pd.read_csv('drewdata.csv')

external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

# assume you have a "long-form" data frame

tab1_content = dbc.Card(
    dbc.CardBody(
        [
        dbc.Button("Enter Account Info", id="open-centered"),
        dbc.Modal(
            [
                dbc.ModalHeader("Enter your Information Below"),
                dbc.ModalBody(html.Div([
                    dbc.Input(id="input", placeholder="username...", type="text"),
                    html.Br(),
                    dbc.Input(id="password", placeholder="password...", type="text")

                ]
            )),
                dbc.ModalFooter(
                    dbc.Button(
                        "Submit", id="close-centered", className="ml-auto"
                    )
                ),
            ],
            id="modal-centered",
            centered=True,
        ),
    html.Div(html.P(id="message")),
    html.Div(html.P(id="password_viewer")),
    html.Div(dbc.Button("Calculate My Year", id="example-button", className="mr-2")),
    dbc.Spinner(html.Div(id="loading-output")),
    html.Div(html.P(id="confirmation_message")),
    ]),
    className="mt-3")

tab2_content = dbc.Card(
    dbc.CardBody([
    html.Div(html.H1(id="Title")),
        html.Br(),
         dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Br(),
                    html.Div(html.H4(id="total_rides")),
                    html.Br(),
                    html.Div(html.H4(id="total_calories")),
                    html.Br(),
                    html.Div(html.H4(id="fave_workout"))])),
            dbc.Col(dbc.Card(dcc.Graph(id="workout_pie")))
            ])
         ])
    )



app.layout = html.Div(children=[
    html.H1(children='PELETON YEAR IN REVIEW'),
    html.Div(
    [
    dbc.Tabs(
                [
                    dbc.Tab(tab1_content,label="Get Started", tab_id="tab-1"),
                    dbc.Tab(tab2_content,label="Reviewing 2020", tab_id="tab-2"),
                ],
                id="card-tabs",
                card=True,
                active_tab="tab-1",
            )
    ])])

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
    df_my_id = pd.json_normalize(apidata)
    df_my_id_clean = df_my_id[['id']]
    my_id = (df_my_id_clean.iloc[0]['id'])
 
    url = 'https://api.onepeloton.com/api/user/{}/workouts?joins=ride,ride.instructor&limit=250&page=0'.format(my_id)
    response = s.get(url)
    data = s.get(url).json()
    df_workouts_raw = pd.json_normalize(data['data'])

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

    #filter out year for 2020 only
    df_peloton_final_stg = df_peloton_final_stg[(df_peloton_final_stg['created_at'])>=1577836800 & (df_peloton_final_stg['created_at']<1609459200)]  

    user = "WOW! You killed it this year, {}... let's look closer at what you achieved.".format(user)

    return(df_peloton_final_stg,"Successfully got data! Let's take a look at your year!", user)


@app.callback(
    Output("modal-centered", "is_open"),
    [Input("open-centered", "n_clicks"), Input("close-centered", "n_clicks")],
    [State("modal-centered", "is_open")])

def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    [Output("confirmation_message", "children"), Output("Title", "children"), Output("total_rides","children"),Output("total_calories","children"),Output("fave_workout","children"),Output("loading-output", "children"),Output("workout_pie","figure")],
    [Input("example-button", "n_clicks"),Input("input", "value"),Input("password", "value")]
)
def on_button_click(n, value1, value2):
    if n is None:
        return no_update
    else:
        user_data, user_data_message, user_welcome = getdata(value1, value2)

        total_workouts_message, fave_message = numWorkouts(user_data)
        total_cals_message = get_total_calories(user_data)
        pie = make_pie(user_data)
        return('Year has been generated! Check out your Peloton Year In Review using the tabs.',
            user_welcome, total_workouts_message, total_cals_message,fave_message,"",pie)

def numWorkouts(dt):
    #total number of workouts
    n = len(dt)

    #most popular categories
    dt2 = dt[['created_at', 'fitness_discipline']].groupby(['fitness_discipline']).agg({'fitness_discipline' :['count']})
    dt2.columns = dt2.columns.droplevel(0)
    dt2.reset_index(inplace=True)

    if len(dt2)>2:
        top = dt2.nlargest(3, 'count')
        top = top['fitness_discipline'].tolist()
        top_message = "In 2020, you diversified your workouts. Your most popular categories were {}, {}, and {}. Great choices!".format(top[0], top[1], top[2])
    elif len(dt2)==2:
        top = dt2.nlargest(2, 'count')
        top = top['fitness_discipline'].tolist()
        top_message = "In 2020, you diversified your workouts. Your most popular categories were {} and {}. Great choices!".format(top[0], top[1])
    else:
        top = dt2.nlargest(1, 'count')
        top = top['fitness_discipline'].tolist()
        top_message = "In 2020, your most popular category was {}. Good choice!".format(top[0])

    n = "You had a great year of working out, altogether you completed " + str(n) + " workouts, you were on FIRE!"



    return n, top_message

def get_total_calories(data):
    total_cals = data['Calories'].sum()
    total_cals_message = "You burned " + str(round(total_cals)) + " calories in 2020."
    return total_cals_message

def make_pie(data):
    fig = px.pie(data, title="Workout Types for 2020",template='seaborn',values=data['fitness_discipline'].value_counts(), names=data.fitness_discipline.unique())
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)