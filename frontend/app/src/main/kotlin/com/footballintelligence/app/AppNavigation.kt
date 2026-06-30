package com.footballintelligence.app

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.footballintelligence.core.navigation.Screen
import com.footballintelligence.feature.assistant.AssistantScreen
import com.footballintelligence.feature.assistant.AssistantViewModel
import com.footballintelligence.feature.home.HomeScreen
import com.footballintelligence.feature.home.HomeViewModel
import com.footballintelligence.feature.prediction.ExplainPredictionScreen
import com.footballintelligence.feature.prediction.PredictionResultScreen
import com.footballintelligence.feature.prediction.PredictionScreen
import com.footballintelligence.feature.prediction.PredictionViewModel
import com.footballintelligence.feature.settings.AboutScreen
import com.footballintelligence.feature.settings.ModelInfoScreen
import com.footballintelligence.feature.settings.SettingsScreen
import com.footballintelligence.feature.settings.SettingsViewModel
import org.koin.androidx.compose.koinViewModel

/** Root navigation graph for the Football Intelligence app. */
@Composable
fun AppNavigation(navController: NavHostController) {
    NavHost(
        navController = navController,
        startDestination = Screen.Home.route,
    ) {
        composable(Screen.Home.route) {
            val vm: HomeViewModel = koinViewModel()
            val state by vm.state.collectAsState()
            HomeScreen(
                uiState = state,
                onPredictClick = { navController.navigate(Screen.Prediction.route) },
                onAssistantClick = { navController.navigate(Screen.Assistant.route) },
                onSettingsClick = { navController.navigate(Screen.Settings.route) },
                onRetry = vm::retry,
            )
        }

        composable(Screen.Prediction.route) {
            val vm: PredictionViewModel = koinViewModel()
            val state by vm.predictionState.collectAsState()
            PredictionScreen(
                uiState = state,
                onPredict = vm::predict,
                onNavigateToResult = {
                    navController.navigate(Screen.PredictionResult.route)
                },
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.PredictionResult.route) {
            val vm: PredictionViewModel = koinViewModel(
                viewModelStoreOwner = navController.getBackStackEntry(Screen.Prediction.route),
            )
            val state by vm.predictionState.collectAsState()
            PredictionResultScreen(
                uiState = state,
                onExplain = {
                    vm.explain()
                    navController.navigate(Screen.ExplainPrediction.route)
                },
                onNewPrediction = {
                    vm.resetPrediction()
                    navController.popBackStack(Screen.Prediction.route, inclusive = false)
                },
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.ExplainPrediction.route) {
            val vm: PredictionViewModel = koinViewModel(
                viewModelStoreOwner = navController.getBackStackEntry(Screen.Prediction.route),
            )
            val state by vm.explanationState.collectAsState()
            ExplainPredictionScreen(
                uiState = state,
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.Assistant.route) {
            val vm: AssistantViewModel = koinViewModel()
            val state by vm.state.collectAsState()
            val isSending by vm.isSending.collectAsState()
            AssistantScreen(
                uiState = state,
                isSending = isSending,
                onSend = vm::send,
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                onModelInfoClick = { navController.navigate(Screen.ModelInfo.route) },
                onAboutClick = { navController.navigate(Screen.About.route) },
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.ModelInfo.route) {
            val vm: SettingsViewModel = koinViewModel()
            val state by vm.modelInfoState.collectAsState()
            ModelInfoScreen(
                uiState = state,
                onRetry = vm::retry,
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.About.route) {
            AboutScreen(onBack = { navController.popBackStack() })
        }
    }
}
