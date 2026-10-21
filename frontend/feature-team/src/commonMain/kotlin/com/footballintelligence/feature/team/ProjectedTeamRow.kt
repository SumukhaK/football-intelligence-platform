package com.footballintelligence.feature.team

import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.TeamCrest
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.cd_table_row
import com.footballintelligence.feature.team.resources.outlook_percent
import com.footballintelligence.feature.team.resources.table_your_team
import org.jetbrains.compose.resources.stringResource

/** A fixed rank and team identity alongside horizontally scrollable metrics. */
@Composable
internal fun ProjectedTeamRow(row: TableRow, index: Int, scroll: ScrollState) {
    val description = stringResource(
        Res.string.cd_table_row,
        row.position,
        row.team,
        row.currentPoints,
        row.expectedPoints,
        row.titlePercent,
        row.topFourPercent,
        row.relegationPercent,
    )
    val background = when {
        row.isFavourite -> MaterialTheme.colorScheme.primaryContainer
        index % 2 == 0 -> MaterialTheme.colorScheme.surface
        else -> MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.35f)
    }
    val foreground = if (row.isFavourite) {
        MaterialTheme.colorScheme.onPrimaryContainer
    } else {
        MaterialTheme.colorScheme.onSurface
    }
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.fillMaxWidth().height(IntrinsicSize.Min).heightIn(min = 72.dp).background(background)
            .clearAndSetSemantics { contentDescription = description },
    ) {
        TeamIdentity(row, foreground, Modifier.width(TABLE_IDENTITY_WIDTH))
        Row(Modifier.weight(1f).horizontalScroll(scroll), verticalAlignment = Alignment.CenterVertically) {
            MetricCell("${row.currentPoints}", foreground)
            MetricCell("${row.expectedPoints}", foreground, bold = true)
            MetricCell(stringResource(Res.string.outlook_percent, row.titlePercent), foreground)
            MetricCell(stringResource(Res.string.outlook_percent, row.topFourPercent), foreground)
            MetricCell(stringResource(Res.string.outlook_percent, row.relegationPercent), foreground)
        }
    }
    HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
}

@Composable
private fun TeamIdentity(row: TableRow, foreground: Color, modifier: Modifier) {
    Row(modifier.fillMaxHeight(), verticalAlignment = Alignment.CenterVertically) {
        val accent = if (row.isFavourite) MaterialTheme.colorScheme.primary else Color.Transparent
        Box(Modifier.width(4.dp).fillMaxHeight().background(accent))
        Text(
            "${row.position}",
            style = MaterialTheme.typography.titleSmall,
            color = foreground,
            textAlign = TextAlign.Center,
            modifier = Modifier.width(TABLE_RANK_WIDTH - 4.dp),
        )
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.weight(1f).padding(vertical = 12.dp, horizontal = 4.dp),
        ) {
            TeamCrest(row.team, size = 28.dp)
            Column {
                Text(
                    row.team,
                    style = MaterialTheme.typography.bodyMedium,
                    color = foreground,
                    fontWeight = FontWeight.SemiBold,
                )
                if (row.isFavourite) {
                    Text(
                        stringResource(Res.string.table_your_team),
                        style = MaterialTheme.typography.labelSmall,
                        color = foreground,
                    )
                }
            }
        }
    }
}

@Composable
private fun MetricCell(text: String, color: Color, bold: Boolean = false) {
    Text(
        text,
        color = color,
        style = if (bold) MaterialTheme.typography.titleMedium else MaterialTheme.typography.bodyMedium,
        fontWeight = if (bold) FontWeight.Bold else FontWeight.Medium,
        textAlign = TextAlign.Center,
        modifier = Modifier.width(TABLE_METRIC_WIDTH).padding(horizontal = 8.dp, vertical = 12.dp),
    )
}
