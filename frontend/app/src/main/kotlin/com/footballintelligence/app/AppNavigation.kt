package com.footballintelligence.app

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.navArgument
import com.footballintelligence.core.navigation.Screen
import com.footballintelligence.core.ui.SettingsButton
import com.footballintelligence.feature.assistant.AssistantScreen
import com.footballintelligence.feature.assistant.AssistantViewModel
import com.footballintelligence.feature.home.BackendStatusSection
import com.footballintelligence.feature.home.BackendStatusViewModel
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
import com.footballintelligence.feature.team.FavouriteTeamViewModel
import com.footballintelligence.feature.team.MyTeamScreen
import com.footballintelligence.feature.team.MyTeamSettingsSection
import com.footballintelligence.feature.team.MyTeamViewModel
import com.footballintelligence.feature.team.PickerFlow
import org.koin.androidx.compose.koinViewModel

/**
 * Root of the app: the navigation graph, with a bottom bar on the top-level
 * screens (fixtures, predict, my team, assistant) and Settings behind the
 * top bar's settings icon. The first launch starts with onboarding.
 */
@Composable
fun AppNavigation(navController: NavHostController) {
    val favourite: FavouriteTeamViewModel = koinViewModel()
    val start = if (favourite.needsOnboarding) Screen.Onboarding.route else Screen.Home.route
    val entry by navController.currentBackStackEntryAsState()
    val current = TopLevelDestination.forRoute(entry?.destination?.route)
    Scaffold(
        bottomBar = {
            if (current != null) {
                BottomNavBar(current = current, onSelect = { navController.navigateTo(it) })
            }
        },
    ) { padding ->
        AppNavHost(
            navController,
            start,
            Modifier
                .padding(padding)
                .consumeWindowInsets(padding),
        )
    }
}

/**
 * Switches tabs, keeping each tab's own back stack and state. Fixtures is the
 * root tab even on first launch, when the graph starts at onboarding.
 */
