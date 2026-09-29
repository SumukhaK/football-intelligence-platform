package com.footballintelligence.core.common

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import java.time.ZoneId
import java.util.Locale

class SavedAtTest {
    @Test
    fun `shows the saved time in the phone's time zone`() {
        val text = formatSavedAt("2026-09-29T09:00:00Z", ZoneId.of("Asia/Kolkata"), Locale.US)
        assertEquals("29 Sep, 14:30", text)
    }

    @Test
    fun `unreadable times are shown as they are`() {
        assertEquals("yesterday", formatSavedAt("yesterday", ZoneId.of("UTC"), Locale.US))
    }
}
