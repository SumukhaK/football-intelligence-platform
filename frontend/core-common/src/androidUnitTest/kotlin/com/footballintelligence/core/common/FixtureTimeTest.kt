package com.footballintelligence.core.common

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import java.time.LocalDate
import java.time.ZoneId
import java.util.Locale

class FixtureTimeTest {
    private val london = ZoneId.of("Europe/London")
    private val kolkata = ZoneId.of("Asia/Kolkata")

    @Test
    fun `a fixture's day is its kick-off day in the phone's zone`() {
        val day = fixtureDay("2026-10-10", "2026-10-10T20:00:00+01:00", kolkata)
        assertEquals(LocalDate.of(2026, 10, 11), day)
    }

    @Test
    fun `a fixture without a time keeps its listed date`() {
        assertEquals(LocalDate.of(2026, 10, 10), fixtureDay("2026-10-10", null, kolkata))
    }

    @Test
    fun `kick-off is shown in the phone's zone`() {
        assertEquals("12:30", formatKickoff("2026-10-10T12:30:00+01:00", london))
        assertEquals("17:00", formatKickoff("2026-10-10T12:30:00+01:00", kolkata))
    }

    @Test
    fun `match day reads as weekday, day and month`() {
        assertEquals("Sat 10 Oct", formatMatchDay(LocalDate.of(2026, 10, 10), Locale.US))
    }
}