private fun NavHostController.navigateTo(destination: TopLevelDestination) {
    navigate(destination.screen.route) {
        popUpTo(Screen.Home.route) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}

/** Leaves onboarding for Fixtures, then opens My Team with the new favourite. */
private fun NavHostController.finishOnboarding() {
    navigate(Screen.Home.route) { popUpTo(Screen.Onboarding.route) { inclusive = true } }
    navigateTo(TopLevelDestination.MY_TEAM)
}

@Composable
private fun AppNavHost(navController: NavHostController, startDestination: String, modifier: Modifier) {
    val settingsAction: @Composable RowScope.() -> Unit = {
        SettingsButton(onClick = { navController.navigate(Screen.Settings.route) })
    }
    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier,
    ) {
        composable(Screen.Onboarding.route) {
            TeamPickerRoute(
                flow = PickerFlow.ONBOARDING,
                onLeave = {},
                onOnboardingFinished = navController::finishOnboarding,
            )
        }

        composable(
            Screen.ChangeTeam.route,
            arguments = listOf(navArgument(FLOW_ARG) { type = NavType.StringType }),
        ) { entry ->
            TeamPickerRoute(
                flow = PickerFlow.valueOf(checkNotNull(entry.arguments?.getString(FLOW_ARG))),
                onLeave = { navController.popBackStack() },
                onOnboardingFinished = {},
            )
        }

        composable(Screen.MyTeam.route) {
            val vm: MyTeamViewModel = koinViewModel()
            val state by vm.state.collectAsState()
            val isRefreshing by vm.isRefreshing.collectAsState()
            MyTeamScreen(
                uiState = state,
                onRetry = vm::retry,
                isRefreshing = isRefreshing,
                onRefresh = vm::refresh,
                actions = settingsAction,
            )
        }

        composable(Screen.Home.route) {
            val vm: HomeViewModel = koinViewModel()
            val state by vm.state.collectAsState()
            val selectedLeague by vm.selectedLeague.collectAsState()
            val isRefreshing by vm.isRefreshing.collectAsState()
            HomeScreen(
                uiState = state,
                leagues = vm.leagues,
                selectedLeague = selectedLeague,
                onSelectLeague = vm::selectLeague,
                onRetry = vm::retry,
                isRefreshing = isRefreshing,
                onRefresh = vm::refresh,
                actions = settingsAction,
            )
        }

        composable(Screen.Prediction.route) {
            val vm: PredictionViewModel = koinViewModel()
            val state by vm.predictionState.collectAsState()
            val teamsState by vm.teamsState.collectAsState()
            val competitionsState by vm.competitionsState.collectAsState()
            val isRefreshing by vm.isRefreshing.collectAsState()
            PredictionScreen(
                uiState = state,
                competitionsState = competitionsState,
                teamsState = teamsState,
                onSelectCompetition = vm::selectCompetition,
                onPredict = vm::predict,
                onRetryTeams = vm::loadTeams,
                onNavigateToResult = {
                    navController.navigate(Screen.PredictionResult.route)
                },
                onBack = { navController.popBackStack() },
                isRefreshing = isRefreshing,
                onRefresh = vm::refreshTeams,
                actions = settingsAction,
            )
        }

        composable(Screen.PredictionResult.route) {
            val vm: PredictionViewModel = koinViewModel(
                viewModelStoreOwner = navController.getBackStackEntry(Screen.Prediction.route),
            )
            val state by vm.predictionState.collectAsState()
            val insightsState by vm.insightsState.collectAsState()
            val isRefreshing by vm.isRefreshing.collectAsState()
            // Leaving the result must clear it; otherwise the team selection
            // screen still holds a finished prediction and shows a spinner.
            val backToTeamSelection: () -> Unit = {
                vm.resetPrediction()
                navController.popBackStack(Screen.Prediction.route, inclusive = false)
            }
            BackHandler(onBack = backToTeamSelection)
            PredictionResultScreen(
                uiState = state,
                insightsState = insightsState,
                onExplain = {
                    vm.explain()
                    navController.navigate(Screen.ExplainPrediction.route)
                },
                onNewPrediction = backToTeamSelection,
                onBack = backToTeamSelection,
                isRefreshing = isRefreshing,
                onRefresh = vm::refreshPrediction,
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
                actions = settingsAction,
            )
        }

        composable(Screen.Settings.route) {
            val vm: BackendStatusViewModel = koinViewModel()
            val status by vm.state.collectAsState()
            val team: FavouriteTeamViewModel = koinViewModel()
            SettingsScreen(
                onModelInfoClick = { navController.navigate(Screen.ModelInfo.route) },
                onAboutClick = { navController.navigate(Screen.About.route) },
                onBack = { navController.popBackStack() },
                status = { BackendStatusSection(status, onRetry = vm::retry) },
                myTeam = {
                    team.favourite?.let {
                        MyTeamSettingsSection(
                            favourite = it,
                            onChangeLeague = {
                                navController.navigate(Screen.ChangeTeam.route(PickerFlow.CHANGE_LEAGUE.name))
                            },
                            onChangeTeam = {
                                navController.navigate(Screen.ChangeTeam.route(PickerFlow.CHANGE_TEAM.name))
                            },
                        )
                    }
                },
            )
        }

        composable(Screen.ModelInfo.route) {
            val vm: SettingsViewModel = koinViewModel()
            val state by vm.modelInfoState.collectAsState()
            val isRefreshing by vm.isRefreshing.collectAsState()
            ModelInfoScreen(
                uiState = state,
                onRetry = vm::retry,
                onBack = { navController.popBackStack() },
                isRefreshing = isRefreshing,
                onRefresh = vm::refresh,
            )
        }

        composable(Screen.About.route) {
            AboutScreen(onBack = { navController.popBackStack() })
        }
    }
}

private const val FLOW_ARG = "flow"
