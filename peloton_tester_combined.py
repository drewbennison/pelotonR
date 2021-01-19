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

#CHANGED THEME TO DARK ******
external_stylesheets = [dbc.themes.DARKLY]
app = dash.Dash(__name__,external_stylesheets=external_stylesheets)
app.title = 'Peloton Year In Review' 

# assume you have a "long-form" data frame

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


"""tab2_content = dbc.Card(
    dbc.CardBody([
    html.Div(html.H2(id="Title")),
        html.Br(),
         dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Br(),
                    html.Div(html.H4(id="total_workouts")),
                    html.Br(),
                    html.Div(html.H4(id="total_calories")),
                    html.Br(),
                    html.Div(html.H4(id="fave_workout")),
                    html.Br(),
                    html.Div(html.H4(id="favorite_instructors"))], outline=True), width=7),
            dbc.Col(dbc.Card([html.Br(),html.H3("Your Workout Types of 2020"),dcc.Graph(id="workout_pie")]),width=5)
            ])
         ])
    )
"""

tab2_content = html.Div([
    dbc.Row(dbc.Card(html.H3(id="Title",style={'padding':'20px'}),style={"width": "90rem"},color='dark',outline=True)),
    html.Br(),
    dbc.Row([
        dbc.Col([dbc.Card(dbc.ListGroup(
        [
            dbc.ListGroupItem(html.H4(id="total_workouts",style={'padding':'20px'})),
            dbc.ListGroupItem(html.H4(id="total_calories",style={'padding':'20px'})),
            dbc.ListGroupItem(html.H4(id="fave_workout",style={'padding':'20px'})),
            dbc.ListGroupItem(html.H4(id="favorite_instructors",style={'padding':'20px'})),
        ], flush=True),color="secondary")]),
        dbc.Col([dbc.Card([html.Br(),html.H3("Your Workout Types of 2020",style={"text-align":"center"}),dcc.Graph(id="workout_pie")], color="secondary", outline=True)]),
        ])
    ],style={'padding':'40px',"background-image":'url("https://wallpapercave.com/wp/wp4047946.jpg")'})


tab3_content = dbc.Card(
    dbc.CardBody([
    html.Div(html.H2(id="Cycling Stats")),
        html.Br(),
         dbc.Row([
            dbc.Col(
                dbc.Card([
                    html.Br(),
                    html.Div(html.H4(id="cycling-total-rides")),
                    html.Br(),
                    html.Div(html.H4(id="cycling-total-distance")),
                    html.Br(),
                    html.Div(html.H4(id="cycling-total-output")),
                    ], outline=True), width=7),
            ])
         ])
    )


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
            dbc.Tab(tab3_content,label="Cycling Stats",tab_id="tab-3")],
            id="card-tabs",
            card=False,
            active_tab="tab-1")]
        )]
    )

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
    df_my_id = json_normalize(apidata)
    df_my_id_clean = df_my_id[['id']]
    my_id = (df_my_id_clean.iloc[0]['id'])
 
    url = 'https://api.onepeloton.com/api/user/{}/workouts?joins=ride,ride.instructor&limit=1000&page=0'.format(my_id)
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
        #can we get away with an every_n that is very large?
         response2 = s.get('https://api.onepeloton.com/api/workout/{}/performance_graph?every_n=1800'.format(workout_id))
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
    df_peloton_final_stg['workout_length'] = df_peloton_final_stg['end_time'] - df_peloton_final_stg['start_time']
    #df_peloton_final_stg[['ride.length']]

    #filter out year for 2020 only - I'm not sure if this works
    df_peloton_final_stg = df_peloton_final_stg[df_peloton_final_stg.created_at>=1577836800]
    df_peloton_final_stg = df_peloton_final_stg[df_peloton_final_stg.created_at<1609477200]

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
    [Output("confirmation_message", "children"), Output("Title", "children"), Output("total_workouts","children"),
    Output("total_calories","children"),Output("fave_workout","children"),Output("loading-output", "children"),Output("workout_pie","figure"),
    Output("favorite_instructors", "children"), Output("cycling-total-rides", "children"), Output("cycling-total-distance", "children"),
    Output("cycling-total-output", "children")],
    [Input("example-button", "n_clicks"),Input("input", "value"),Input("password", "value")]
)
def on_button_click(n, value1, value2):
    if n is None:
        return no_update
    else:
        user_data, user_data_message, user_welcome = getdata(value1, value2)

        rides_message, total_distance, total_output = get_cycling_stats(user_data)


        total_workouts_message, fave_message = numWorkouts(user_data)
        total_cals_message = get_total_calories(user_data)
        pie = make_pie(user_data)
        combined_message = favoriteInstructor(user_data)
        return('Year has been generated! Check out your Peloton Year In Review using the tabs.',
            user_welcome, total_workouts_message, total_cals_message,fave_message,"",pie,
            combined_message, rides_message, total_distance, total_output)

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


