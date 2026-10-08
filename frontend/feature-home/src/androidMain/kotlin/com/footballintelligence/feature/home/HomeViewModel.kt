package com.footballintelligence.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.common.fixtureDay
import com.footballintelligence.core.common.formatKickoff
import com.footballintelligence.core.common.formatMatchDay
import com.footballintelligence.core.common.formatSavedAt
import com.footballintelligence.core.model.Fixture
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.SERVED_LEAGUES
import com.footballintelligence.feature.home.repository.FixturesRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.ZoneId
import java.util.Locale

/**
 * ViewModel for [HomeScreen]: upcoming fixtures of the selected league. The
 * fan's [favouriteLeague], when saved, is the first tab and opens selected.
 */
class HomeViewModel(
    private val repository: FixturesRepository,
    favouriteLeague: String? = null,
    private val zone: ZoneId = ZoneId.systemDefault(),
    private val locale: Locale = Locale.getDefault(),
) : ViewModel() {

    /** League tabs, in display order. */
    val leagues: List<String> = SERVED_LEAGUES.sortedByDescending { it == favouriteLeague }

    private val _selectedLeague = MutableStateFlow(leagues.first())
    val selectedLeague: StateFlow<String> = _selectedLeague.asStateFlow()

    private val _state = MutableStateFlow<HomeUiState>(HomeUiState.Loading)
    val state: StateFlow<HomeUiState> = _state.asStateFlow()

    private val _isRefreshing = MutableStateFlow(false)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing.asStateFlow()

    init {
        load()
    }

    /** Shows [league]'s fixtures. */
    fun selectLeague(league: String) {
        _selectedLeague.value = league
        load()
    }

    fun retry() {
        load()
    }

    /** Pull to refresh: reloads while the current content stays on screen. */
    fun refresh() {
        _isRefreshing.value = true
        viewModelScope.launch {
            _state.value = fetch(_selectedLeague.value)
            _isRefreshing.value = false
        }
    }

    private fun load() {
        _state.value = HomeUiState.Loading
        val league = _selectedLeague.value
        viewModelScope.launch {
            val result = fetch(league)
            // A slower answer for a league the user has left must not replace the new one.
            if (league == _selectedLeague.value) _state.value = result
        }
    }

    private suspend fun fetch(league: String): HomeUiState =
        when (val result = repository.getFixtures(league)) {
            is NetworkResult.Success -> HomeUiState.Success(
                days = fixtureDays(result.data.fixtures),
                savedAt = result.cachedAt?.let { formatSavedAt(it) },
            )
            is NetworkResult.Error -> HomeUiState.Error(result.message, result.kind)
            is NetworkResult.Loading -> HomeUiState.Loading
        }

    private fun fixtureDays(fixtures: List<Fixture>): List<FixtureDay> =
        fixtures
            .groupBy { fixtureDay(it.matchDate, it.kickoff, zone) }
            .toSortedMap()
            .map { (day, onDay) ->
                FixtureDay(
                    label = formatMatchDay(day, locale),
                    fixtures = onDay.map {
                        FixtureRow(it.homeTeam, it.awayTeam, it.kickoff?.let { k -> formatKickoff(k, zone, locale) })
                    },
                )
            }
}
