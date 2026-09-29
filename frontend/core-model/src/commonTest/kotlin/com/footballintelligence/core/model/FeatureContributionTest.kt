package com.footballintelligence.core.model

import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class FeatureContributionTest {

    private val json = Json { ignoreUnknownKeys = true }

    @Test
    fun `decodes the fan-friendly fields from the api`() {
        val decoded = json.decodeFromString<FeatureContribution>(
            """{"feature_name":"home_elo_before","feature_value":1617.7,"shap_value":0.34,
               "display_name":"Arsenal team strength rating","display_value":"1618"}""",
        )
        assertEquals("Arsenal team strength rating", decoded.label())
        assertEquals("1618", decoded.valueText())
    }

    @Test
    fun `falls back to the raw name and value from older servers`() {
        val decoded = json.decodeFromString<FeatureContribution>(
            """{"feature_name":"home_win_pct","feature_value":0.681,"shap_value":0.09}""",
        )
        assertEquals("home win pct", decoded.label())
        assertEquals("0.681", decoded.valueText())
    }

    @Test
    fun `impact is relative to the strongest contribution`() {
        val strongest = 0.34
        assertEquals(Impact.BIG, contribution(0.34).impact(strongest))
        assertEquals(Impact.BIG, contribution(-0.2).impact(strongest))
        assertEquals(Impact.MEDIUM, contribution(0.09).impact(strongest))
        assertEquals(Impact.SMALL, contribution(0.004).impact(strongest))
        assertEquals(Impact.SMALL, contribution(0.0).impact(0.0))
    }

    private fun contribution(shap: Double) = FeatureContribution(
        featureName = "x",
        featureValue = 1.0,
        shapValue = shap,
    )
}
