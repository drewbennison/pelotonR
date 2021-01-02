#
# This is a Shiny web application. You can run the application by clicking
# the 'Run App' button above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

library(shiny)
# packages
library("pelotonR")
library(tidyverse)
library(lubridate)
library(data.table)
library(ggpubr)

# Define UI for application that draws a histogram
ui <- fluidPage(

    # Application title
    titlePanel("Peloton Live Tracker"),
    fluidRow(
        column(textInput("username", "Peloton Username"), width = 4),
        column(passwordInput("pw", "Peloton Password"), width = 4),
        column(textInput("time", "How long is your workout (minutes)?"), width = 3),
        column(actionButton(inputId = "SubmitButton",label = "Start"), width = 1, 
               style = "display:flex;padding-top:25px;justify-content:center;align-items:center;"),
        style = "background-color:#C34539;color:white;"
    ),

    # Sidebar with a slider input for number of bins 
    fluidRow(
        column(width = 12,
        # Show a plot of the generated distribution
        tabsetPanel(type = "tabs",
                    tabPanel("Live Stats", plotOutput("distPlot")),
                    tabPanel("Post Ride Analysis",
                             fluidRow(
                                 column(12, uiOutput("welcome_message"))
                             ),
                             fluidRow(h3("Your weekly stats", style = "padding-left:20px;")),
                             fluidRow(
                                 column(3, uiOutput("wow_total_output")),
                                 column(3, uiOutput("wow_total_cals")),
                                 column(3, uiOutput("wow_total_distance")),
                                 column(3, uiOutput("wow_avg_output"))),
                             fluidRow(
                                 column(3, h4("Total Output")),
                                 column(3, h4("Total Calories")),
                                 column(3, h4("Total Distance")),
                                 column(3, h4("Average Output"))
                             ),
                             fluidRow(
                             plotOutput("summary")
                             )
                             )
                    )
        #mainPanel(
        #   plotOutput("distPlot")
        #)
    )
)
)

