package com.footballintelligence.feature.home.repository

import com.footballintelligence.core.model.FixturesResponse
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.network.FootballApiService

/** Retrieves a league's upcoming fixtures. */
interface FixturesRepository {
    suspend fun getFixtures(competition: String): NetworkResult<FixturesResponse>
}

/** Production implementation backed by [FootballApiService]. */
class DefaultFixturesRepository(
    private val api: FootballApiService,
) : FixturesRepository {
    override suspend fun getFixtures(competition: String): NetworkResult<FixturesResponse> =
        api.getFixtures(competition)
}
