package com.footballintelligence.feature.team

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.common.formatSavedAt
import com.footballintelligence.core.model.FavouriteTeamStore
import com.footballintelligence.core.model.Fixture
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.feature.team.repository.TeamRepository
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.ZoneId
import java.util.Locale

/**
 * ViewModel for [MyTeamScreen]: the favourite team's next unplayed fixture,
 * its pick, the reasons behind it and the goals model's view.
 */
class MyTeamViewModel(
    private val repository: TeamRepository,
    store: FavouriteTeamStore,
    private val now: () -> Instant = Instant::now,
    private val zone: ZoneId = ZoneId.systemDefault(),
    private val locale: Locale = Locale.getDefault(),
) : ViewModel() {

    private val favourite = checkNotNull(store.load()) { "My Team opened before a favourite team was saved" }

    private val _state = MutableStateFlow<MyTeamUiState>(MyTeamUiState.Loading)
    val state: StateFlow<MyTeamUiState> = _state.asStateFlow()

    private val _isRefreshing = MutableStateFlow(false)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing.asStateFlow()

    init {
        retry()
    }

    fun retry() {
        _state.value = MyTeamUiState.Loading
        viewModelScope.launch { _state.value = fetch() }
    }

    /** Pull to refresh: reloads while the current content stays on screen. */
    fun refresh() {
        _isRefreshing.value = true
        viewModelScope.launch {
            _state.value = fetch()
            _isRefreshing.value = false
        }
    }

    private suspend fun fetch(): MyTeamUiState =
        when (val result = repository.getTeamFixtures(favourite)) {
            is NetworkResult.Success -> nextMatchState(result.data, result.cachedAt?.let { formatSavedAt(it) })
            is NetworkResult.Error -> MyTeamUiState.Error(result.message, result.kind)
            is NetworkResult.Loading -> MyTeamUiState.Loading
        }

    /** The first fixture not yet played; once a match is over the card moves on to the next. */
    private suspend fun nextMatchState(fixtures: List<Fixture>, savedAt: String?): MyTeamUiState {
        val fixture = fixtures.firstOrNull { !it.isOver(now(), zone) }
            ?: return MyTeamUiState.NoUpcomingMatch(favourite.team, savedAt)
        return forecast(fixture, savedAt)
    }

    private suspend fun forecast(fixture: Fixture, savedAt: String?): MyTeamUiState = coroutineScope {
        val request = PredictionRequest(fixture.homeTeam, fixture.awayTeam, favourite.league)
        val explanation = async { repository.explain(request) }
        val insights = async { repository.insights(request) }
        when (val prediction = repository.predict(request)) {
            is NetworkResult.Success -> MyTeamUiState.Success(
                match = nextMatch(
                    team = favourite.team,
                    fixture = fixture,
                    prediction = prediction.data,
                    explanation = (explanation.await() as? NetworkResult.Success)?.data,
                    insights = (insights.await() as? NetworkResult.Success)?.data,
                    zone = zone,
                    locale = locale,
                ),
                savedAt = savedAt ?: prediction.cachedAt?.let { formatSavedAt(it) },
            )
            is NetworkResult.Error -> MyTeamUiState.Error(prediction.message, prediction.kind)
            is NetworkResult.Loading -> MyTeamUiState.Loading
        }
    }
}
