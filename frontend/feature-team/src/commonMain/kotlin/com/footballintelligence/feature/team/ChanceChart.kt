package com.footballintelligence.feature.team

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.unit.dp
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.cd_outlook_chart
import com.footballintelligence.feature.team.resources.outlook_chart_axis
import com.footballintelligence.feature.team.resources.outlook_relegation
import com.footballintelligence.feature.team.resources.outlook_title
import com.footballintelligence.feature.team.resources.outlook_top_four
import org.jetbrains.compose.resources.stringResource
import kotlin.math.roundToInt

/**
 * The title, top-four and relegation chances through the season, one point
 * per week, on a 0 to 100% scale. Read out as a sentence from first to last.
 */
@Composable
fun ChanceChart(history: List<ChancePoint>, modifier: Modifier = Modifier) {
    if (history.isEmpty()) return
    val colors = chanceColors()
    val first = history.first()
    val last = history.last()
    val description = stringResource(
        Res.string.cd_outlook_chart,
        percent(first.title),
        percent(last.title),
        percent(first.topFour),
        percent(last.topFour),
        percent(first.relegation),
        percent(last.relegation),
    )
    val grid = MaterialTheme.colorScheme.outlineVariant
    Column(
        verticalArrangement = Arrangement.spacedBy(6.dp),
        modifier = modifier.clearAndSetSemantics { contentDescription = description },
    ) {
        Canvas(Modifier.fillMaxWidth().height(CHART_HEIGHT)) {
            drawGrid(grid)
            drawChance(history.map { it.title }, colors.title)
            drawChance(history.map { it.topFour }, colors.topFour)
            drawChance(history.map { it.relegation }, colors.relegation)
        }
        Text(
            stringResource(Res.string.outlook_chart_axis, first.played, last.played),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Legend(stringResource(Res.string.outlook_title), colors.title)
            Legend(stringResource(Res.string.outlook_top_four), colors.topFour)
            Legend(stringResource(Res.string.outlook_relegation), colors.relegation)
        }
    }
}

/** One colour per chance, shared by the chart and the chance tiles. */
internal data class ChanceColors(val title: Color, val topFour: Color, val relegation: Color)

@Composable
internal fun chanceColors() = ChanceColors(
    title = MaterialTheme.colorScheme.primary,
    topFour = MaterialTheme.colorScheme.tertiary,
    relegation = MaterialTheme.colorScheme.error,
)

@Composable
private fun Legend(label: String, color: Color) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
        Box(Modifier.size(8.dp).background(color, CircleShape))
        Text(label, style = MaterialTheme.typography.labelSmall)
    }
}

private fun DrawScope.drawGrid(color: Color) {
    GRID_LEVELS.forEach { level ->
        val y = size.height * (1f - level)
        drawLine(color, Offset(0f, y), Offset(size.width, y), strokeWidth = 1.dp.toPx())
    }
}

/** A line through [values] (0 to 1), or a single dot when there is one point. */
private fun DrawScope.drawChance(values: List<Float>, color: Color) {
    val step = if (values.size > 1) size.width / (values.size - 1) else 0f
    val points = values.mapIndexed { i, v -> Offset(i * step, size.height * (1f - v.coerceIn(0f, 1f))) }
    if (points.size == 1) {
        drawCircle(color, radius = 3.dp.toPx(), center = points.first())
        return
    }
    val path = Path().apply {
        moveTo(points.first().x, points.first().y)
        points.drop(1).forEach { lineTo(it.x, it.y) }
    }
    drawPath(path, color, style = Stroke(width = 2.5.dp.toPx()))
}

private fun percent(chance: Float): Int = (chance * PERCENT).roundToInt()

private const val PERCENT = 100

// Lines at 0, 50% and 100%.
private val GRID_LEVELS = listOf(0f, 0.5f, 1f)
private val CHART_HEIGHT = 120.dp
