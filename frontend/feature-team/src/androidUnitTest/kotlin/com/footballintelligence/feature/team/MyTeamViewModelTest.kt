package com.footballintelligence.feature.team

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.ExpectedGoals
import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.FavouriteTeamStore
import com.footballintelligence.core.model.FeatureContribution
import com.footballintelligence.core.model.Fixture
import com.footballintelligence.core.model.GoalMarkets
import com.footballintelligence.core.model.Insights
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.OutcomeProbabilities
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.model.ScoreProbability
import com.footballintelligence.feature.team.repository.TeamRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.time.Instant
import java.time.ZoneId
import java.util.Locale

@OptIn(ExperimentalCoroutinesApi::class)
class MyTeamViewModelTest {
    private val repository = mockk<TeamRepository>()
    private val store = mockk<FavouriteTeamStore> {
        every { load() } returns FavouriteTeam("Premier League", "Arsenal")
    }
    private val now = Instant.parse("2026-10-10T12:00:00Z")

    // Kicked off 3.5 hours before "now", so it has been played.
    private val played = Fixture("2026-10-10", "2026-10-10T09:30:00+01:00", "Arsenal", "Leeds", "Matchday 6")
    private val next = Fixture("2026-10-18", "2026-10-18T16:30:00+01:00", "Everton", "Arsenal", "Matchday 7")
    private val nextRequest = PredictionRequest("Everton", "Arsenal", "Premier League")

    private val awayWin = PredictionResult(
        homeTeam = "Everton",
        awayTeam = "Arsenal",
        predictedResult = "A",
        probabilityHome = 0.2,
        probabilityDraw = 0.28,
        probabilityAway = 0.52,
        confidence = 0.52,
        modelVersion = "test",
        drawPossible = true,
    )

    private fun feature(name: String, shap: Double) = FeatureContribution(name, 1.0, shap, name, "$shap")

    private val explanation = ExplanationResult(
        homeTeam = "Everton",
        awayTeam = "Arsenal",
        predictedResult = "A",
        probabilityHome = 0.2,
        probabilityDraw = 0.28,
        probabilityAway = 0.52,
        confidence = 0.52,
        topPositiveFeatures = listOf(feature("d", 0.1), feature("a", 0.4), feature("b", 0.3), feature("c", 0.2)),
        topNegativeFeatures = emptyList(),
        allContributions = emptyList(),
        modelVersion = "test",
        featureVersion = "v1",
        datasetVersion = "v1",
        explanationTimestamp = "2026-10-10T12:00:00Z",
    )

    private val insights = Insights(
        homeTeam = "Everton",
        awayTeam = "Arsenal",
        modelVersion = "dc",
        fittedBefore = "2026-10-10",
        expectedGoals = ExpectedGoals(0.9, 1.6),
        topScores = listOf(
            ScoreProbability(0, 1, 0.14),
            ScoreProbability(1, 1, 0.12),
            ScoreProbability(0, 2, 0.11),
            ScoreProbability(1, 2, 0.09),
        ),
        markets = GoalMarkets(0.45, 0.7, 0.45, 0.2, homeCleanSheet = 0.2, awayCleanSheet = 0.31),
        outcome = OutcomeProbabilities(0.22, 0.27, 0.51),
        reasons = emptyList(),
    )

    private fun respond(
        fixtures: List<Fixture> = listOf(played, next),
        prediction: PredictionResult = awayWin,
        cachedAt: String? = null,
    ) {
        coEvery { repository.getTeamFixtures(FavouriteTeam("Premier League", "Arsenal")) } returns
            NetworkResult.Success(fixtures, cachedAt)
        coEvery { repository.predict(any()) } returns NetworkResult.Success(prediction)
        coEvery { repository.explain(any()) } returns NetworkResult.Success(explanation)
        coEvery { repository.insights(any()) } returns NetworkResult.Success(insights)
    }

    private fun viewModel(at: Instant = now) =
        MyTeamViewModel(repository, store, { at }, ZoneId.of("Europe/London"), Locale.US)

