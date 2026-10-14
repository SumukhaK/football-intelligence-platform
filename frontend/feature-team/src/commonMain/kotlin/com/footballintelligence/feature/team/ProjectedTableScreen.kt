package com.footballintelligence.feature.team

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.OfflineBanner
import com.footballintelligence.core.ui.TeamCrest
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.cd_table_row
import com.footballintelligence.feature.team.resources.table_points_now
import com.footballintelligence.feature.team.resources.table_points_projected
import com.footballintelligence.feature.team.resources.table_position
import com.footballintelligence.feature.team.resources.table_relegation
import com.footballintelligence.feature.team.resources.table_team
import com.footballintelligence.feature.team.resources.table_title
import com.footballintelligence.feature.team.resources.table_title_chance
import com.footballintelligence.feature.team.resources.table_top_four
import org.jetbrains.compose.resources.stringResource

/** The projected league table behind the Season outlook, with the favourite team highlighted. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProjectedTableScreen(
    uiState: SeasonOutlookUiState,
    onRetry: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(Res.string.table_title)) },
                navigationIcon = { BackButton(onClick = onBack) },
            )
        },
        modifier = modifier,
    ) { padding ->
        Column(Modifier.padding(padding)) {
            when (uiState) {
                is SeasonOutlookUiState.Loading -> LoadingView()
                is SeasonOutlookUiState.Error -> ErrorView(errorMessage(uiState.kind, uiState.message), onRetry)
                is SeasonOutlookUiState.Success -> {
                    OfflineBanner(uiState.savedAt)
                    Table(uiState.outlook.table)
                }
            }
        }
    }
}

@Composable
private fun Table(rows: List<TableRow>) {
    LazyColumn(contentPadding = PaddingValues(vertical = 8.dp)) {
        item {
            TableLine(highlight = false) {
                Cell(stringResource(Res.string.table_position), POSITION_WIDTH, bold = true)
                Text(
                    stringResource(Res.string.table_team),
                    style = MaterialTheme.typography.labelMedium,
                    modifier = Modifier.weight(1f).padding(start = TEAM_GAP),
                )
                Cell(stringResource(Res.string.table_points_now), NUMBER_WIDTH, bold = true)
                Cell(stringResource(Res.string.table_points_projected), NUMBER_WIDTH, bold = true)
                Cell(stringResource(Res.string.table_title_chance), NUMBER_WIDTH, bold = true)
                Cell(stringResource(Res.string.table_top_four), NUMBER_WIDTH, bold = true)
                Cell(stringResource(Res.string.table_relegation), NUMBER_WIDTH, bold = true)
            }
        }
        items(rows, key = { it.team }) { row -> TeamLine(row) }
    }
}

@Composable
private fun TeamLine(row: TableRow) {
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
    TableLine(highlight = row.isFavourite, Modifier.clearAndSetSemantics { contentDescription = description }) {
        Cell("${row.position}", POSITION_WIDTH, bold = row.isFavourite)
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.weight(1f).padding(start = TEAM_GAP),
        ) {
            TeamCrest(row.team, size = 20.dp)
            Text(
                row.team,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = if (row.isFavourite) FontWeight.Bold else FontWeight.Normal,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
        Cell("${row.currentPoints}", NUMBER_WIDTH, bold = row.isFavourite)
        Cell("${row.expectedPoints}", NUMBER_WIDTH, bold = true)
        Cell("${row.titlePercent}%", NUMBER_WIDTH, bold = row.isFavourite)
        Cell("${row.topFourPercent}%", NUMBER_WIDTH, bold = row.isFavourite)
        Cell("${row.relegationPercent}%", NUMBER_WIDTH, bold = row.isFavourite)
    }
}

@Composable
private fun TableLine(highlight: Boolean, modifier: Modifier = Modifier, content: @Composable RowScope.() -> Unit) {
    val background = if (highlight) MaterialTheme.colorScheme.primaryContainer else Color.Transparent
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = modifier
            .fillMaxWidth()
            .background(background)
            .padding(horizontal = 12.dp, vertical = 10.dp),
        content = content,
    )
}

@Composable
private fun Cell(text: String, width: Dp, bold: Boolean) {
    Text(
        text,
        style = MaterialTheme.typography.labelMedium,
        fontWeight = if (bold) FontWeight.Bold else FontWeight.Normal,
        textAlign = TextAlign.End,
        modifier = Modifier.width(width),
    )
}

private val POSITION_WIDTH = 24.dp
private val NUMBER_WIDTH = 44.dp
private val TEAM_GAP = 10.dp
