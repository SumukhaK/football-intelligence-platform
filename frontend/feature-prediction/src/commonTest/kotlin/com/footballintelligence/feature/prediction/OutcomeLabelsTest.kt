package com.footballintelligence.feature.prediction

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

class OutcomeLabelsTest {
    @Test
    fun `a home win is won by the home team`() {
        assertEquals("Arsenal", winningTeam("H", "Arsenal", "Leeds"))
    }

    @Test
    fun `an away win is won by the away team`() {
        assertEquals("Leeds", winningTeam("A", "Arsenal", "Leeds"))
    }

    @Test
    fun `a draw has no winner`() {
        assertNull(winningTeam("D", "Arsenal", "Leeds"))
    }
}