def favoriteInstructor(dt):
    #most popular categories
    dt2 = dt[['created_at', 'ride.instructor.name']].groupby(['ride.instructor.name']).agg({'ride.instructor.name' :['count']})
    dt2.columns = dt2.columns.droplevel(0)
    dt2.reset_index(inplace=True)

    n = len(dt2)

    if len(dt2)>2:
        top = dt2.nlargest(3, 'count')
        top = top['ride.instructor.name'].tolist()
        top_message = "Your go to instructors were {}, {}, and {}.".format(top[0], top[1], top[2])
        n = "You completed workouts with {} different instructors this year.".format(n)
    elif len(dt2)==2:
        top = dt2.nlargest(2, 'count')
        top = top['ride.instructor.name'].tolist()
        top_message = "Your go to instructors were {} and {}.".format(top[0], top[1])
        n = "You completed workouts with {} different instructors this year.".format(n)
    else:
        top = dt2.nlargest(1, 'count')
        top = top['ride.instructor.name'].tolist()
        top_message = "But if something works, why change, right? Your favorite instructor (and only instructor) was {}.".format(top[0])
        n = "You completed workouts with only one instructor this year...I'm guessing you're a fan?"

    combined_message = n + " " + top_message
    return combined_message


def get_total_calories(data):
    total_cals = data['Calories'].sum()
    total_time = data['workout_length'].sum()
    total_time = round(total_time/60)
    total_cals_message = "You worked out for " + str(total_time) + " minutes this year (that's " + str(round((total_time/60/24),2)) + " days) and along the way you burned " + str(round(total_cals)) + " calories in 2020."
    return total_cals_message

def make_pie(data):
    #most popular categories
    dt2 = data[['created_at', 'fitness_discipline']].groupby(['fitness_discipline']).agg({'fitness_discipline' :['count']})
    dt2.columns = dt2.columns.droplevel(0)
    dt2.reset_index(inplace=True)

    fig = px.pie(dt2, title="Workout Types for 2020",template='seaborn',values='count', names='fitness_discipline',color_discrete_sequence=px.colors.sequential.RdBu)

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


def get_cycling_stats(data):
    cycling_workouts = data[data.fitness_discipline == "cycling"]

    if len(cycling_workouts) == 0:
        #no cycling workouts
        return "Looks like you didn't complete any rides this year...no problem!", ""

    else:
        rides_message = "You completed {} cycling workouts this year...".format(len(cycling_workouts))

        total_output = round(data['Total Output'].sum())
        total_iphone_charges = round((total_output*.0002777777/2), 1)

        total_distance = "...rode for {} miles...".format(str( round(data['Distance'].sum(),1)))
        total_output = "...had a total output of {} Kilojoules  (that's enough to charge your iphone {} times)".format(str(total_output), total_iphone_charges)


        return rides_message, total_distance, total_output

if __name__ == '__main__':
    app.run_server(debug=True)