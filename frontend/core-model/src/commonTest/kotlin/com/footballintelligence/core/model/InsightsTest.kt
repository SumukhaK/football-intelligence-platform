package com.footballintelligence.core.model

import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class InsightsTest {
    private val json = Json { ignoreUnknownKeys = true }

    private val body =
        """{"home_team":"Arsenal","away_team":"Chelsea","model_version":"dc-2026-09-28",
           "fitted_before":"2026-09-28","expected_goals":{"home":1.95,"away":0.98},
           "top_scores":[{"home":1,"away":1,"probability":0.112},{"home":2,"away":0,"probability":0.102}],
           "markets":{"btts":0.544,"over_1_5":0.799,"over_2_5":0.56,"over_3_5":0.336,
                      "home_clean_sheet":0.376,"away_clean_sheet":0.143},
           "outcome":{"home":0.59,"draw":0.235,"away":0.175},
           "strengths":{"home_attack":1.23,"home_defence":0.69,"away_attack":1.13,"away_defence":1.06},
           "reasons":["Arsenal concede 31% fewer goals than an average side in this league"]}"""

    @Test
    fun `decodes the insights response`() {
        val insights = json.decodeFromString<Insights>(body)
        assertEquals(1.95, insights.expectedGoals.home)
        assertEquals(ScoreProbability(home = 1, away = 1, probability = 0.112), insights.topScores.first())
        assertEquals(0.56, insights.markets.over25)
        assertEquals(0.376, insights.markets.homeCleanSheet)
        assertEquals(1, insights.reasons.size)
    }
}
