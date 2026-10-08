package com.footballintelligence.feature.team

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
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

/** ViewModel for [TeamPickerScreen]: a league step, then that league's teams. */
class TeamPickerViewModel(
    private val flow: PickerFlow,
    private val repository: TeamRepository,
    private val store: FavouriteTeamStore,
) : ViewModel() {

    private val leagues = PickerStep.League(SERVED_LEAGUES)

    private val _step = MutableStateFlow<PickerStep>(leagues)
    val step: StateFlow<PickerStep> = _step.asStateFlow()

    private val outcomes = Channel<PickerOutcome>(Channel.BUFFERED)

    /** Emits once a team is saved; the app then leaves onboarding or relaunches. */
    val outcome: Flow<PickerOutcome> = outcomes.receiveAsFlow()

    init {
        if (flow == PickerFlow.CHANGE_TEAM) store.load()?.let { selectLeague(it.league) }
    }

    /** Moves to [league]'s teams. */
    fun selectLeague(league: String) {
        val loading = PickerStep.Team(league, TeamsUiState.Loading)
        _step.value = loading
        viewModelScope.launch {
            val teams = when (val result = repository.getTeams(league)) {
                is NetworkResult.Success -> TeamsUiState.Success(result.data.teams)
                is NetworkResult.Error -> TeamsUiState.Error(result.message, result.kind)
                is NetworkResult.Loading -> TeamsUiState.Loading
            }
            // The fan may have gone back to the leagues while this loaded.
            if (_step.value == loading) _step.value = PickerStep.Team(league, teams)
        }
    }

    fun retryTeams() {
        (_step.value as? PickerStep.Team)?.let { selectLeague(it.league) }
    }

    fun backToLeagues() {
        _step.value = leagues
    }

    /** Saves [team] of the league on screen as the favourite. */
    fun selectTeam(team: String) {
        val league = (_step.value as? PickerStep.Team)?.league ?: return
        store.save(FavouriteTeam(league, team))
        outcomes.trySend(
            if (flow == PickerFlow.ONBOARDING) PickerOutcome.ONBOARDING_FINISHED else PickerOutcome.RELAUNCH,
        )
    }
}
