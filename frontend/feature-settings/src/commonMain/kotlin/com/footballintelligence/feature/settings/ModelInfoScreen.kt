package com.footballintelligence.feature.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.model.ModelInfo
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.feature.settings.resources.Res
import com.footballintelligence.feature.settings.resources.dataset_version
import com.footballintelligence.feature.settings.resources.git_commit
import com.footballintelligence.feature.settings.resources.model_info_title
import com.footballintelligence.feature.settings.resources.model_version
import com.footballintelligence.feature.settings.resources.section_metrics
import com.footballintelligence.feature.settings.resources.section_registry
import com.footballintelligence.feature.settings.resources.training_timestamp
import org.jetbrains.compose.resources.stringResource

/** Displays model version, training metadata, and evaluation metrics. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ModelInfoScreen(
    uiState: ModelInfoUiState,
    onRetry: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(Res.string.model_info_title)) },
                navigationIcon = { BackButton(onClick = onBack) },
            )
        },
        modifier = modifier,
    ) { padding ->
        when (uiState) {
            is ModelInfoUiState.Loading -> LoadingView(Modifier.padding(padding))
            is ModelInfoUiState.Error -> ErrorView(
                message = uiState.message,
                onRetry = onRetry,
                modifier = Modifier.padding(padding),
            )
            is ModelInfoUiState.Success -> ModelInfoContent(
                info = uiState.info,
                modifier = Modifier.padding(padding),
            )
        }
    }
}

@Composable
private fun ModelInfoContent(info: ModelInfo, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        InfoCard(title = stringResource(Res.string.section_registry)) {
            InfoRow(stringResource(Res.string.model_version), info.modelVersion)
            InfoRow(stringResource(Res.string.dataset_version), info.datasetVersion)
            InfoRow(stringResource(Res.string.training_timestamp), info.trainingTimestamp.take(19).replace("T", " "))
            info.gitCommit?.let { commit ->
                InfoRow(stringResource(Res.string.git_commit), commit.take(8))
            }
        }
        if (info.metrics.isNotEmpty()) {
            InfoCard(title = stringResource(Res.string.section_metrics)) {
                info.metrics.entries.forEach { (key, value) ->
                    InfoRow(
                        label = key.replace('_', ' '),
                        value = "%.4f".format(value),
                    )
                }
            }
        }
    }
}

@Composable
private fun InfoCard(title: String, content: @Composable () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(title, style = MaterialTheme.typography.titleSmall)
            HorizontalDivider()
            content()
        }
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text(
            label,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(value, style = MaterialTheme.typography.bodyMedium)
    }
}
