package com.footballintelligence.core.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.resources.Res
import com.footballintelligence.core.ui.resources.cd_outcome_bar
import com.footballintelligence.core.ui.resources.outcome_bar_draw
import com.footballintelligence.core.ui.resources.outcome_bar_note
import com.footballintelligence.core.ui.resources.outcome_bar_percent
import org.jetbrains.compose.resources.stringResource

/**
 * Home win, draw and away win as one bar with a crest at each end (the crest
 * names the side, so its percentage never gets cut off), and a note
 * that the pick adds up every scoreline, so a 1-1 top score next to a win
 * pick does not read as a contradiction.
 */
@Composable
fun OutcomeBar(homeTeam: String, awayTeam: String, split: OutcomeSplit, modifier: Modifier = Modifier) {
    val description = stringResource(Res.string.cd_outcome_bar, homeTeam, split.home, split.draw, awayTeam, split.away)
    Column(modifier, verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Row(
            Modifier.fillMaxWidth().clearAndSetSemantics { contentDescription = description },
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            TeamCrest(homeTeam, size = 28.dp)
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(Modifier.fillMaxWidth().height(BAR_HEIGHT).clip(RoundedCornerShape(BAR_HEIGHT / 2))) {
                    Segment(split.home, MaterialTheme.colorScheme.primary)
                    Segment(split.draw, MaterialTheme.colorScheme.outlineVariant)
                    Segment(split.away, MaterialTheme.colorScheme.tertiary)
                }
                Row(Modifier.fillMaxWidth()) {
                    Label(stringResource(Res.string.outcome_bar_percent, split.home), TextAlign.Start)
                    Label(stringResource(Res.string.outcome_bar_draw, split.draw), TextAlign.Center)
                    Label(stringResource(Res.string.outcome_bar_percent, split.away), TextAlign.End)
                }
            }
            TeamCrest(awayTeam, size = 28.dp)
        }
        Text(
            stringResource(Res.string.outcome_bar_note),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun RowScope.Segment(percent: Int, color: Color) {
    // A zero chance still gets a sliver so all three parts stay visible.
    Box(Modifier.weight(percent.coerceAtLeast(1).toFloat()).fillMaxHeight().background(color))
}

@Composable
private fun RowScope.Label(text: String, align: TextAlign) {
    Text(
        text,
        style = MaterialTheme.typography.labelMedium,
        textAlign = align,
        maxLines = 1,
        overflow = TextOverflow.Ellipsis,
        modifier = Modifier.weight(1f),
    )
}

private val BAR_HEIGHT = 12.dp
