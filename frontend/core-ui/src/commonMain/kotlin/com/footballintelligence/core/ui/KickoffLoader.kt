package com.footballintelligence.core.ui

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.ProgressBarRangeInfo
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.progressBarRangeInfo
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.resources.Res
import com.footballintelligence.core.ui.resources.cd_loading
import org.jetbrains.compose.resources.stringResource
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

private const val CYCLE_MS = 1600
private const val RING_WIDTH = 0.14f
private const val BALL_RADIUS = 0.26f
private const val PANEL_RADIUS = 0.11f
private const val PENTAGON_POINTS = 5
private val AWAY_AMBER = Color(0xFFFFB300)

/**
 * The app's loading indicator: home, draw and away arcs filling in around a ball,
 * the same animation as the launch screen. Use it wherever something is loading.
 */
@Composable
fun KickoffLoader(modifier: Modifier = Modifier, size: Dp = 56.dp) {
    val description = stringResource(Res.string.cd_loading)
    val progress by rememberInfiniteTransition(label = "kickoff").animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(CYCLE_MS, easing = LinearEasing), RepeatMode.Restart),
        label = "kickoff-progress",
    )
    val colors = listOf(
        MaterialTheme.colorScheme.primary,
        MaterialTheme.colorScheme.secondary.copy(alpha = 0.55f),
        AWAY_AMBER,
    )
    val ball = MaterialTheme.colorScheme.surfaceVariant
    val panel = MaterialTheme.colorScheme.primary
    Canvas(
        modifier = modifier
            .size(size)
            .semantics {
                contentDescription = description
                progressBarRangeInfo = ProgressBarRangeInfo.Indeterminate
            },
    ) {
        drawRing(kickoffSweeps(progress), colors)
        drawBall(ball, panel)
    }
}

private fun DrawScope.drawRing(sweeps: List<Float>, colors: List<Color>) {
    val stroke = this.size.minDimension * RING_WIDTH
    val inset = stroke / 2
    val diameter = this.size.minDimension - stroke
    KICKOFF_ARCS.forEachIndexed { i, arc ->
        drawArc(
            color = colors[i],
            startAngle = arc.startDegrees - 90f,
            sweepAngle = sweeps[i],
            useCenter = false,
            topLeft = Offset(inset, inset),
            size = Size(diameter, diameter),
            style = Stroke(width = stroke, cap = StrokeCap.Butt),
        )
    }
}

private fun DrawScope.drawBall(ball: Color, panel: Color) {
    val d = this.size.minDimension
    drawCircle(color = ball, radius = d * BALL_RADIUS, center = center)
    val r = d * PANEL_RADIUS
    val pentagon = Path().apply {
        repeat(PENTAGON_POINTS) { i ->
            val angle = -PI / 2 + i * 2 * PI / PENTAGON_POINTS
            val point = Offset(center.x + r * cos(angle).toFloat(), center.y + r * sin(angle).toFloat())
            if (i == 0) moveTo(point.x, point.y) else lineTo(point.x, point.y)
        }
        close()
    }
    drawPath(pentagon, color = panel)
}
