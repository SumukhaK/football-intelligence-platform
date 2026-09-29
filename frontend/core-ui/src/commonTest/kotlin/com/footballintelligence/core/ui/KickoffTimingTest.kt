package com.footballintelligence.core.ui

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class KickoffTimingTest {
    private val tolerance = 0.01f

    @Test
    fun `nothing is drawn at the start of a cycle`() {
        assertEquals(listOf(0f, 0f, 0f), kickoffSweeps(0f))
    }

    @Test
    fun `the arcs fill home first, then draw, then away`() {
        val early = kickoffSweeps(0.08f)
        assertTrue(early[0] > 0f)
        assertEquals(0f, early[1], tolerance)
        assertEquals(0f, early[2], tolerance)
        val later = kickoffSweeps(0.15f)
        assertTrue(later[1] > 0f)
        assertEquals(0f, later[2], tolerance)
    }

    @Test
    fun `each arc ends at its share of the ring`() {
        val full = kickoffSweeps(0.9f)
        assertEquals(KICKOFF_ARCS[0].sweepDegrees, full[0], tolerance)
        assertEquals(KICKOFF_ARCS[1].sweepDegrees, full[1], tolerance)
        assertEquals(KICKOFF_ARCS[2].sweepDegrees, full[2], tolerance)
    }

    @Test
    fun `the three arcs and their gaps close the ring`() {
        val total = KICKOFF_ARCS.sumOf { it.sweepDegrees.toDouble() } + KICKOFF_ARCS.size * KICKOFF_GAP_DEGREES
        assertEquals(360.0, total, 0.01)
    }

    @Test
    fun `arcs start where the previous one ends plus a gap`() {
        val (home, draw, away) = KICKOFF_ARCS
        assertEquals(home.startDegrees + home.sweepDegrees + KICKOFF_GAP_DEGREES, draw.startDegrees, tolerance)
        assertEquals(draw.startDegrees + draw.sweepDegrees + KICKOFF_GAP_DEGREES, away.startDegrees, tolerance)
    }
}
