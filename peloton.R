#devtools::install_github("lgellis/pelotonR")
#devtools::install_github("bweiher/pelotonR") # better

library("pelotonR")
library(tidyverse)
library(lubridate)
library(data.table)
library(ggpubr)

#set environment variables
Sys.setenv(PELOTON_LOGIN = "dbennison")
Sys.setenv(PELOTON_PASSWORD = "Maddie11!")

#authorize
peloton_auth()

#get personal info
me <- get_my_info() # peloton_api("api/me")
user_id <- me$id
num_workouts <- 100
joins <- ""


length_workout_seconds <- 30*60

for(i in seq(1, length_workout_seconds+60, 30)) {

workouts <- peloton_api(glue::glue("/api/user/{user_id}/workouts?{joins}&limit={num_workouts}&page=0"))
n_workouts <- length(workouts$content$data)


all_cycle_workouts <- tibble()
if (n_workouts > 0) {
  #for(i in c(2:n_workouts)) # for total stats
  for(i in c(2:5)) { # for live stats
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
  cycling_workout <- temp_workouts
  all_cycle_workouts <- rbindlist(list(all_cycle_workouts, cycling_workout), use.names=TRUE,
                                  fill = TRUE)
  
  }
}

workout_ids <- all_cycle_workouts$id

#get performance stats
keep <- tibble()
for(i in c(1:length(workout_ids))) {
  message(i)
  test <- get_perfomance_graphs(workout_ids[i])
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


#get current ride id
current_ride_id <- all_cycle_workouts %>% 
  filter(is.na(end_time)) %>% 
  select(id) %>% pull()

g1 <- masterdata2 %>% 
  filter(id == current_ride_id) %>% 
  ggplot(aes(x=minutes, y=Cadence)) +
  geom_line()

g2 <-  masterdata2 %>% 
  filter(id == current_ride_id) %>% 
  ggplot(aes(x=minutes, y=Output)) +
  geom_line()

g3 <-  masterdata2 %>% 
  filter(id == current_ride_id) %>% 
  ggplot(aes(x=minutes, y=Resistance)) +
  geom_line() +
  ylim(0,100)

g4 <-  masterdata2 %>% 
  filter(id == current_ride_id) %>% 
  ggplot(aes(x=minutes, y=Speed)) +
  geom_line()

figure <- ggarrange(g1, g2, g3, g4,
                    labels = c("Cadence", "Output", "Resistance", "Speed"),
                    ncol = 2, nrow = 2)

show(figure)
Sys.sleep(30)

}

masterdata2 %>% 
  filter(id == "83bb7bcc42094d91a99c0a08c4159091") %>% 
  ggplot(aes(x=Cadence, y=Output)) +
  geom_line()
  
  