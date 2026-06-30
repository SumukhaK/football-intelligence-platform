package com.footballintelligence.core.navigation

/** All navigable screens in the app. */
sealed class Screen(val route: String) {
    data object Home : Screen("home")
    data object Prediction : Screen("prediction")
    data object PredictionResult : Screen("prediction_result")
    data object ExplainPrediction : Screen("explain_prediction")
    data object Assistant : Screen("assistant")
    data object ModelInfo : Screen("model_info")
    data object Settings : Screen("settings")
    data object About : Screen("about")
}
