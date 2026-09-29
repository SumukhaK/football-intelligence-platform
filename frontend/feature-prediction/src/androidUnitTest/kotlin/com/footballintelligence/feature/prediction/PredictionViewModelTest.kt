package com.footballintelligence.feature.prediction

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
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
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

    private val fixture = PredictionRequest(homeTeam = "Arsenal", awayTeam = "Chelsea")

    @BeforeEach
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @AfterEach
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `loads teams from the api on start`() {
        coEvery { repository.teams() } returns NetworkResult.Success(teams)
        val viewModel = PredictionViewModel(repository)
        assertEquals(TeamsUiState.Success("2026/27", teams.teams), viewModel.teamsState.value)
    }

    @Test
    fun `teams error is shown with its message`() {
        coEvery { repository.teams() } returns NetworkResult.Error("HTTP 503")
        val viewModel = PredictionViewModel(repository)
        assertEquals(TeamsUiState.Error("HTTP 503"), viewModel.teamsState.value)
    }

    @Test
    fun `an empty team list is an error, not a crash`() {
        coEvery { repository.teams() } returns
            NetworkResult.Success(TeamsResponse("Premier League", "2026/27", emptyList()))
        val viewModel = PredictionViewModel(repository)
        assertEquals(
            TeamsUiState.Error("No teams available for Premier League 2026/27"),
            viewModel.teamsState.value,
        )
    }

    @Test
    fun `retrying teams after an error loads them`() {
        coEvery { repository.teams() } returnsMany listOf(
            NetworkResult.Error("HTTP 503"),
            NetworkResult.Success(teams),
        )
        val viewModel = PredictionViewModel(repository)
        viewModel.loadTeams()
        assertEquals(TeamsUiState.Success("2026/27", teams.teams), viewModel.teamsState.value)
    }

    @Test
    fun `predict sends only the two teams`() {
        coEvery { repository.teams() } returns NetworkResult.Success(teams)
        val request = PredictionRequest(homeTeam = "Arsenal", awayTeam = "Chelsea")
        coEvery { repository.predict(request) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(request) } returns NetworkResult.Success(insights)
        val viewModel = PredictionViewModel(repository)

        viewModel.predict("Arsenal", "Chelsea")

        coVerify(exactly = 1) { repository.predict(request) }
        assertEquals(PredictionInputUiState.Success(prediction), viewModel.predictionState.value)
    }

    @Test
    fun `explain reuses the predicted teams`() {
        coEvery { repository.teams() } returns NetworkResult.Success(teams)
        val request = PredictionRequest(homeTeam = "Arsenal", awayTeam = "Chelsea")
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
        coEvery { repository.teams() } returns NetworkResult.Success(teams)
        val viewModel = PredictionViewModel(repository)
        viewModel.explain()
        assertEquals(ExplanationUiState.Idle, viewModel.explanationState.value)
        coVerify(exactly = 0) { repository.explain(any()) }
    }

    @Test
    fun `insights load alongside the prediction`() {
        coEvery { repository.teams() } returns NetworkResult.Success(teams)
        coEvery { repository.predict(fixture) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(fixture) } returns NetworkResult.Success(insights)
        val viewModel = PredictionViewModel(repository)

        viewModel.predict("Arsenal", "Chelsea")

        coVerify(exactly = 1) { repository.insights(fixture) }
        assertEquals(InsightsUiState.Success(insights), viewModel.insightsState.value)
    }

    @Test
    fun `an insights error keeps the prediction`() {
        coEvery { repository.teams() } returns NetworkResult.Success(teams)
        coEvery { repository.predict(fixture) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(fixture) } returns NetworkResult.Error("HTTP 503")
        val viewModel = PredictionViewModel(repository)

        viewModel.predict("Arsenal", "Chelsea")

        assertEquals(PredictionInputUiState.Success(prediction), viewModel.predictionState.value)
        assertEquals(InsightsUiState.Error("HTTP 503"), viewModel.insightsState.value)
    }

    @Test
    fun `reset clears the insights`() {
        coEvery { repository.teams() } returns NetworkResult.Success(teams)
        coEvery { repository.predict(fixture) } returns NetworkResult.Success(prediction)
        coEvery { repository.insights(fixture) } returns NetworkResult.Success(insights)
        val viewModel = PredictionViewModel(repository)

        viewModel.predict("Arsenal", "Chelsea")
        viewModel.resetPrediction()

        assertEquals(InsightsUiState.Idle, viewModel.insightsState.value)
    }
}
