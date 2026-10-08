package com.footballintelligence.core.navigation

/** All navigable screens in the app. */
sealed class Screen(val route: String) {
    data object Home : Screen("home")
    data object Prediction : Screen("prediction")
    data object PredictionResult : Screen("prediction_result")
    data object ExplainPrediction : Screen("explain_prediction")
    data object Assistant : Screen("assistant")
    data object MyTeam : Screen("my_team")

    /** The projected league table behind My Team's season outlook. */
    data object SeasonTable : Screen("season_table")

    /** First-launch favourite team picker; a future login screen goes before it. */
    data object Onboarding : Screen("onboarding")

    /** The favourite team picker opened from Settings. */
    data object ChangeTeam : Screen("change_team")
    data object ModelInfo : Screen("model_info")
    data object Settings : Screen("settings")
    data object About : Screen("about")
}
