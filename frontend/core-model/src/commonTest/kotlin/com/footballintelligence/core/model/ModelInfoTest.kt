package com.footballintelligence.core.model

import kotlinx.serialization.json.Json
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

class ModelInfoTest {
    private val json = Json { ignoreUnknownKeys = true }

    private fun body(extra: String = "") =
        """{"model_version":"20260928_123224","dataset_version":"top5",
           "training_timestamp":"2026-09-28T12:32:24Z"$extra}"""

    @Test
    fun `decodes the model name`() {
        val info = json.decodeFromString<ModelInfo>(body(""","model_name":"Drishti""""))
        assertEquals("Drishti", info.modelName)
    }

    @Test
    fun `an older backend without a model name decodes to null`() {
        val info = json.decodeFromString<ModelInfo>(body())
        assertNull(info.modelName)
    }
}
