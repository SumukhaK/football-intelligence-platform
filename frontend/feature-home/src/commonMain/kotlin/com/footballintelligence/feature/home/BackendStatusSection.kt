package com.footballintelligence.feature.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.model.HealthStatus
import com.footballintelligence.core.ui.StatusChip
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.home.resources.Res
import com.footballintelligence.feature.home.resources.api_version
import com.footballintelligence.feature.home.resources.assistant_offline_hint
import com.footballintelligence.feature.home.resources.backend_status
import com.footballintelligence.feature.home.resources.cd_assistant_offline
import com.footballintelligence.feature.home.resources.cd_assistant_online
import com.footballintelligence.feature.home.resources.cd_explainer_offline
import com.footballintelligence.feature.home.resources.cd_explainer_online
import com.footballintelligence.feature.home.resources.cd_prediction_api_offline
import com.footballintelligence.feature.home.resources.cd_prediction_api_online
import com.footballintelligence.feature.home.resources.retry
import com.footballintelligence.feature.home.resources.status_assistant
import com.footballintelligence.feature.home.resources.status_explainer
import com.footballintelligence.feature.home.resources.status_prediction_api
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.stringResource

/** Card showing which backend services are up, for the Settings screen. */
@Composable
fun BackendStatusSection(
    uiState: BackendStatusUiState,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(stringResource(Res.string.backend_status), style = MaterialTheme.typography.titleSmall)
            when (uiState) {
                is BackendStatusUiState.Loading -> CircularProgressIndicator()
                is BackendStatusUiState.Error -> {
                    Text(errorMessage(uiState.kind, uiState.message), style = MaterialTheme.typography.bodySmall)
                    TextButton(onClick = onRetry) { Text(stringResource(Res.string.retry)) }
                }
                is BackendStatusUiState.Success -> StatusChips(uiState.health)
            }
        }
    }
}

@Composable
private fun StatusChips(health: HealthStatus) {
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
    if (!health.assistantAvailable) {
        Text(
            stringResource(Res.string.assistant_offline_hint),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
    Text(
        text = stringResource(Res.string.api_version, health.version),
        style = MaterialTheme.typography.labelSmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
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
