package com.footballintelligence.feature.prediction

import com.footballintelligence.core.model.NetworkResult
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
}
