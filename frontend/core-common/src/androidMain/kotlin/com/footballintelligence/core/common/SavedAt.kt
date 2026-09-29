package com.footballintelligence.core.common

import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException
import java.util.Locale

/**
 * When saved data was fetched, for the offline banner: "29 Sep, 14:30" in the
 * phone's time zone. Text that isn't an ISO 8601 instant is returned unchanged.
 */
fun formatSavedAt(
    iso: String,
    zone: ZoneId = ZoneId.systemDefault(),
    locale: Locale = Locale.getDefault(),
): String =
    try {
        DateTimeFormatter.ofPattern("d MMM, HH:mm", locale).withZone(zone).format(Instant.parse(iso))
    } catch (e: DateTimeParseException) {
        iso
    }
