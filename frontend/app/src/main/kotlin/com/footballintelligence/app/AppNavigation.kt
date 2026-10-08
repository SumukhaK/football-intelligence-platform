package com.footballintelligence.app

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import com.footballintelligence.core.navigation.Screen
import com.footballintelligence.core.ui.SettingsButton
import com.footballintelligence.feature.assistant.AssistantScreen
import com.footballintelligence.feature.assistant.AssistantViewModel
import com.footballintelligence.feature.auth.SignOutViewModel
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
import com.footballintelligence.feature.team.ProjectedTableScreen
import org.koin.androidx.compose.koinViewModel

/**
 * Root of the app: the navigation graph, with a bottom bar on the top-level
 * screens (fixtures, predict, my team, assistant) and Settings behind the
 * top bar's settings icon. The app starts at sign-in without a session, else
 * at the notice check (ADR 022); then onboarding on first launch, else home.
 */
@Composable
fun AppNavigation(navController: NavHostController, signedIn: Boolean) {
    val favourite: FavouriteTeamViewModel = koinViewModel()
    val firstRoute = if (favourite.needsOnboarding) Screen.Onboarding.route else Screen.Home.route
    // Read once: NavHost rebuilds its graph if the start destination changes.
    val start = remember { if (signedIn) Screen.Consent.route else Screen.Auth.route }
    FollowSession(navController, signedIn)
    val entry by navController.currentBackStackEntryAsState()
    val route = entry?.destination?.route
    val current = TopLevelDestination.forRoute(route)
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
            firstRoute,
            if (route in FULL_SCREEN_ROUTES) Modifier else Modifier.padding(padding).consumeWindowInsets(padding),
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

private const val FIXTURE_KEY = "fixture"

/**
 * Opens the predict tab fresh for a fixture tapped on home: any earlier
 * prediction flow is dropped, then the new screen predicts the fixture.
 */
private fun NavHostController.openFixture(league: String, homeTeam: String, awayTeam: String) {
    clearBackStack(Screen.Prediction.route)
    navigateTo(TopLevelDestination.PREDICT)
    getBackStackEntry(Screen.Prediction.route).savedStateHandle[FIXTURE_KEY] =
        arrayListOf(league, homeTeam, awayTeam)
}

@Composable
private fun AppNavHost(
    navController: NavHostController,
    startDestination: String,
    firstRoute: String,
    modifier: Modifier,
) {
    val settingsAction: @Composable RowScope.() -> Unit = {
        SettingsButton(onClick = { navController.navigate(Screen.Settings.route) })
    }
    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier,
    ) {
        authRoutes(onReady = { navController.restartAt(firstRoute) })

        composable(Screen.Onboarding.route) {
            TeamPickerRoute(
                flow = PickerFlow.ONBOARDING,
                onLeave = {},
                onOnboardingFinished = navController::finishOnboarding,
            )
        }

        composable(Screen.ChangeTeam.route) {
            TeamPickerRoute(
                flow = PickerFlow.CHANGE,
                onLeave = { navController.popBackStack() },
                onOnboardingFinished = {},
            )
        }

        composable(Screen.MyTeam.route) {
            val vm: MyTeamViewModel = koinViewModel()
            val state by vm.state.collectAsState()
            val outlook by vm.outlookState.collectAsState()
            val isRefreshing by vm.isRefreshing.collectAsState()
            MyTeamScreen(
                uiState = state,
                outlookState = outlook,
                onRetry = vm::retry,
                onOpenTable = { navController.navigate(Screen.SeasonTable.route) },
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
                onFixtureClick = { navController.openFixture(selectedLeague, it.homeTeam, it.awayTeam) },
            )
        }

        composable(Screen.SeasonTable.route) {
            val vm: MyTeamViewModel = koinViewModel(
                viewModelStoreOwner = navController.getBackStackEntry(Screen.MyTeam.route),
            )
            val outlook by vm.outlookState.collectAsState()
            ProjectedTableScreen(
                uiState = outlook,
                onRetry = vm::retry,
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.Prediction.route) { entry ->
            val vm: PredictionViewModel = koinViewModel()
            LaunchedEffect(entry) {
                entry.savedStateHandle.remove<ArrayList<String>>(FIXTURE_KEY)?.let { (league, home, away) ->
                    vm.predictFixture(league, home, away)
                }
            }
            val presetTeams by vm.presetTeams.collectAsState()
            val state by vm.predictionState.collectAsState()
            val teamsState by vm.teamsState.collectAsState()
            val competitionsState by vm.competitionsState.collectAsState()
            val isRefreshing by vm.isRefreshing.collectAsState()
            PredictionScreen(
                uiState = state,
                competitionsState = competitionsState,
                teamsState = teamsState,
                onSelectCompetition = vm::selectCompetition,
                onPredict = { home, away -> vm.predict(home, away) },
                onRetryTeams = vm::loadTeams,
                onNavigateToResult = {
                    navController.navigate(Screen.PredictionResult.route)
                },
                onBack = { navController.popBackStack() },
                isRefreshing = isRefreshing,
                onRefresh = vm::refreshTeams,
                actions = settingsAction,
                presetTeams = presetTeams,
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
            val account: SignOutViewModel = koinViewModel()
            SettingsScreen(
                onModelInfoClick = { navController.navigate(Screen.ModelInfo.route) },
                onAboutClick = { navController.navigate(Screen.About.route) },
                onBack = { navController.popBackStack() },
                onSignOut = account::signOut,
                status = { BackendStatusSection(status, onRetry = vm::retry) },
                myTeam = {
                    team.favourite?.let {
                        MyTeamSettingsSection(
                            favourite = it,
                            onChange = { navController.navigate(Screen.ChangeTeam.route) },
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
