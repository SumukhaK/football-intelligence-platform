package com.footballintelligence.feature.prediction

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.common.formatSavedAt
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

    private val _isRefreshing = MutableStateFlow(false)
    val isRefreshing: StateFlow<Boolean> = _isRefreshing.asStateFlow()

    private var lastRequest: PredictionRequest? = null

    /** The league of a fixture opened from home, selected once the leagues load. */
    private var fixtureLeague: String? = null

    private val _presetTeams = MutableStateFlow<Pair<String, String>?>(null)

    /** Home and away teams the team pickers start on, set when a fixture is opened. */
    val presetTeams: StateFlow<Pair<String, String>?> = _presetTeams.asStateFlow()

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
                        selected = fixtureLeague
                            ?.takeIf { league -> result.data.competitions.any { it.name == league } }
                            ?: result.data.default,
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
        val league = selectedCompetition
        if (league == null) {
            loadCompetitions()
            return
        }
        _teamsState.value = TeamsUiState.Loading
        viewModelScope.launch {
            _teamsState.value = teamsState(repository.teams(league))
        }
    }

    /**
     * Opens a fixture tapped on the home list: selects its league, presets its
     * teams and predicts it straight away.
     */
    fun predictFixture(league: String, homeTeam: String, awayTeam: String) {
        fixtureLeague = league
        _presetTeams.value = homeTeam to awayTeam
        val competitions = _competitionsState.value
        if (competitions is CompetitionsUiState.Success && competitions.selected != league) {
            selectCompetition(league)
        }
        predict(homeTeam, awayTeam, league)
    }

    /**
     * Requests a prediction and, in parallel, the goals insights for the same
     * fixture. An insights failure never affects the prediction.
     */
    fun predict(homeTeam: String, awayTeam: String, competition: String? = selectedCompetition) {
        _predictionState.value = PredictionInputUiState.Loading
        val request = PredictionRequest(homeTeam = homeTeam, awayTeam = awayTeam, competition = competition)
        lastRequest = request
        loadInsights(request)
        viewModelScope.launch {
            _predictionState.value = when (val result = repository.predict(request)) {
                is NetworkResult.Success -> PredictionInputUiState.Success(
                    result.data,
                    savedAt = result.cachedAt?.let { formatSavedAt(it) },
                )
                is NetworkResult.Error -> PredictionInputUiState.Error(result.message, result.kind)
                is NetworkResult.Loading -> PredictionInputUiState.Loading
            }
        }
    }

    /** Requests a SHAP explanation for the current prediction's fixture. */
    fun explain() {
        if (_predictionState.value !is PredictionInputUiState.Success) return
        val request = lastRequest ?: return
        _explanationState.value = ExplanationUiState.Loading
        viewModelScope.launch {
            _explanationState.value = when (val result = repository.explain(request)) {
                is NetworkResult.Success -> ExplanationUiState.Success(
                    result.data,
                    savedAt = result.cachedAt?.let { formatSavedAt(it) },
                )
                is NetworkResult.Error -> ExplanationUiState.Error(result.message, result.kind)
                is NetworkResult.Loading -> ExplanationUiState.Loading
            }
        }
    }

    /** Pull to refresh on the result: asks again for the same fixture. */
    fun refreshPrediction() {
        val request = lastRequest ?: return
        _isRefreshing.value = true
        loadInsights(request)
        viewModelScope.launch {
            val result = repository.predict(request)
            if (result is NetworkResult.Success) {
                _predictionState.value = PredictionInputUiState.Success(
                    result.data,
                    savedAt = result.cachedAt?.let { formatSavedAt(it) },
                )
            }
            _isRefreshing.value = false
        }
    }

    /** Pull to refresh on team selection: reloads the leagues and teams. */
    fun refreshTeams() {
        _isRefreshing.value = true
        viewModelScope.launch {
            val result = repository.competitions()
            if (result is NetworkResult.Success) {
                val current = _competitionsState.value as? CompetitionsUiState.Success
                val selected = current?.selected ?: result.data.default
                _competitionsState.value =
                    CompetitionsUiState.Success(result.data.competitions, selected)
            }
            val league = selectedCompetition
            if (league != null) _teamsState.value = teamsState(repository.teams(league))
            _isRefreshing.value = false
        }
    }

    /** Clears the current prediction, explanation and insights. */
    fun resetPrediction() {
        _predictionState.value = PredictionInputUiState.Idle
        _explanationState.value = ExplanationUiState.Idle
        _insightsState.value = InsightsUiState.Idle
    }

    private val selectedCompetition: String?
        get() = (_competitionsState.value as? CompetitionsUiState.Success)?.selected

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

private fun teamsState(result: NetworkResult<TeamsResponse>): TeamsUiState =
    when (result) {
        is NetworkResult.Success -> result.data.toUiState(result.cachedAt?.let { formatSavedAt(it) })
        is NetworkResult.Error -> TeamsUiState.Error(result.message, result.kind)
        is NetworkResult.Loading -> TeamsUiState.Loading
    }

/** A team list needs at least two teams to pick a fixture from. */
private fun TeamsResponse.toUiState(savedAt: String?): TeamsUiState =
    if (teams.size < 2) {
        TeamsUiState.Error("No teams available for $competition $season")
    } else {
        TeamsUiState.Success(season, teams, savedAt)
    }
