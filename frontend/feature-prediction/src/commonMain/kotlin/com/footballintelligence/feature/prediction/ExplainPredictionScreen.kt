package com.footballintelligence.feature.prediction

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.model.ExplanationResult
import com.footballintelligence.core.model.FeatureContribution
import com.footballintelligence.core.model.toOutcomeLabel
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import kotlin.math.roundToInt

/** Displays SHAP feature contributions explaining the prediction. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ExplainPredictionScreen(
    uiState: ExplanationUiState,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Explanation") },
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
            is ExplanationUiState.Loading -> LoadingView(Modifier.padding(padding))
            is ExplanationUiState.Error -> ErrorView(
                message = uiState.message,
                modifier = Modifier.padding(padding),
            )
            is ExplanationUiState.Idle -> ErrorView(
                message = "No explanation loaded.",
                modifier = Modifier.padding(padding),
            )
            is ExplanationUiState.Success -> ExplanationContent(
                result = uiState.result,
                modifier = Modifier.padding(padding),
            )
        }
    }
}

@Composable
private fun ExplanationContent(
    result: ExplanationResult,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Card(
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer,
            ),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                Text(
                    "${result.homeTeam} vs ${result.awayTeam}",
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    "Prediction: ${result.predictedResult.toOutcomeLabel(result.homeTeam, result.awayTeam)}",
                    style = MaterialTheme.typography.bodyLarge,
                )
                Text(
                    "Confidence: ${(result.confidence * 100).roundToInt()}%",
                    style = MaterialTheme.typography.bodyMedium,
                )
                Text(
                    "Dataset: ${result.datasetVersion} · Model: ${result.modelVersion}",
                    style = MaterialTheme.typography.labelSmall,
                )
            }
        }

        FeatureSection(
            title = "Top Positive Contributors",
            subtitle = "Features that pushed toward this prediction",
            features = result.topPositiveFeatures,
            isPositive = true,
        )

        FeatureSection(
            title = "Top Negative Contributors",
            subtitle = "Features that pushed against this prediction",
            features = result.topNegativeFeatures,
            isPositive = false,
        )
    }
}

@Composable
private fun FeatureSection(
    title: String,
    subtitle: String,
    features: List<FeatureContribution>,
    isPositive: Boolean,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(title, style = MaterialTheme.typography.titleSmall)
            Text(
                subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            HorizontalDivider()
            features.forEach { feature ->
                FeatureRow(feature = feature, isPositive = isPositive)
            }
            if (features.isEmpty()) {
                Text(
                    "No features in this category.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun FeatureRow(feature: FeatureContribution, isPositive: Boolean) {
    val color = if (isPositive) Color(0xFF2E7D32) else Color(0xFFC62828)
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                feature.featureName.replace('_', ' '),
                style = MaterialTheme.typography.bodyMedium,
            )
            Text(
                "value: ${"%.3f".format(feature.featureValue)}",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Text(
            text = "${"%.4f".format(feature.shapValue)}",
            style = MaterialTheme.typography.bodyMedium,
            color = color,
        )
    }
}
