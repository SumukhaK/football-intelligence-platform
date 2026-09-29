package com.footballintelligence.core.model

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class CompetitionsTest {
    private val json = Json { ignoreUnknownKeys = true }

    @Test
    fun `decodes the competitions response`() {
        val body =
            """{"default":"Premier League","competitions":[{"name":"Bundesliga",
               "season":"2026/27","team_count":18,"matches_through":"2026-09-20",
               "insights_available":true}]}"""
        val decoded = json.decodeFromString<CompetitionsResponse>(body)
        assertEquals("Premier League", decoded.default)
        assertEquals(Competition("Bundesliga", "2026/27", 18, "2026-09-20", true), decoded.competitions[0])
    }

    @Test
    fun `requests send the league when one is chosen`() {
        val encoded = json.encodeToString(PredictionRequest("Bayern Munich", "Leipzig", competition = "Bundesliga"))
        assertTrue(encoded.contains("\"competition\":\"Bundesliga\""))
    }

    @Test
    fun `requests without a league leave it out`() {
        assertFalse(json.encodeToString(PredictionRequest("Arsenal", "Chelsea")).contains("competition"))
    }

    @Test
    fun `older servers without a league decode to an empty one`() {
        val result = json.decodeFromString<PredictionResult>(
            """{"home_team":"Arsenal","away_team":"Chelsea","predicted_result":"H",
               "probability_home":0.5,"probability_draw":0.3,"probability_away":0.2,
               "confidence":0.5,"model_version":"v1"}""",
        )
        assertEquals("", result.competition)
    }
}