    @BeforeEach
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        // The season outlook has its own tests in SeasonOutlookViewModelTest.
        coEvery { repository.getOutlook(any()) } returns NetworkResult.Error("unused")
    }

    @AfterEach
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun `the card shows the next match from the team's side`() {
        respond()
        val state = viewModel().state.value as MyTeamUiState.Success
        val expected = NextMatch(
            homeTeam = "Everton",
            awayTeam = "Arsenal",
            day = "Sun 18 Oct",
            time = "16:30",
            pick = TeamOutcome.WIN,
            pickPercent = 52,
            drawPossible = true,
            reasons = listOf(MatchReason("a", "0.4"), MatchReason("b", "0.3"), MatchReason("c", "0.2")),
            scorelines = listOf(Scoreline(0, 1, 14), Scoreline(1, 1, 12), Scoreline(0, 2, 11)),
            cleanSheetPercent = 31,
        )
        assertEquals(expected, state.match)
        coVerify { repository.predict(nextRequest) }
    }

    @Test
    fun `a home win against the team is a loss`() {
        respond(prediction = awayWin.copy(predictedResult = "H", confidence = 0.6))
        val match = (viewModel().state.value as MyTeamUiState.Success).match
        assertEquals(TeamOutcome.LOSS, match.pick)
        assertEquals(60, match.pickPercent)
    }

    @Test
    fun `a draw pick is a draw`() {
        respond(prediction = awayWin.copy(predictedResult = "D"))
        assertEquals(TeamOutcome.DRAW, (viewModel().state.value as MyTeamUiState.Success).match.pick)
    }

    @Test
    fun `a match still in play stays on the card`() {
        respond()
        val duringMatch = Instant.parse("2026-10-10T09:30:00Z")
        val match = (viewModel(duringMatch).state.value as MyTeamUiState.Success).match
        assertEquals("Leeds", match.awayTeam)
    }

    @Test
    fun `a fixture without a kick-off time counts until its day is over`() {
        respond(fixtures = listOf(played.copy(kickoff = null), next))
        val match = (viewModel().state.value as MyTeamUiState.Success).match
        assertEquals("Leeds", match.awayTeam)
        assertEquals(null, match.time)
    }

    @Test
    fun `no match left is its own state`() {
        respond(fixtures = listOf(played))
        assertEquals(MyTeamUiState.NoUpcomingMatch("Arsenal"), viewModel().state.value)
    }

    @Test
    fun `missing explanation and insights leave those parts out`() {
        respond()
        coEvery { repository.explain(any()) } returns NetworkResult.Error("503", kind = ErrorKind.SERVER_BUSY)
        coEvery { repository.insights(any()) } returns NetworkResult.Error("503", kind = ErrorKind.SERVER_BUSY)
        val match = (viewModel().state.value as MyTeamUiState.Success).match
        assertEquals(emptyList<MatchReason>(), match.reasons)
        assertEquals(emptyList<Scoreline>(), match.scorelines)
        assertEquals(null, match.cleanSheetPercent)
    }

    @Test
    fun `an unreachable server is an error`() {
        coEvery { repository.getTeamFixtures(any()) } returns
            NetworkResult.Error("Connection refused", kind = ErrorKind.OFFLINE)
        assertEquals(ErrorKind.OFFLINE, (viewModel().state.value as MyTeamUiState.Error).kind)
    }

    @Test
    fun `a failed prediction is an error`() {
        respond()
        coEvery { repository.predict(any()) } returns
            NetworkResult.Error("Model not available", kind = ErrorKind.SERVER_BUSY)
        assertEquals(ErrorKind.SERVER_BUSY, (viewModel().state.value as MyTeamUiState.Error).kind)
    }

    @Test
    fun `saved data carries when it was saved`() {
        respond(cachedAt = "2026-10-09T09:00:00Z")
        assertNotNull((viewModel().state.value as MyTeamUiState.Success).savedAt)
    }

    @Test
    fun `refresh reloads without leaving the content`() {
        respond()
        val vm = viewModel()
        vm.refresh()
        coVerify(exactly = 2) { repository.getTeamFixtures(any()) }
        assertEquals(MyTeamUiState.Success::class, vm.state.value::class)
        assertFalse(vm.isRefreshing.value)
    }

    @Test
    fun `retry loads again after an error`() {
        coEvery { repository.getTeamFixtures(any()) } returns NetworkResult.Error("down", kind = ErrorKind.OFFLINE)
        val vm = viewModel()
        respond()
        vm.retry()
        assertEquals(MyTeamUiState.Success::class, vm.state.value::class)
    }
}
