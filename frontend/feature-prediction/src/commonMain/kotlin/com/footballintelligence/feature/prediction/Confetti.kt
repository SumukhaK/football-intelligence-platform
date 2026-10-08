package com.footballintelligence.feature.prediction

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.rotate
import kotlin.math.PI
import kotlin.math.sin
import kotlin.random.Random

/** One burst of confetti falling through its bounds, played once to celebrate a predicted win. */
@Composable
internal fun Confetti(modifier: Modifier = Modifier) {
    val scheme = MaterialTheme.colorScheme
    val colors = listOf(scheme.primary, scheme.secondary, scheme.tertiary, scheme.error, CONFETTI_GOLD)
    val pieces = remember { List(PIECE_COUNT) { ConfettiPiece.random(colors) } }
    val progress = remember { Animatable(0f) }
    LaunchedEffect(Unit) {
        progress.animateTo(1f, tween(DURATION_MS, easing = LinearEasing))
    }
    Canvas(modifier) {
        val t = progress.value
        if (t >= 1f) return@Canvas
        pieces.forEach { piece ->
            val sway = sin(t * 2 * PI.toFloat() * piece.sways) * SWAY_PX
            val center = Offset(piece.x * size.width + sway, (piece.start + t * piece.speed) * size.height)
            rotate(piece.spin * t, center) {
                drawRect(
                    color = piece.color.copy(alpha = 1f - t),
                    topLeft = center - Offset(PIECE_WIDTH_PX / 2, PIECE_HEIGHT_PX / 2),
                    size = Size(PIECE_WIDTH_PX, PIECE_HEIGHT_PX),
                )
            }
        }
    }
}

private class ConfettiPiece(
    val x: Float,
    val start: Float,
    val speed: Float,
    val sways: Float,
    val spin: Float,
    val color: Color,
) {
    companion object {
        fun random(colors: List<Color>) = ConfettiPiece(
            x = Random.nextFloat(),
            start = -Random.nextFloat() * MAX_START_ABOVE,
            speed = MIN_SPEED + Random.nextFloat() * SPEED_RANGE,
            sways = Random.nextFloat() * MAX_SWAYS,
            spin = (Random.nextFloat() - CENTRE) * MAX_SPIN_DEGREES,
            color = colors.random(),
        )
    }
}

private val CONFETTI_GOLD = Color(0xFFFFC107)
private const val PIECE_COUNT = 60
private const val DURATION_MS = 2_500
private const val SWAY_PX = 24f
private const val PIECE_WIDTH_PX = 18f
private const val PIECE_HEIGHT_PX = 10f
private const val MAX_START_ABOVE = 0.5f
private const val MIN_SPEED = 1.1f
private const val SPEED_RANGE = 0.6f
private const val MAX_SWAYS = 2f
private const val CENTRE = 0.5f
private const val MAX_SPIN_DEGREES = 1_440f
