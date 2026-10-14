package com.footballintelligence.feature.prediction

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class ResultToShowTest {
    private val error = PredictionInputUiState.Error("Server down")

    @Test
    fun `leaving the result keeps it on screen instead of flashing an error`() {
        assertEquals(error, resultToShow(previous = error, current = PredictionInputUiState.Idle))
    }

    @Test
    fun `a result screen that never had a result says so`() {
        val idle = PredictionInputUiState.Idle
        assertEquals(idle, resultToShow(previous = null, current = idle))
    }

    @Test
    fun `a new state replaces the old one`() {
        val loading = PredictionInputUiState.Loading
        assertEquals(loading, resultToShow(previous = error, current = loading))
    }
}
