package com.footballintelligence.feature.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.ScrollableTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.onClick
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.OfflineBanner
import com.footballintelligence.core.ui.RefreshableContent
import com.footballintelligence.core.ui.TeamCrest
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.home.resources.Res
import com.footballintelligence.feature.home.resources.cd_fixture
import com.footballintelligence.feature.home.resources.cd_fixture_predict
import com.footballintelligence.feature.home.resources.cd_league_tab
import com.footballintelligence.feature.home.resources.fixture_time_tbc
import com.footballintelligence.feature.home.resources.fixtures_empty
import com.footballintelligence.feature.home.resources.fixtures_versus
import com.footballintelligence.feature.home.resources.home_title
import org.jetbrains.compose.resources.stringResource

/** Home screen: upcoming fixtures by date, one tab per league; tapping one predicts it. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    uiState: HomeUiState,
    leagues: List<String>,
    selectedLeague: String,
    onSelectLeague: (String) -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
    isRefreshing: Boolean = false,
    onRefresh: () -> Unit = {},
    onFixtureClick: (FixtureRow) -> Unit = {},
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(Res.string.home_title)) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                ),
            )
        },
        modifier = modifier,
    ) { padding ->
        Column(Modifier.padding(padding)) {
            LeagueTabs(leagues, selectedLeague, onSelectLeague)
            when (uiState) {
                is HomeUiState.Loading -> LoadingView()
                is HomeUiState.Error -> ErrorView(
                    message = errorMessage(uiState.kind, uiState.message),
                    onRetry = onRetry,
                )
                is HomeUiState.Success -> RefreshableContent(
                    isRefreshing = isRefreshing,
                    onRefresh = onRefresh,
                ) {
                    Column {
                        OfflineBanner(uiState.savedAt)
                        FixtureList(uiState.days, selectedLeague, onFixtureClick)
                    }
                }
            }
        }
    }
}

@Composable
private fun LeagueTabs(leagues: List<String>, selected: String, onSelect: (String) -> Unit) {
    ScrollableTabRow(
        selectedTabIndex = leagues.indexOf(selected).coerceAtLeast(0),
        edgePadding = 8.dp,
    ) {
        leagues.forEach { league ->
            val description = stringResource(Res.string.cd_league_tab, league)
            Tab(
                selected = league == selected,
                onClick = { onSelect(league) },
                text = { Text(league) },
                modifier = Modifier.semantics { contentDescription = description },
            )
        }
    }
}

@Composable
private fun FixtureList(days: List<FixtureDay>, league: String, onFixtureClick: (FixtureRow) -> Unit) {
    if (days.isEmpty()) {
        Text(
            stringResource(Res.string.fixtures_empty, league),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth().padding(32.dp),
        )
        return
    }
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        days.forEach { day ->
            item(key = day.label) {
                Text(
                    day.label,
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(top = 8.dp).semantics { heading() },
                )
            }
            items(day.fixtures, key = { "${day.label}|${it.homeTeam}|${it.awayTeam}" }) {
                FixtureCard(it, onClick = { onFixtureClick(it) })
            }
        }
    }
}

@Composable
private fun FixtureCard(fixture: FixtureRow, onClick: () -> Unit) {
    val time = fixture.time ?: stringResource(Res.string.fixture_time_tbc)
    val description = stringResource(Res.string.cd_fixture, fixture.homeTeam, fixture.awayTeam, time)
    val clickLabel = stringResource(Res.string.cd_fixture_predict)
    Card(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .clearAndSetSemantics {
                contentDescription = description
                onClick(label = clickLabel) {
                    onClick()
                    true
                }
            },
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                time,
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.weight(0.22f),
            )
            Text(
                fixture.homeTeam,
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Medium,
                textAlign = TextAlign.End,
                modifier = Modifier.weight(0.35f),
            )
            TeamCrest(fixture.homeTeam)
            Text(
                stringResource(Res.string.fixtures_versus),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            TeamCrest(fixture.awayTeam)
            Text(
                fixture.awayTeam,
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.weight(0.35f),
            )
        }
    }
}
