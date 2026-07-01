package com.footballintelligence.feature.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Psychology
import androidx.compose.material.icons.filled.QueryStats
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
                title = { Text("Football Intelligence") },
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
                message = uiState.message,
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
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        BackendStatusCard(health)
        Spacer(Modifier.height(4.dp))
        FeatureCard(
            icon = Icons.Default.SportsSoccer,
            title = "Match Prediction",
            description = "Predict Premier League match outcomes using the XGBoost model with SHAP explanations.",
            enabled = health.modelLoaded,
            buttonLabel = "Predict a Match",
            onClick = onPredictClick,
        )
        FeatureCard(
            icon = Icons.Default.Psychology,
            title = "AI Assistant",
            description = "Ask questions about the model, predictions, and football analytics.",
            enabled = health.assistantAvailable,
            buttonLabel = "Open Assistant",
            onClick = onAssistantClick,
        )
        FeatureCard(
            icon = Icons.Default.Settings,
            title = "Settings & Model Info",
            description = "View model details, metrics, and configure the app.",
            enabled = true,
            buttonLabel = "Open Settings",
            onClick = onSettingsClick,
        )
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
            Text("Backend Status", style = MaterialTheme.typography.titleSmall)
            StatusChip(
                label = "Prediction API",
                available = health.modelLoaded,
                modifier = Modifier.semantics {
                    contentDescription = if (health.modelLoaded) "Prediction API online" else "Prediction API offline"
                },
            )
            StatusChip(
                label = "SHAP Explainer",
                available = health.explainabilityAvailable,
                modifier = Modifier.semantics {
                    contentDescription = if (health.explainabilityAvailable) "Explainer online" else "Explainer offline"
                },
            )
            StatusChip(
                label = "AI Assistant",
                available = health.assistantAvailable,
                modifier = Modifier.semantics {
                    contentDescription = if (health.assistantAvailable) "Assistant online" else "Assistant offline"
                },
            )
            Text(
                text = "API v${health.version}",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun FeatureCard(
    icon: ImageVector,
    title: String,
    description: String,
    enabled: Boolean,
    buttonLabel: String,
    onClick: () -> Unit,
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
