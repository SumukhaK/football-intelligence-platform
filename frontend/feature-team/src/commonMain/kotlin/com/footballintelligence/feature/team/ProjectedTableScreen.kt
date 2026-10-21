package com.footballintelligence.feature.team

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.OfflineBanner
import com.footballintelligence.core.ui.appBarColors
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.table_guide
import com.footballintelligence.feature.team.resources.table_heading
import com.footballintelligence.feature.team.resources.table_scroll_hint
import com.footballintelligence.feature.team.resources.table_title
import org.jetbrains.compose.resources.stringResource

/** The sortable projected table, retaining the favourite team's identity and model ranks. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProjectedTableScreen(
    uiState: ProjectedTableUiState,
    onSort: (TableColumn) -> Unit,
    onRetry: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(Res.string.table_title)) },
                navigationIcon = { BackButton(onClick = onBack) },
                colors = appBarColors(),
            )
        },
        modifier = modifier,
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            when (val content = uiState.content) {
                is SeasonOutlookUiState.Loading -> LoadingView()
                is SeasonOutlookUiState.Error -> ErrorView(errorMessage(content.kind, content.message), onRetry)
                is SeasonOutlookUiState.Success -> {
                    OfflineBanner(content.savedAt)
                    ProjectedTable(content.outlook.table, uiState.sort, onSort)
                }
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun ProjectedTable(rows: List<TableRow>, sort: TableSort, onSort: (TableColumn) -> Unit) {
    val scroll = rememberScrollState()
    LazyColumn(contentPadding = PaddingValues(bottom = 24.dp), modifier = Modifier.fillMaxSize()) {
        item {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(stringResource(Res.string.table_heading), style = MaterialTheme.typography.headlineSmall)
                Text(
                    stringResource(Res.string.table_guide),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text(
                    stringResource(Res.string.table_scroll_hint),
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
            }
        }
        stickyHeader { TableHeader(sort, onSort, scroll) }
        itemsIndexed(rows, key = { _, row -> row.team }) { index, row -> ProjectedTeamRow(row, index, scroll) }
    }
}

@Composable
private fun TableHeader(sort: TableSort, onSort: (TableColumn) -> Unit, scroll: ScrollState) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.fillMaxWidth().background(MaterialTheme.colorScheme.surfaceVariant),
    ) {
        Row(Modifier.width(TABLE_IDENTITY_WIDTH)) {
            SortHeader(TableColumn.POSITION, sort, onSort, Modifier.width(TABLE_RANK_WIDTH))
            SortHeader(TableColumn.TEAM, sort, onSort, Modifier.weight(1f))
        }
        Row(Modifier.weight(1f).horizontalScroll(scroll)) {
            for (column in TABLE_METRIC_COLUMNS) {
                SortHeader(column, sort, onSort, Modifier.width(TABLE_METRIC_WIDTH))
            }
        }
    }
}
