package com.footballintelligence.feature.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Psychology
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.SportsSoccer
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ElevatedButton
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.model.HealthStatus
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.StatusChip
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.home.resources.Res
import com.footballintelligence.feature.home.resources.api_version
import com.footballintelligence.feature.home.resources.assistant_offline_hint
import com.footballintelligence.feature.home.resources.backend_status
import com.footballintelligence.feature.home.resources.card_assistant_action
import com.footballintelligence.feature.home.resources.card_assistant_description
import com.footballintelligence.feature.home.resources.card_assistant_title
import com.footballintelligence.feature.home.resources.card_prediction_action
import com.footballintelligence.feature.home.resources.card_prediction_description
import com.footballintelligence.feature.home.resources.card_prediction_title
import com.footballintelligence.feature.home.resources.card_settings_action
import com.footballintelligence.feature.home.resources.card_settings_description
import com.footballintelligence.feature.home.resources.card_settings_title
import com.footballintelligence.feature.home.resources.cd_assistant_offline
import com.footballintelligence.feature.home.resources.cd_assistant_online
import com.footballintelligence.feature.home.resources.cd_explainer_offline
import com.footballintelligence.feature.home.resources.cd_explainer_online
import com.footballintelligence.feature.home.resources.cd_prediction_api_offline
import com.footballintelligence.feature.home.resources.cd_prediction_api_online
import com.footballintelligence.feature.home.resources.home_title
import com.footballintelligence.feature.home.resources.status_assistant
import com.footballintelligence.feature.home.resources.status_explainer
import com.footballintelligence.feature.home.resources.status_prediction_api
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.stringResource

/** Home screen: shows backend status and navigation cards. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    uiState: HomeUiState,
    onPredictClick: () -> Unit,
    onAssistantClick: () -> Unit,
    onSettingsClick: () -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
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
        when (uiState) {
            is HomeUiState.Loading -> LoadingView(Modifier.padding(padding))
            is HomeUiState.Error -> ErrorView(
                message = errorMessage(uiState.kind, uiState.message),
                onRetry = onRetry,
                modifier = Modifier.padding(padding),
            )
            is HomeUiState.Success -> HomeContent(
                health = uiState.health,
                onPredictClick = onPredictClick,
                onAssistantClick = onAssistantClick,
                onSettingsClick = onSettingsClick,
                modifier = Modifier.padding(padding),
            )
        }
    }
}

@Composable
private fun HomeContent(
    health: HealthStatus,
    onPredictClick: () -> Unit,
    onAssistantClick: () -> Unit,
    onSettingsClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        FeatureCard(
            icon = Icons.Default.SportsSoccer,
            title = stringResource(Res.string.card_prediction_title),
            description = stringResource(Res.string.card_prediction_description),
            enabled = health.modelLoaded,
            buttonLabel = stringResource(Res.string.card_prediction_action),
            onClick = onPredictClick,
        )
        FeatureCard(
            icon = Icons.Default.Psychology,
            title = stringResource(Res.string.card_assistant_title),
            description = stringResource(Res.string.card_assistant_description),
            enabled = health.assistantAvailable,
            buttonLabel = stringResource(Res.string.card_assistant_action),
            onClick = onAssistantClick,
            disabledHint = stringResource(Res.string.assistant_offline_hint),
        )
        FeatureCard(
            icon = Icons.Default.Settings,
            title = stringResource(Res.string.card_settings_title),
            description = stringResource(Res.string.card_settings_description),
            enabled = true,
            buttonLabel = stringResource(Res.string.card_settings_action),
            onClick = onSettingsClick,
        )
        BackendStatusCard(health)
    }
}

@Composable
private fun BackendStatusCard(health: HealthStatus) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
        ),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(stringResource(Res.string.backend_status), style = MaterialTheme.typography.titleSmall)
            BackendStatusChip(
                label = Res.string.status_prediction_api,
                available = health.modelLoaded,
                onlineDescription = Res.string.cd_prediction_api_online,
                offlineDescription = Res.string.cd_prediction_api_offline,
            )
            BackendStatusChip(
                label = Res.string.status_explainer,
                available = health.explainabilityAvailable,
                onlineDescription = Res.string.cd_explainer_online,
                offlineDescription = Res.string.cd_explainer_offline,
            )
            BackendStatusChip(
                label = Res.string.status_assistant,
                available = health.assistantAvailable,
                onlineDescription = Res.string.cd_assistant_online,
                offlineDescription = Res.string.cd_assistant_offline,
            )
            Text(
                text = stringResource(Res.string.api_version, health.version),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun BackendStatusChip(
    label: StringResource,
    available: Boolean,
    onlineDescription: StringResource,
    offlineDescription: StringResource,
) {
    val description = stringResource(if (available) onlineDescription else offlineDescription)
    StatusChip(
        label = stringResource(label),
        available = available,
        modifier = Modifier.semantics { contentDescription = description },
    )
}

@Composable
private fun FeatureCard(
    icon: ImageVector,
    title: String,
    description: String,
    enabled: Boolean,
    buttonLabel: String,
    onClick: () -> Unit,
    disabledHint: String? = null,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
            )
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(
                description,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (!enabled && disabledHint != null) {
                Text(
                    disabledHint,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            ElevatedButton(
                onClick = onClick,
                enabled = enabled,
                modifier = Modifier.align(Alignment.End),
            ) {
                Text(buttonLabel)
            }
        }
    }
}
