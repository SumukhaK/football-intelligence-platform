package com.footballintelligence.feature.team.repository

import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.Fixture
import com.footballintelligence.core.model.Insights
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.PredictionRequest
import com.footballintelligence.core.model.PredictionResult
import com.footballintelligence.core.model.TeamsResponse
import com.footballintelligence.core.network.FootballApiService

/** Data for the favourite team: its league's teams, its fixtures and match forecasts. */
interface TeamRepository {
    suspend fun getTeams(league: String): NetworkResult<TeamsResponse>

    /** The team's upcoming fixtures, earliest first. */
    suspend fun getTeamFixtures(favourite: FavouriteTeam): NetworkResult<List<Fixture>>
    suspend fun predict(request: PredictionRequest): NetworkResult<PredictionResult>
    suspend fun explain(request: PredictionRequest): NetworkResult<ExplanationResult>
    suspend fun insights(request: PredictionRequest): NetworkResult<Insights>
}

/** Production implementation backed by [FootballApiService]. */
class DefaultTeamRepository(
    private val api: FootballApiService,
) : TeamRepository {
    override suspend fun getTeams(league: String): NetworkResult<TeamsResponse> = api.getTeams(league)

    override suspend fun getTeamFixtures(favourite: FavouriteTeam): NetworkResult<List<Fixture>> =
        when (val result = api.getFixtures(favourite.league)) {
            is NetworkResult.Success -> NetworkResult.Success(
                result.data.fixtures.filter { favourite.team == it.homeTeam || favourite.team == it.awayTeam },
                result.cachedAt,
            )
            is NetworkResult.Error -> result
            is NetworkResult.Loading -> result
        }

    override suspend fun predict(request: PredictionRequest): NetworkResult<PredictionResult> = api.predict(request)

    override suspend fun explain(request: PredictionRequest): NetworkResult<ExplanationResult> = api.explain(request)

    override suspend fun insights(request: PredictionRequest): NetworkResult<Insights> = api.getInsights(request)
}
