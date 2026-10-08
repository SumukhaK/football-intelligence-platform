package com.footballintelligence.feature.team

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.OfflineBanner
import com.footballintelligence.core.ui.RefreshableContent
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.my_team_title
import com.footballintelligence.feature.team.resources.next_match_none
import org.jetbrains.compose.resources.stringResource

/**
 * My Team: the favourite team's next match, then its season outlook, which
 * opens the projected table. [actions] go at the top right of the app bar.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MyTeamScreen(
    uiState: MyTeamUiState,
    outlookState: SeasonOutlookUiState,
    onRetry: () -> Unit,
    onOpenTable: () -> Unit,
    modifier: Modifier = Modifier,
    isRefreshing: Boolean = false,
    onRefresh: () -> Unit = {},
    actions: @Composable RowScope.() -> Unit = {},
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(Res.string.my_team_title)) },
                actions = actions,
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    actionIconContentColor = MaterialTheme.colorScheme.onPrimary,
                ),
            )
        },
        modifier = modifier,
    ) { padding ->
        Column(Modifier.padding(padding)) {
            when (uiState) {
                is MyTeamUiState.Loading -> LoadingView()
                is MyTeamUiState.Error -> ErrorView(
                    message = errorMessage(uiState.kind, uiState.message),
                    onRetry = onRetry,
                )
                is MyTeamUiState.Success -> Refreshable(uiState.savedAt, isRefreshing, onRefresh) {
                    NextMatchCard(uiState.match)
                    SeasonOutlookSection(outlookState, onOpenTable, onRetry)
                }
                is MyTeamUiState.NoUpcomingMatch -> Refreshable(uiState.savedAt, isRefreshing, onRefresh) {
                    Text(
                        stringResource(Res.string.next_match_none, uiState.team),
                        style = MaterialTheme.typography.bodyMedium,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth().padding(16.dp),
                    )
                    SeasonOutlookSection(outlookState, onOpenTable, onRetry)
                }
            }
        }
    }
}

@Composable
private fun Refreshable(
    savedAt: String?,
    isRefreshing: Boolean,
    onRefresh: () -> Unit,
    content: @Composable () -> Unit,
) {
    RefreshableContent(isRefreshing = isRefreshing, onRefresh = onRefresh) {
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
            OfflineBanner(savedAt)
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                content()
            }
        }
    }
}
