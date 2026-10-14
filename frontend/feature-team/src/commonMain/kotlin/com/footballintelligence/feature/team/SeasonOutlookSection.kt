package com.footballintelligence.feature.team

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.KickoffLoader
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.cd_open_table
import com.footballintelligence.feature.team.resources.cd_outlook_tile
import com.footballintelligence.feature.team.resources.outlook_attack
import com.footballintelligence.feature.team.resources.outlook_chart_heading
import com.footballintelligence.feature.team.resources.outlook_chart_note
import com.footballintelligence.feature.team.resources.outlook_defence
import com.footballintelligence.feature.team.resources.outlook_heading
import com.footballintelligence.feature.team.resources.outlook_open_table
import com.footballintelligence.feature.team.resources.outlook_percent
import com.footballintelligence.feature.team.resources.outlook_points_now
import com.footballintelligence.feature.team.resources.outlook_projection
import com.footballintelligence.feature.team.resources.outlook_relegation
import com.footballintelligence.feature.team.resources.outlook_retry
import com.footballintelligence.feature.team.resources.outlook_strength_heading
import com.footballintelligence.feature.team.resources.outlook_times
import com.footballintelligence.feature.team.resources.outlook_title
import com.footballintelligence.feature.team.resources.outlook_top_four
import org.jetbrains.compose.resources.stringResource
import kotlin.math.roundToInt

/** "Season outlook": projected finish, chances, their history and strengths. Tap for the table. */
@Composable
fun SeasonOutlookSection(
    uiState: SeasonOutlookUiState,
    onOpenTable: () -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val description = stringResource(Res.string.cd_open_table)
    Card(
        onClick = onOpenTable,
        enabled = uiState is SeasonOutlookUiState.Success,
        colors = CardDefaults.cardColors(),
        modifier = modifier.fillMaxWidth().semantics { contentDescription = description },
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(
                stringResource(Res.string.outlook_heading),
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.semantics { heading() },
            )
            when (uiState) {
                is SeasonOutlookUiState.Loading -> Box(Modifier.fillMaxWidth(), Alignment.Center) {
                    KickoffLoader(size = 40.dp)
                }
                is SeasonOutlookUiState.Error -> OutlookError(errorMessage(uiState.kind, uiState.message), onRetry)
                is SeasonOutlookUiState.Success -> OutlookContent(uiState.outlook)
            }
        }
    }
}

@Composable
private fun ColumnScope.OutlookContent(outlook: SeasonOutlook) {
    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text(
            stringResource(Res.string.outlook_projection, outlook.position, outlook.expectedPoints),
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
        )
        Text(
            stringResource(Res.string.outlook_points_now, outlook.currentPoints),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
    val colors = chanceColors()
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        val tile = Modifier.weight(1f)
        ChanceTile(stringResource(Res.string.outlook_title), outlook.titlePercent, colors.title, tile)
        ChanceTile(stringResource(Res.string.outlook_top_four), outlook.topFourPercent, colors.topFour, tile)
        ChanceTile(
            stringResource(Res.string.outlook_relegation),
            outlook.relegationPercent,
            colors.relegation,
            tile,
        )
    }
    HorizontalDivider()
    Text(stringResource(Res.string.outlook_chart_heading), style = MaterialTheme.typography.titleSmall)
    ChanceChart(outlook.history)
    Text(
        stringResource(Res.string.outlook_chart_note),
        style = MaterialTheme.typography.labelSmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
    HorizontalDivider()
    Text(stringResource(Res.string.outlook_strength_heading), style = MaterialTheme.typography.titleSmall)
    StrengthBar(stringResource(Res.string.outlook_attack), outlook.attack)
    StrengthBar(stringResource(Res.string.outlook_defence), outlook.defence)
    Text(
        stringResource(Res.string.outlook_open_table),
        style = MaterialTheme.typography.labelLarge,
        color = MaterialTheme.colorScheme.primary,
        modifier = Modifier.align(Alignment.End),
    )
}

@Composable
private fun ChanceTile(label: String, percent: Int, color: Color, modifier: Modifier) {
    val description = stringResource(Res.string.cd_outlook_tile, label, percent)
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        modifier = modifier.clearAndSetSemantics { contentDescription = description },
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
        ) {
            Text(
                stringResource(Res.string.outlook_percent, percent),
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = color,
            )
            Text(label, style = MaterialTheme.typography.labelMedium)
        }
    }
}

/** A bar where the middle is a league-average side, with the multiple beside it. */
@Composable
private fun StrengthBar(label: String, value: Double) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(label, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.width(LABEL_WIDTH))
        LinearProgressIndicator(
            progress = { (value / STRENGTH_SCALE).toFloat().coerceIn(0f, 1f) },
            modifier = Modifier.weight(1f),
        )
        Text(stringResource(Res.string.outlook_times, twoDecimals(value)), style = MaterialTheme.typography.labelLarge)
    }
}

@Composable
private fun OutlookError(message: String, onRetry: () -> Unit) {
    Text(message, style = MaterialTheme.typography.bodyMedium)
    TextButton(onClick = onRetry) { Text(stringResource(Res.string.outlook_retry)) }
}

/** A number such as 1.23. */
internal fun twoDecimals(value: Double): String {
    val hundredths = (value * HUNDRED).roundToInt()
    return "${hundredths / HUNDRED}.${(hundredths % HUNDRED).toString().padStart(2, '0')}"
}

private const val HUNDRED = 100

// Twice a league-average side fills the bar, so average sits in the middle.
private const val STRENGTH_SCALE = 2.0
private val LABEL_WIDTH = 120.dp
