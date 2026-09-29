package com.footballintelligence.feature.prediction

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.TeamsResponse
import com.footballintelligence.feature.prediction.repository.PredictionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** ViewModel for team selection, prediction and explanation. */
class PredictionViewModel(
    private val repository: PredictionRepository,
) : ViewModel() {

    private val _competitionsState =
        MutableStateFlow<CompetitionsUiState>(CompetitionsUiState.Loading)
    val competitionsState: StateFlow<CompetitionsUiState> = _competitionsState.asStateFlow()

    private val _teamsState = MutableStateFlow<TeamsUiState>(TeamsUiState.Loading)
    val teamsState: StateFlow<TeamsUiState> = _teamsState.asStateFlow()

    private val _predictionState =
        MutableStateFlow<PredictionInputUiState>(PredictionInputUiState.Idle)
    val predictionState: StateFlow<PredictionInputUiState> = _predictionState.asStateFlow()

    private val _explanationState =
        MutableStateFlow<ExplanationUiState>(ExplanationUiState.Idle)
    val explanationState: StateFlow<ExplanationUiState> = _explanationState.asStateFlow()

    private val _insightsState = MutableStateFlow<InsightsUiState>(InsightsUiState.Idle)
    val insightsState: StateFlow<InsightsUiState> = _insightsState.asStateFlow()

    init {
        loadCompetitions()
    }

    /** Loads the served leagues, selects the default and loads its teams. */
    fun loadCompetitions() {
        _competitionsState.value = CompetitionsUiState.Loading
        viewModelScope.launch {
            when (val result = repository.competitions()) {
                is NetworkResult.Success -> {
                    _competitionsState.value = CompetitionsUiState.Success(
                        competitions = result.data.competitions,
                        selected = result.data.default,
                    )
                    loadTeams()
                }
                is NetworkResult.Error -> {
                    _competitionsState.value = CompetitionsUiState.Error(result.message, result.kind)
                    _teamsState.value = TeamsUiState.Error(result.message, result.kind)
                }
                is NetworkResult.Loading -> Unit
            }
        }
    }

    /** Switches league and loads its teams. */
    fun selectCompetition(name: String) {
        val current = _competitionsState.value
        if (current !is CompetitionsUiState.Success || current.selected == name) return
        _competitionsState.value = current.copy(selected = name)
        loadTeams()
    }

    /** Loads the selected league's teams, or retries loading the leagues. */
    fun loadTeams() {
        val league = selectedCompetition()
        if (league == null) {
            loadCompetitions()
            return
        }
        _teamsState.value = TeamsUiState.Loading
        viewModelScope.launch {
            _teamsState.value = when (val result = repository.teams(league)) {
                is NetworkResult.Success -> result.data.toUiState()
                is NetworkResult.Error -> TeamsUiState.Error(result.message, result.kind)
                is NetworkResult.Loading -> TeamsUiState.Loading
            }
        }
    }

    /**
     * Requests a prediction and, in parallel, the goals insights for the same
     * fixture. An insights failure never affects the prediction.
     */
    fun predict(homeTeam: String, awayTeam: String) {
        _predictionState.value = PredictionInputUiState.Loading
        val request = PredictionRequest(
            homeTeam = homeTeam,
            awayTeam = awayTeam,
            competition = selectedCompetition(),
        )
        loadInsights(request)
        viewModelScope.launch {
            _predictionState.value = when (val result = repository.predict(request)) {
                is NetworkResult.Success -> PredictionInputUiState.Success(result.data)
                is NetworkResult.Error -> PredictionInputUiState.Error(result.message, result.kind)
                is NetworkResult.Loading -> PredictionInputUiState.Loading
            }
        }
    }

    /** Requests a SHAP explanation for the current prediction's teams. */
    fun explain() {
        val current = _predictionState.value
        if (current !is PredictionInputUiState.Success) return
        _explanationState.value = ExplanationUiState.Loading
        val request = PredictionRequest(
            homeTeam = current.result.homeTeam,
            awayTeam = current.result.awayTeam,
            competition = selectedCompetition(),
        )
        viewModelScope.launch {
            _explanationState.value = when (val result = repository.explain(request)) {
                is NetworkResult.Success -> ExplanationUiState.Success(result.data)
                is NetworkResult.Error -> ExplanationUiState.Error(result.message, result.kind)
                is NetworkResult.Loading -> ExplanationUiState.Loading
            }
        }
    }

    /** Clears the current prediction, explanation and insights. */
    fun resetPrediction() {
        _predictionState.value = PredictionInputUiState.Idle
        _explanationState.value = ExplanationUiState.Idle
        _insightsState.value = InsightsUiState.Idle
    }

    private fun selectedCompetition(): String? =
        (_competitionsState.value as? CompetitionsUiState.Success)?.selected

    private fun loadInsights(request: PredictionRequest) {
        _insightsState.value = InsightsUiState.Loading
        viewModelScope.launch {
            _insightsState.value = when (val result = repository.insights(request)) {
                is NetworkResult.Success -> InsightsUiState.Success(result.data)
                is NetworkResult.Error -> InsightsUiState.Error(result.message, result.kind)
                is NetworkResult.Loading -> InsightsUiState.Loading
            }
        }
    }
}

/** A team list needs at least two teams to pick a fixture from. */
private fun TeamsResponse.toUiState(): TeamsUiState =
    if (teams.size < 2) {
        TeamsUiState.Error("No teams available for $competition $season")
    } else {
        TeamsUiState.Success(season, teams)
    }
