rm(list = ls())
#devtools::install_github("lgellis/pelotonR") # might be useful but not now
#devtools::install_github("bweiher/pelotonR") # better
#install.packages("ggpubr")

# packages
library("pelotonR")
library(tidyverse)
library(lubridate)
library(data.table)
library(ggpubr)

#set environment variables
Sys.setenv(PELOTON_LOGIN = "")
Sys.setenv(PELOTON_PASSWORD = "")

#authorize
peloton_auth()

#get personal info
me <- get_my_info() # peloton_api("api/me")
user_id <- me$id
num_workouts <- 100 #set to max number of workouts you want to retrieve
joins <- ""

    #pull in all workouts
    workouts <- peloton_api(glue::glue("/api/user/{user_id}/workouts?{joins}&limit={num_workouts}&page=0"))
    n_workouts <- length(workouts$content$data)
    
    
    #grab a couple old rides and your current ride to calculate things without errors
    all_cycle_workouts <- tibble()
    if (n_workouts > 0) {
      #for(i in c(2:n_workouts)) # for total stats
      for(i in c(2:50)) { # for live stats
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
      if(temp_workouts$fitness_discipline == "cycling") {
        cycling_workout <- temp_workouts %>% 
          mutate(end_time = as.character(end_time))
        all_cycle_workouts <- rbindlist(list(all_cycle_workouts, cycling_workout), use.names=TRUE,
                                        fill = TRUE)
        
      }
    }
    
    #get all workout ids
    workout_ids <- all_cycle_workouts$id
    
    #get performance stats for each workout
    keep <- tibble()
    for(i in c(1:length(workout_ids))) {
      message(i)
      test <- get_perfomance_graphs(workout_ids[i])
      keep <- rbindlist(list(keep, test), use.names = TRUE, fill = TRUE)
    }
    
    #extract averages
    average_summaries <- keep %>% select(id, average_summaries) %>% unnest(cols = c(average_summaries)) %>% 
      mutate(display_name = sapply(average_summaries,'[[',1),
             display_unit = sapply(average_summaries,'[[',2),
             value = sapply(average_summaries,'[[',3)) %>% 
      select(-average_summaries) %>% 
      pivot_wider(names_from = display_name, values_from = c(value, display_unit))
    
    #extract totals summaries
    totals_summaries <- keep %>% select(id, summaries) %>% unnest(cols = c(summaries)) %>% 
      mutate(display_name = sapply(summaries,'[[',1),
             display_unit = sapply(summaries,'[[',2),
             value = sapply(summaries,'[[',3)) %>% 
      select(-summaries) %>% 
      pivot_wider(names_from = display_name, values_from = c(value, display_unit))
    
    # Adding weekly summaries compared to previous week -----------------------
    
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
                              if_else(week_sum_stats[2,"WOW_workout_diff"] == 1 | week_sum_stats[2,"WOW_workout_diff"] == -1, "workout this week.", "workouts this week."))
    
    total_output_diff <- week_sum_stats %>% filter(week_num == isoweek(today())) %>% pull(WOW_total_output)
    total_cals_diff <- week_sum_stats %>% filter(week_num == isoweek(today())) %>% pull(WOW_total_cals)
    total_distance_diff <- week_sum_stats %>% filter(week_num == isoweek(today())) %>% pull(WOW_total_distance)
    avg_output_diff <- week_sum_stats %>% filter(week_num == isoweek(today())) %>% pull(WOW_avg_output)
    
    