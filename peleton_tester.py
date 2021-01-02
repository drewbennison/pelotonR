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
    html.Div(html.P(id="opening_message")),
    html.Div(dbc.Button("Calculate My Year", id="example-button", className="mr-2")),
    #html.Div(html.P(id="stats"))
    ]),
    className="mt-3")


tab2_content = dbc.Card(
    dbc.CardBody(
        [
    html.Div(html.H1(id="user_message")),
    html.Div(html.P(id="num_workouts")),
    html.Div(html.P(id="pop_categories")),
    ]),
    className="mt-3")


app.layout = html.Div(children=[
    html.H1(children='PELETON YEAR IN REVIEW'),
    html.Div(
    [
    dbc.Tabs(
                [
                    dbc.Tab(tab1_content,label="Account Info", tab_id="tab-1"),
                    dbc.Tab(tab2_content, label="Workout Details", tab_id="tab-2"),
                ],
                id="card-tabs",
                card=True,
                active_tab="tab-1",
            )
    ])])

#function that returns data
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
    #df_my_id = json_normalize(apidata, 'id', ['id'])
    #df_my_id_clean = df_my_id.iloc[0]
    #my_id = (df_my_id_clean.drop([0])).values.tolist()

    df_my_id = pd.json_normalize(apidata)
    #print(df_my_id)
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

    #filter out year for 2020 only
    df_peloton_final_stg = df_peloton_final_stg[(df_peloton_final_stg['created_at'])>=1577836800 & (df_peloton_final_stg['created_at']<1609459200)]  


    return(df_peloton_final_stg,"Successfully got data... let's take a look at your year! Head to the next tab to get started", user)


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
        top_message = "In 2020, you diversified your workouts. Your most popular categories were {}, {}, and {}!".format(top[0], top[1], top[2])
    elif len(dt2)==2:
        top = dt2.nlargest(2, 'count')
        top = top['fitness_discipline'].tolist()
        top_message = "In 2020, you diversified your workouts. Your most popular categories were {} and {}!".format(top[0], top[1])
    else:
        top = dt2.nlargest(1, 'count')
        top = top['fitness_discipline'].tolist()
        top_message = "In 2020, your most popular category was {}!".format(top[0])

    n = "You had a great year of working out, altogether you completed " + str(n) + " Peloton workouts, nice job!"



    return n, top_message

@app.callback(
    Output("modal-centered", "is_open"),
    [Input("open-centered", "n_clicks"), Input("close-centered", "n_clicks")],
    [State("modal-centered", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(Output("message", "children"), [Input("input", "value")])
def output_text(value):
    return("")

@app.callback(Output("password_viewer", "children"), [Input("password", "value")])
def output_text(value):
    return("")

@app.callback(
    [Output("opening_message", "children"),
    Output("user_message", "children"),
    Output("num_workouts", "children"),
    Output("pop_categories", "children")],
    [Input("example-button", "n_clicks"),Input("input", "value"),Input("password", "value")]
)
def on_button_click(n, value1, value2):
    if n is None:
        return("Click 'Calculate My Year' after inputting account info: we'll let you know when we get your data, it may take a few minutes!", "Unknown User", "No data yet.", "No data yet")
    else:
        user_data, message, user = getdata(value1, value2)

        number_workouts, popular_categories = numWorkouts(user_data)

        user = "Welcome to your Peloton Wrapped, " + user + "."


        return(message, user, number_workouts, popular_categories)

if __name__ == '__main__':
    app.run_server(debug=True)