package com.footballintelligence.feature.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.model.ModelInfo
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView

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
                title = { Text("Model Information") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
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
        InfoCard(title = "Registry") {
            InfoRow("Model Version", info.modelVersion)
            InfoRow("Dataset Version", info.datasetVersion)
            InfoRow("Training Timestamp", info.trainingTimestamp.take(19).replace("T", " "))
            info.gitCommit?.let { commit ->
                InfoRow("Git Commit", commit.take(8))
            }
        }
        if (info.metrics.isNotEmpty()) {
            InfoCard(title = "Evaluation Metrics") {
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
