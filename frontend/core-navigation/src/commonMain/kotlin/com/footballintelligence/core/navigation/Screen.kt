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

    /** Sign in or redeem an invite (ADR 022); shown whenever there is no session. */
    data object Auth : Screen("auth")

    /** Checks the signed-in user and shows the notice if it still needs accepting. */
    data object Consent : Screen("consent")

    /** First-launch favourite team picker, after sign-in. */
    data object Onboarding : Screen("onboarding")

    /** The favourite team picker opened from Settings. */
    data object ChangeTeam : Screen("change_team")
    data object ModelInfo : Screen("model_info")
    data object Settings : Screen("settings")
    data object About : Screen("about")
}
