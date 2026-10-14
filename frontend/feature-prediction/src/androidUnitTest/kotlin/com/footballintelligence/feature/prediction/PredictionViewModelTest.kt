package com.footballintelligence.feature.prediction

import com.footballintelligence.core.model.Competition
import com.footballintelligence.core.model.CompetitionsResponse
import com.footballintelligence.core.model.ExpectedGoals
import com.footballintelligence.core.model.GoalMarkets
import com.footballintelligence.core.model.Insights
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.OutcomeProbabilities
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.model.TeamsResponse
import com.footballintelligence.feature.prediction.repository.PredictionRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

@OptIn(ExperimentalCoroutinesApi::class)
class PredictionViewModelTest {

    private val repository = mockk<PredictionRepository>()

    private val teams = TeamsResponse(
        competition = "Premier League",
        season = "2026/27",
        teams = listOf("Arsenal", "Chelsea", "Leeds"),
    )

    private val prediction = PredictionResult(
        homeTeam = "Arsenal",
        awayTeam = "Chelsea",
        predictedResult = "H",
        probabilityHome = 0.5,
        probabilityDraw = 0.3,
        probabilityAway = 0.2,
        confidence = 0.5,
        modelVersion = "test-v1",
    )

    private val insights = Insights(
        homeTeam = "Arsenal",
        awayTeam = "Chelsea",
        modelVersion = "dc-2026-09-28",
        fittedBefore = "2026-09-28",
        expectedGoals = ExpectedGoals(home = 1.9, away = 1.0),
        topScores = emptyList(),
        markets = GoalMarkets(0.5, 0.8, 0.55, 0.3, 0.35, 0.15),
        outcome = OutcomeProbabilities(home = 0.58, draw = 0.24, away = 0.18),
        reasons = emptyList(),
    )

    private val fixture = PredictionRequest(
        homeTeam = "Arsenal",
        awayTeam = "Chelsea",
        competition = "Premier League",
    )

    private val leagues = CompetitionsResponse(
        default = "Premier League",
        competitions = listOf(
            Competition("Premier League", "2026/27", 20, "2026-09-20", true),
            Competition("Bundesliga", "2026/27", 18, "2026-09-20", true),
        ),
    )

    private val bundesligaTeams = TeamsResponse(
        competition = "Bundesliga",
        season = "2026/27",
        teams = listOf("Bayern Munich", "Dortmund", "Leipzig"),
    )

