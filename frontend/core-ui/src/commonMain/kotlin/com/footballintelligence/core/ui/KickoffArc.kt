package com.footballintelligence.core.ui

import androidx.compose.animation.core.FastOutSlowInEasing

/** One arc of the Kick-off ring: where it starts (0° is 12 o'clock) and how far it runs. */
data class KickoffArc(val startDegrees: Float, val sweepDegrees: Float, val delay: Float)

/** Gap between arcs, so the three outcomes stay distinct. */
const val KICKOFF_GAP_DEGREES = 10.8f

/** Home, draw and away, sized 47%, 22% and 22% of the ring like the app icon's concept. */
val KICKOFF_ARCS: List<KickoffArc> = listOf(
    KickoffArc(startDegrees = 0f, sweepDegrees = 169.2f, delay = 0f),
    KickoffArc(startDegrees = 180f, sweepDegrees = 79.2f, delay = 0.1f),
    KickoffArc(startDegrees = 270f, sweepDegrees = 79.2f, delay = 0.2f),
)

/** Share of a cycle each arc takes to fill; the rest of the cycle it holds. */
private const val FILL_FRACTION = 0.45f

/**
 * How far each arc has filled, in degrees, at [progress] through one cycle (0 to 1).
 * Arcs start one after another and hold once full, like the Kick-off splash screen.
 */
fun kickoffSweeps(progress: Float): List<Float> = KICKOFF_ARCS.map { arc ->
    val local = ((progress - arc.delay) / FILL_FRACTION).coerceIn(0f, 1f)
    arc.sweepDegrees * FastOutSlowInEasing.transform(local)
}
