package com.footballintelligence.feature.team

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.FavouriteTeamStore
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.SERVED_LEAGUES
import com.footballintelligence.feature.team.repository.TeamRepository
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for [TeamPickerScreen]: a league step, then that league's teams.
 * Opened from Settings, the saved league and team start checked.
 */
class TeamPickerViewModel(
    private val flow: PickerFlow,
    private val repository: TeamRepository,
    private val store: FavouriteTeamStore,
) : ViewModel() {

    private val saved = if (flow == PickerFlow.CHANGE) store.load() else null
    private val leagues = PickerStep.League(SERVED_LEAGUES, selected = saved?.league)

    private val _step = MutableStateFlow<PickerStep>(leagues)
    val step: StateFlow<PickerStep> = _step.asStateFlow()

    private val outcomes = Channel<PickerOutcome>(Channel.BUFFERED)

    /** Emits once a team is saved; the app then leaves onboarding or relaunches. */
    val outcome: Flow<PickerOutcome> = outcomes.receiveAsFlow()

    /** Moves to [league]'s teams. */
    fun selectLeague(league: String) {
        val selected = saved?.team?.takeIf { saved.league == league }
        val loading = PickerStep.Team(league, TeamsUiState.Loading, selected)
        _step.value = loading
        viewModelScope.launch {
            val teams = when (val result = repository.getTeams(league)) {
                is NetworkResult.Success -> TeamsUiState.Success(result.data.teams)
                is NetworkResult.Error -> TeamsUiState.Error(result.message, result.kind)
                is NetworkResult.Loading -> TeamsUiState.Loading
            }
            // The fan may have gone back to the leagues while this loaded.
            if (_step.value == loading) _step.value = loading.copy(teams = teams)
        }
    }

    fun retryTeams() {
        (_step.value as? PickerStep.Team)?.let { selectLeague(it.league) }
    }

    fun backToLeagues() {
        _step.value = leagues
    }

    /** Checks [team] of the league on screen and saves it as the favourite. */
    fun selectTeam(team: String) {
        val step = _step.value as? PickerStep.Team ?: return
        _step.value = step.copy(selected = team)
        store.save(FavouriteTeam(step.league, team))
        outcomes.trySend(
            if (flow == PickerFlow.ONBOARDING) PickerOutcome.ONBOARDING_FINISHED else PickerOutcome.RELAUNCH,
        )
    }
}
