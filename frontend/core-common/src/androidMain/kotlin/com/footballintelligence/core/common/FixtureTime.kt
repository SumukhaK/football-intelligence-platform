package com.footballintelligence.core.common

import java.time.LocalDate
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

/**
 * The phone's calendar day for a fixture: its kick-off day in [zone] when the
 * time is known, otherwise the date the league lists.
 */
fun fixtureDay(matchDate: String, kickoff: String?, zone: ZoneId = ZoneId.systemDefault()): LocalDate =
    kickoff?.let { OffsetDateTime.parse(it).atZoneSameInstant(zone).toLocalDate() }
        ?: LocalDate.parse(matchDate)

/** Kick-off time in the phone's zone, e.g. "17:00". */
fun formatKickoff(
    kickoff: String,
    zone: ZoneId = ZoneId.systemDefault(),
    locale: Locale = Locale.getDefault(),
): String =
    DateTimeFormatter.ofPattern("HH:mm", locale)
        .format(OffsetDateTime.parse(kickoff).atZoneSameInstant(zone))

/** A fixtures list day heading, e.g. "Sat 10 Oct". */
fun formatMatchDay(day: LocalDate, locale: Locale = Locale.getDefault()): String =
    DateTimeFormatter.ofPattern("EEE d MMM", locale).format(day)