# Define server logic required to draw a histogram
server <- function(input, output) {
        
        autoInvalidate <- reactiveTimer(30000)
        
        observeEvent(input$SubmitButton,
                 {
                     if(input$username!=""&&input$pw!="")
                         
                     {
                         peloton_auth(login = input$username, password = input$pw)
                         me <- get_my_info() # peloton_api("api/me")
                         user_id <- me$id
                         
                         output$distPlot <-  renderPlot({
                             autoInvalidate()
                             workouts <- peloton_api(glue::glue("/api/user/{user_id}/workouts?&limit=100&page=0"))
                             n_workouts <- length(workouts$content$data)
                             
                             all_cycle_workouts <- tibble()
                             if (n_workouts > 0) {
                                 #for(i in c(2:n_workouts)) # for total stats
                                 for(i in c(2:10)) { # for live stats
                                     temp_workouts <- parse_list_to_df(workouts$content$data[[i]])
                                     if (temp_workouts$fitness_discipline == "cycling") {
                                         cycling_workout <- temp_workouts %>% 
                                             mutate(end_time = as.character(end_time))
                                         all_cycle_workouts <- rbindlist(list(all_cycle_workouts, cycling_workout), use.names=TRUE,
                                                                         fill = TRUE)
                                         
                                     }
                                 }
                                 #get current workout
                                 temp_workouts <- parse_list_to_df(workouts$content$data[[1]])
                                 if(temp_workouts$fitness_discipline == "cycling" && temp_workouts$has_pedaling_metrics==TRUE) {
                                     cycling_workout <- temp_workouts %>% mutate(end_time = as.character(end_time))
                                     all_cycle_workouts <- rbindlist(list(all_cycle_workouts, cycling_workout), use.names=TRUE,
                                                                     fill = TRUE)
                                     
                                 } else{ #if current ride is not cycling
                                     x <- ggplot() + annotate("text", x = input$time, y = 100, label = "NO LIVE RIDE") +
                                         labs(x="", y="")
                                     x
                                 }
                             }
                             
                             #check if there is a current workout
                             is_there_current_workout <- all_cycle_workouts %>% filter(status != "COMPLETE")
                             
                             if(nrow(is_there_current_workout) == 0) {
                                 x <- ggplot() + annotate("text", x = input$time, y = 10, label = "NO LIVE RIDE") +
                                     labs(x="", y="")
                                 x
                             } else {
                             
                             workout_ids <- all_cycle_workouts$id
                             
                             #get performance stats for each workout
                             keep <- tibble()
                             for(i in c(1:length(workout_ids))) {
                                 message(i)
                                 test <- get_perfomance_graphs(workout_ids[i], every_n = 1)
                                 keep <- rbindlist(list(keep, test), use.names = TRUE, fill = TRUE)
                             }
                             
                             #extract pedal seconds
                             pedal_seconds <- keep %>% select(id, seconds_since_pedaling_start)
                             pedal_seconds <- pedal_seconds %>% unnest(cols=c(seconds_since_pedaling_start))
                             
                             #extract averages
                             average_summaries <- keep %>% select(id, average_summaries) %>% unnest(cols = c(average_summaries)) %>% 
                                 mutate(display_name = sapply(average_summaries,'[[',1),
                                        display_unit = sapply(average_summaries,'[[',2),
                                        value = sapply(average_summaries,'[[',3)) %>% 
                                 select(-average_summaries) %>% 
                                 pivot_wider(names_from = display_name, values_from = c(value, display_unit))
                             
                             #extract summaries
                             totals_summaries <- keep %>% select(id, summaries) %>% unnest(cols = c(summaries)) %>% 
                                 mutate(display_name = sapply(summaries,'[[',1),
                                        display_unit = sapply(summaries,'[[',2),
                                        value = sapply(summaries,'[[',3)) %>% 
                                 select(-summaries) %>% 
                                 pivot_wider(names_from = display_name, values_from = c(value, display_unit))
                             
                             #extract metrics
                             metrics_summaries <- keep %>% select(id, metrics) %>% unnest(cols = c(metrics)) %>% 
                                 mutate(display_name = sapply(metrics,'[[',1),
                                        second_list = sapply(metrics,'[[',5)) %>% 
                                 rename(id2 = id) %>% 
                                 select(-metrics) %>% 
                                 unnest(cols = c(second_list)) %>% 
                                 group_by(id2, display_name) %>% 
                                 mutate(row_marker = row_number()) %>% 
                                 pivot_wider(names_from = c(display_name) ,values_from = c(second_list))
                             
                             #merge seconds with instantaneous stats
                             master_data <- cbind(pedal_seconds, metrics_summaries)
                             
                             #bring in average summaries and totals summaries
                             masterdata2 <- master_data %>% left_join(average_summaries, by="id") %>% 
                                 left_join(totals_summaries)
                             
                             #done
                             masterdata2 <- masterdata2 %>% unnest(cols = c(seconds_since_pedaling_start, Output, Cadence, Resistance, Speed))
                             masterdata2 <- masterdata2 %>% mutate(minutes = seconds_since_pedaling_start/60)
                             
                             #add cumulative total output
                             masterdata2 <- masterdata2 %>% 
                                 group_by(id) %>% 
                                 mutate(cum_average_output = cummean(Output)*minutes*60/1000)
                             
                             #get current ride id of live ride
                             current_ride_id <- all_cycle_workouts %>% 
                                 filter(is.na(end_time)) %>% 
                                 select(id) %>% pull()
                             
                             #make performance plots
                             g1 <- masterdata2 %>% 
                                 filter(id == current_ride_id) %>% 
                                 ggplot(aes(x=minutes, y=Cadence)) +
                                 geom_line()
                             
                             
                             g2 <-  masterdata2 %>% 
                                 filter(id == current_ride_id) %>% 
                                 ggplot(aes(x=minutes, y=Output)) +
                                 geom_line() +
                                 geom_line(aes(x=minutes, y=cum_average_output), color="red")
                             
                             g3 <-  masterdata2 %>% 
                                 filter(id == current_ride_id) %>% 
                                 ggplot(aes(x=minutes, y=Resistance)) +
                                 geom_line() +
                                 ylim(0,100)
                             
                             g4 <-  masterdata2 %>% 
                                 filter(id == current_ride_id) %>% 
                                 ggplot(aes(x=minutes, y=Speed)) +
                                 geom_line()
                             
                             #arrange all plots together
                             figure <- ggarrange(g1, g2, g3, g4,
                                                 labels = c("Cadence", "Output", "Resistance", "Speed"),
                                                 ncol = 2, nrow = 2)
                             
                             figure
                             }
                         }) #end of live plot output
                         
                         # Rerun basic tables for post-ride analysis page
                         workouts <- peloton_api(glue::glue("/api/user/{user_id}/workouts?&limit=1000&page=0"))
                         n_workouts <- length(workouts$content$data)
                         
                         all_cycle_workouts <- tibble()
                         if (n_workouts > 0) {
                             for(i in c(1:n_workouts)) { # for all stats
                                 temp_workouts <- parse_list_to_df(workouts$content$data[[i]])
                                 if (temp_workouts$fitness_discipline == "cycling" && temp_workouts$status == "COMPLETE") {
                                     cycling_workout <- temp_workouts
                                     all_cycle_workouts <- rbindlist(list(all_cycle_workouts, cycling_workout), use.names=TRUE,
                                                                     fill = TRUE)
                                     
                                 }
                             }}
                         
                         workout_ids <- all_cycle_workouts$id
                         
                         #get performance stats for each workout
                         keep <- tibble()
                         for(i in c(1:length(workout_ids))) {
                             message(i)
                             test <- get_perfomance_graphs(workout_ids[i], every_n = 10)
                             if(is.na(test$seconds_since_pedaling_start)==FALSE) {
                                 keep <- rbindlist(list(keep, test), use.names = TRUE, fill = TRUE)
                             }
                         }
                         
                         #extract pedal seconds
                         pedal_seconds <- keep %>% select(id, seconds_since_pedaling_start)
                         pedal_seconds <- pedal_seconds %>% unnest(cols=c(seconds_since_pedaling_start))
                         
                         #extract averages
                         average_summaries <- keep %>% select(id, average_summaries) %>% unnest(cols = c(average_summaries)) %>% 
                             mutate(display_name = sapply(average_summaries,'[[',1),
                                    display_unit = sapply(average_summaries,'[[',2),
                                    value = sapply(average_summaries,'[[',3)) %>% 
                             select(-average_summaries) %>% 
                             pivot_wider(names_from = display_name, values_from = c(value, display_unit))
                         
                         #extract summaries
                         totals_summaries <- keep %>% select(id, summaries) %>% unnest(cols = c(summaries)) %>% 
                             mutate(display_name = sapply(summaries,'[[',1),
                                    display_unit = sapply(summaries,'[[',2),
                                    value = sapply(summaries,'[[',3)) %>% 
                             select(-summaries) %>% 
                             pivot_wider(names_from = display_name, values_from = c(value, display_unit))
                         
                         #extract metrics
                         metrics_summaries <- keep %>% select(id, metrics) %>% unnest(cols = c(metrics)) %>% 
                             mutate(display_name = sapply(metrics,'[[',1),
                                    second_list = sapply(metrics,'[[',5)) %>% 
                             rename(id2 = id) %>% 
                             select(-metrics) %>% 
                             unnest(cols = c(second_list)) %>% 
                             group_by(id2, display_name) %>% 
                             mutate(row_marker = row_number()) %>% 
                             pivot_wider(names_from = c(display_name) ,values_from = c(second_list))
                         
                         #post ride stats Plot
                         output$summary <- renderPlot({
                             
                             #merge seconds with instantaneous stats
                             master_data <- cbind(pedal_seconds, metrics_summaries)
                             
                             #bring in average summaries and totals summaries
                             masterdata2 <- master_data %>% left_join(average_summaries, by="id") %>% 
                                 left_join(totals_summaries)
                             
                             #done
                             masterdata2 <- masterdata2 %>% unnest(cols = c(seconds_since_pedaling_start, Output, Cadence, Resistance, Speed))
                             masterdata2 <- masterdata2 %>% mutate(minutes = seconds_since_pedaling_start/60)
                             
                             #add cumulative total output
                             masterdata2 <- masterdata2 %>% 
                                 group_by(id) %>% 
                                 mutate(cum_average_output = cummean(Output)*minutes*60/1000)
                             
                             
                             summary_1 <- masterdata2 %>% 
                                 left_join(all_cycle_workouts, by=c("id")) %>% 
                                 group_by(id, start_time, `value_Total Output`) %>% 
                                 arrange(-minutes) %>% 
                                 slice_head() %>% 
                                 mutate(created_at = as_date(created_at),
                                        output_per_minute = `value_Total Output` / minutes) %>% 
                                 filter(minutes>6) %>% 
                                 ggplot(aes(x=created_at, y=output_per_minute)) +
                                 geom_point() +
                                 geom_smooth(method = "lm", se=FALSE) +
                                 labs(x="Ride date", y="Output per minute",
                                      title = "Output over time")
                             
                             summary_2 <- masterdata2 %>% 
                                 left_join(all_cycle_workouts, by=c("id")) %>% 
                                 select(id, created_at) %>% 
                                 unique() %>% 
                                 mutate(created_at = as_date(created_at),
                                        day_of_week = lubridate::wday(created_at, label=TRUE)) %>% 
                                 group_by(day_of_week) %>% 
                                 count() %>% 
                                 ggplot(aes(x=day_of_week, y=n)) +
                                 geom_col() +
                                 labs(x="", y="Number of rides",
                                      title = "Most popular days to ride")
                                 
                             #arrange all plots together
                             figure <- ggarrange(summary_1, summary_2,
                                                 ncol = 2, nrow = 2)
                             
                             figure
                             

                         }) #end of summary stats plot
                         
                         # Welcome Message and WOW Stats -------------------------------------------
                         
                         # Create lookup of day of week and weekday number
                         weekday_nums <- 1:7
                         weekday_names <- c("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
                         
                         day_num_lookup <- tibble(weekday_names, weekday_nums)
                         
                         today_day_num <- day_num_lookup %>% filter(weekday_names == weekdays(today())) %>% pull(weekday_nums)
                         days_since_monday <- today_day_num - 1
                         
                         ### Get weekly stats vs. last week
                         joined_stats <- all_cycle_workouts %>% left_join(totals_summaries, by = "id")
                         joined_stats <- joined_stats %>% left_join(average_summaries, by = "id")
                         
                         # Add Week number to workouts using epiweek
                         joined_stats <- joined_stats %>% 
                             mutate(week_num = isoweek(start_time),
                                    start_date = as.Date(start_time))
                         
                         # Summarise by week, then calculate differences
                         week_sum_stats <- joined_stats %>% 
                             filter(week_num  %in% c(isoweek(today()), isoweek(today()-7))) %>% 
                             filter(dplyr::between(as.Date(start_time), today() - days_since_monday, today()) | 
                                        dplyr::between(as.Date(start_time), today() - 7 - days_since_monday, today() - 7)) %>% 
                             group_by(week_num) %>% 
                             summarise(total_weekly_output = sum(`value_Total Output`),
                                       total_weekly_calories = sum(value_Calories),
                                       total_weekly_distance = sum(value_Distance),
                                       avg_weekly_output = mean(`value_Avg Output`),
                                       workout_count = n()) %>% 
                             arrange(week_num) %>% 
                             mutate(WOW_total_output = scales::percent((total_weekly_output - lag(total_weekly_output, n = 1L)) / lag(total_weekly_output, n = 1L), accuracy = .1),
                                    WOW_total_cals = scales::percent((total_weekly_calories - lag(total_weekly_calories, n = 1L)) / lag(total_weekly_calories, n = 1L), accuracy = .1),
                                    WOW_total_distance = scales::percent((total_weekly_distance - lag(total_weekly_distance, n = 1L)) / lag(total_weekly_distance, n = 1L), accuracy = .1),
                                    WOW_avg_output = scales::percent((avg_weekly_output - lag(avg_weekly_output, n = 1L)) / lag(avg_weekly_output, n = 1L), accuracy = .1),
                                    WOW_workout_diff = workout_count - lag(workout_count))
                         
                         welcome_message <- paste0("Hi, ", if_else(is.na(me$first_name)==T, me$username, me$first_name),
                                                   ". You have done ", case_when(week_sum_stats[2,"WOW_workout_diff"] > 0 ~ paste0(week_sum_stats[2,"WOW_workout_diff"], " more "),
                                                                                 week_sum_stats[2,"WOW_workout_diff"] == 0 ~ paste0(" the same number of "),
                                                                                 week_sum_stats[2,"WOW_workout_diff"] < 0 ~ paste0(abs(week_sum_stats[2,"WOW_workout_diff"]), " less ")
                                                   ), 
                                                   if_else(week_sum_stats[2,"WOW_workout_diff"] == 1 | week_sum_stats[2,"WOW_workout_diff"] == -1, "workout this week compared to this time last week.", "workouts this week compared to this time last week."))
                         
                         output$welcome_message <- renderUI(h2(welcome_message))
                         
                         total_output_diff <- week_sum_stats %>% filter(week_num == isoweek(today())) %>% pull(WOW_total_output)
                         total_cals_diff <- week_sum_stats %>% filter(week_num == isoweek(today())) %>% pull(WOW_total_cals)
                         total_distance_diff <- week_sum_stats %>% filter(week_num == isoweek(today())) %>% pull(WOW_total_distance)
                         avg_output_diff <- week_sum_stats %>% filter(week_num == isoweek(today())) %>% pull(WOW_avg_output)
                         
                         output$wow_total_output <- renderUI(h3(total_output_diff, style = paste0("color:", if_else(total_output_diff > 0, "green;", "red;"))))
                         output$wow_total_distance <- renderUI(h3(total_distance_diff, style = paste0("color:", if_else(total_distance_diff > 0, "green;", "red;"))))
                         output$wow_total_cals <- renderUI(h3(total_cals_diff, style = paste0("color:", if_else(total_cals_diff > 0, "green;", "red;"))))
                         output$wow_avg_output <- renderUI(h3(avg_output_diff, style = paste0("color:", if_else(avg_output_diff > 0, "green;", "red;"))))
                        
                         
                         
                         
                     }
                 })



        

}

# Run the application 
shinyApp(ui = ui, server = server)
