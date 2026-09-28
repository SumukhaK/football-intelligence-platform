package com.footballintelligence.core.model

import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class PredictionResultTest {
    private val json = Json { ignoreUnknownKeys = true }

    private fun body(extra: String = "") =
        """{"home_team":"Arsenal","away_team":"Chelsea","predicted_result":"H",
           "probability_home":0.41,"probability_draw":0.29,"probability_away":0.30,
           "confidence":0.41,"model_version":"v1"$extra}"""

    @Test
    fun `decodes the draw possible flag`() {
        val decoded = json.decodeFromString<PredictionResult>(body(""","draw_possible":true"""))
        assertTrue(decoded.drawPossible)
    }

    @Test
    fun `older servers without the flag mean no tag`() {
        val decoded = json.decodeFromString<PredictionResult>(body())
        assertFalse(decoded.drawPossible)
    }
}
