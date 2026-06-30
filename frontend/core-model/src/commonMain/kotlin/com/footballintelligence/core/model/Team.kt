package com.footballintelligence.core.model

/** A Premier League team. */
data class Team(val name: String)

/** Premier League 2023/24 teams used in the training dataset. */
val PREMIER_LEAGUE_TEAMS: List<Team> = listOf(
    Team("Arsenal"),
    Team("Aston Villa"),
    Team("Bournemouth"),
    Team("Brentford"),
    Team("Brighton"),
    Team("Burnley"),
    Team("Chelsea"),
    Team("Crystal Palace"),
    Team("Everton"),
    Team("Fulham"),
    Team("Liverpool"),
    Team("Luton"),
    Team("Man City"),
    Team("Man United"),
    Team("Newcastle"),
    Team("Nottm Forest"),
    Team("Sheffield United"),
    Team("Tottenham"),
    Team("West Ham"),
    Team("Wolves"),
)

/**
 * Default neutral feature values used when submitting a prediction.
 * These represent average/equal strength for both teams — a known
 * limitation for a demo app that does not pre-compute live features.
 */
fun buildNeutralFeatures(): Map<String, Double> = mapOf(
    "home_elo" to 1500.0,
    "away_elo" to 1500.0,
    "elo_diff" to 0.0,
    "home_form_wins_last5" to 0.4,
    "away_form_wins_last5" to 0.4,
    "home_form_wins_last10" to 0.4,
    "away_form_wins_last10" to 0.4,
    "home_form_pts_last5" to 1.5,
    "away_form_pts_last5" to 1.5,
    "home_form_pts_last10" to 1.5,
    "away_form_pts_last10" to 1.5,
    "home_goals_scored_mean_last5" to 1.3,
    "away_goals_scored_mean_last5" to 1.1,
    "home_goals_scored_mean_last10" to 1.3,
    "away_goals_scored_mean_last10" to 1.1,
    "home_goals_conceded_mean_last5" to 1.1,
    "away_goals_conceded_mean_last5" to 1.3,
    "home_goals_conceded_mean_last10" to 1.1,
    "away_goals_conceded_mean_last10" to 1.3,
    "home_goal_diff_mean_last5" to 0.2,
    "away_goal_diff_mean_last5" to -0.2,
    "home_goal_diff_mean_last10" to 0.2,
    "away_goal_diff_mean_last10" to -0.2,
    "home_win_pct" to 0.45,
    "home_ppg" to 1.7,
    "away_win_pct" to 0.30,
    "away_ppg" to 1.1,
    "home_rest_days" to 7.0,
    "away_rest_days" to 7.0,
    "h2h_matches" to 10.0,
    "h2h_home_wins" to 4.0,
    "h2h_draws" to 3.0,
    "h2h_away_wins" to 3.0,
    "home_position" to 10.0,
    "home_points" to 38.0,
    "home_matches_played" to 19.0,
    "away_position" to 10.0,
    "away_points" to 38.0,
    "away_matches_played" to 19.0,
    "home_sos_mean" to 1500.0,
    "away_sos_mean" to 1500.0,
    "home_sos_recent" to 1500.0,
    "away_sos_recent" to 1500.0,
)