    @BeforeEach
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        coEvery { repository.competitions() } returns NetworkResult.Success(leagues)
    }

    @AfterEach
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `loads teams from the api on start`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        val viewModel = PredictionViewModel(repository)
        assertEquals(TeamsUiState.Success("2026/27", teams.teams), viewModel.teamsState.value)
    }

    @Test
    fun `teams error is shown with its message`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Error("HTTP 503")
        val viewModel = PredictionViewModel(repository)
        assertEquals(TeamsUiState.Error("HTTP 503"), viewModel.teamsState.value)
    }

    @Test
    fun `an empty team list is an error, not a crash`() {
        coEvery { repository.teams("Premier League") } returns
            NetworkResult.Success(TeamsResponse("Premier League", "2026/27", emptyList()))
        val viewModel = PredictionViewModel(repository)
        assertEquals(
            TeamsUiState.Error("No teams available for Premier League 2026/27"),
            viewModel.teamsState.value,
        )
    }

    @Test
    fun `retrying teams after an error loads them`() {
        coEvery { repository.teams("Premier League") } returnsMany listOf(
            NetworkResult.Error("HTTP 503"),
            NetworkResult.Success(teams),
        )
        val viewModel = PredictionViewModel(repository)
        viewModel.loadTeams()
        assertEquals(TeamsUiState.Success("2026/27", teams.teams), viewModel.teamsState.value)
    }

    @Test
    fun `predict sends only the two teams`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        val request = fixture
        coEvery { repository.predict(request) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(request) } returns NetworkResult.Success(insights)
        val viewModel = PredictionViewModel(repository)

        viewModel.predict("Arsenal", "Chelsea")

        coVerify(exactly = 1) { repository.predict(request) }
        assertEquals(PredictionInputUiState.Success(prediction), viewModel.predictionState.value)
    }

    @Test
    fun `explain reuses the predicted teams`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        val request = fixture
        coEvery { repository.predict(request) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(request) } returns NetworkResult.Success(insights)
        coEvery { repository.explain(request) } returns NetworkResult.Error("HTTP 422")
        val viewModel = PredictionViewModel(repository)

        viewModel.predict("Arsenal", "Chelsea")
        viewModel.explain()

        coVerify(exactly = 1) { repository.explain(request) }
        assertEquals(ExplanationUiState.Error("HTTP 422"), viewModel.explanationState.value)
    }

    @Test
    fun `explain does nothing before a prediction`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        val viewModel = PredictionViewModel(repository)
        viewModel.explain()
        assertEquals(ExplanationUiState.Idle, viewModel.explanationState.value)
        coVerify(exactly = 0) { repository.explain(any()) }
    }

    @Test
    fun `insights load alongside the prediction`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        coEvery { repository.predict(fixture) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(fixture) } returns NetworkResult.Success(insights)
        val viewModel = PredictionViewModel(repository)

        viewModel.predict("Arsenal", "Chelsea")

        coVerify(exactly = 1) { repository.insights(fixture) }
        assertEquals(InsightsUiState.Success(insights), viewModel.insightsState.value)
    }

    @Test
    fun `an insights error keeps the prediction`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        coEvery { repository.predict(fixture) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(fixture) } returns NetworkResult.Error("HTTP 503")
        val viewModel = PredictionViewModel(repository)

        viewModel.predict("Arsenal", "Chelsea")

        assertEquals(PredictionInputUiState.Success(prediction), viewModel.predictionState.value)
        assertEquals(InsightsUiState.Error("HTTP 503"), viewModel.insightsState.value)
    }

    @Test
    fun `reset clears the insights`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        coEvery { repository.predict(fixture) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(fixture) } returns NetworkResult.Success(insights)
        val viewModel = PredictionViewModel(repository)

        viewModel.predict("Arsenal", "Chelsea")
        viewModel.resetPrediction()

        assertEquals(InsightsUiState.Idle, viewModel.insightsState.value)
    }

    @Test
    fun `loads the leagues and selects the default`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        val viewModel = PredictionViewModel(repository)
        assertEquals(
            CompetitionsUiState.Success(leagues.competitions, selected = "Premier League"),
            viewModel.competitionsState.value,
        )
    }

    @Test
    fun `choosing a league loads its teams`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        coEvery { repository.teams("Bundesliga") } returns NetworkResult.Success(bundesligaTeams)
        val viewModel = PredictionViewModel(repository)

        viewModel.selectCompetition("Bundesliga")

        assertEquals(
            TeamsUiState.Success("2026/27", bundesligaTeams.teams),
            viewModel.teamsState.value,
        )
        assertEquals(
            CompetitionsUiState.Success(leagues.competitions, selected = "Bundesliga"),
            viewModel.competitionsState.value,
        )
    }

    @Test
    fun `predictions carry the chosen league`() {
        coEvery { repository.teams(any()) } returns NetworkResult.Success(bundesligaTeams)
        val request = PredictionRequest("Bayern Munich", "Leipzig", competition = "Bundesliga")
        coEvery { repository.predict(request) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(request) } returns NetworkResult.Success(insights)
        val viewModel = PredictionViewModel(repository)

        viewModel.selectCompetition("Bundesliga")
        viewModel.predict("Bayern Munich", "Leipzig")

        coVerify(exactly = 1) { repository.predict(request) }
        coVerify(exactly = 1) { repository.insights(request) }
    }

    @Test
    fun `a leagues error is shown and can be retried`() {
        coEvery { repository.competitions() } returnsMany listOf(
            NetworkResult.Error("HTTP 503"),
            NetworkResult.Success(leagues),
        )
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        val viewModel = PredictionViewModel(repository)
        assertEquals(CompetitionsUiState.Error("HTTP 503"), viewModel.competitionsState.value)

        viewModel.loadCompetitions()

        assertEquals(TeamsUiState.Success("2026/27", teams.teams), viewModel.teamsState.value)
    }

    @Test
    fun `a saved prediction is shown with when it was saved`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        coEvery { repository.predict(fixture) } returns
            NetworkResult.Success(prediction, cachedAt = "2026-09-29T09:00:00Z")
        coEvery { repository.insights(fixture) } returns NetworkResult.Success(insights)
        val viewModel = PredictionViewModel(repository)

        viewModel.predict("Arsenal", "Chelsea")

        val state = viewModel.predictionState.value as PredictionInputUiState.Success
        assertEquals(prediction, state.result)
        assertTrue(state.savedAt != null)
    }

    @Test
    fun `refreshing a prediction asks again for the same fixture`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        coEvery { repository.predict(fixture) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(fixture) } returns NetworkResult.Success(insights)
        val viewModel = PredictionViewModel(repository)

        viewModel.predict("Arsenal", "Chelsea")
        viewModel.refreshPrediction()

        coVerify(exactly = 2) { repository.predict(fixture) }
        coVerify(exactly = 2) { repository.insights(fixture) }
        assertEquals(PredictionInputUiState.Success(prediction), viewModel.predictionState.value)
        assertFalse(viewModel.isRefreshing.value)
    }

    @Test
    fun `refreshing teams reloads the leagues and teams`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        val viewModel = PredictionViewModel(repository)

        viewModel.refreshTeams()

        coVerify(exactly = 2) { repository.competitions() }
        coVerify(exactly = 2) { repository.teams("Premier League") }
    }

    @Test
    fun `a fixture from home predicts its teams in its league`() {
        coEvery { repository.teams("Premier League") } returns NetworkResult.Success(teams)
        coEvery { repository.teams("Bundesliga") } returns NetworkResult.Success(bundesligaTeams)
        val request = PredictionRequest("Bayern Munich", "Leipzig", competition = "Bundesliga")
        coEvery { repository.predict(request) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(request) } returns NetworkResult.Success(insights)
        val viewModel = PredictionViewModel(repository)

        viewModel.predictFixture("Bundesliga", "Bayern Munich", "Leipzig")

        coVerify(exactly = 1) { repository.predict(request) }
        assertEquals(PredictionInputUiState.Success(prediction), viewModel.predictionState.value)
        assertEquals("Bayern Munich" to "Leipzig", viewModel.presetTeams.value)
        assertEquals(
            CompetitionsUiState.Success(leagues.competitions, selected = "Bundesliga"),
            viewModel.competitionsState.value,
        )
        assertEquals(
            TeamsUiState.Success("2026/27", bundesligaTeams.teams),
            viewModel.teamsState.value,
        )
    }

    @Test
    fun `a fixture opened before the leagues load keeps its league`() {
        val pending = CompletableDeferred<NetworkResult<CompetitionsResponse>>()
        coEvery { repository.competitions() } coAnswers { pending.await() }
        coEvery { repository.teams("Bundesliga") } returns NetworkResult.Success(bundesligaTeams)
        val request = PredictionRequest("Bayern Munich", "Leipzig", competition = "Bundesliga")
        coEvery { repository.predict(request) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(request) } returns NetworkResult.Success(insights)
        val viewModel = PredictionViewModel(repository)

        viewModel.predictFixture("Bundesliga", "Bayern Munich", "Leipzig")
        pending.complete(NetworkResult.Success(leagues))

        coVerify(exactly = 1) { repository.predict(request) }
        coVerify(exactly = 0) { repository.teams("Premier League") }
        assertEquals(
            CompetitionsUiState.Success(leagues.competitions, selected = "Bundesliga"),
            viewModel.competitionsState.value,
        )
    }
}
