package com.footballintelligence.feature.prediction

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
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
import com.footballintelligence.core.model.Impact
import com.footballintelligence.core.model.impact
import com.footballintelligence.core.model.label
import com.footballintelligence.core.model.valueText
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.prediction.resources.Res
import com.footballintelligence.feature.prediction.resources.against_subtitle
import com.footballintelligence.feature.prediction.resources.against_title
import com.footballintelligence.feature.prediction.resources.confidence
import com.footballintelligence.feature.prediction.resources.dataset_and_model
import com.footballintelligence.feature.prediction.resources.explanation_title
import com.footballintelligence.feature.prediction.resources.fixture
import com.footballintelligence.feature.prediction.resources.impact_big
import com.footballintelligence.feature.prediction.resources.impact_medium
import com.footballintelligence.feature.prediction.resources.impact_small
import com.footballintelligence.feature.prediction.resources.leans_subtitle
import com.footballintelligence.feature.prediction.resources.leans_title
import com.footballintelligence.feature.prediction.resources.no_explanation
import com.footballintelligence.feature.prediction.resources.nothing_notable
import com.footballintelligence.feature.prediction.resources.prediction_label
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.stringResource
import kotlin.math.abs

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
                title = { Text(stringResource(Res.string.explanation_title)) },
                navigationIcon = { BackButton(onClick = onBack) },
            )
        },
        modifier = modifier,
    ) { padding ->
        when (uiState) {
            is ExplanationUiState.Loading -> LoadingView(Modifier.padding(padding))
            is ExplanationUiState.Error -> ErrorView(
                message = errorMessage(uiState.kind, uiState.message),
                modifier = Modifier.padding(padding),
            )
            is ExplanationUiState.Idle -> ErrorView(
                message = stringResource(Res.string.no_explanation),
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
                if (result.competition.isNotBlank()) {
                    Text(result.competition, style = MaterialTheme.typography.labelMedium)
                }
                Text(
                    stringResource(Res.string.fixture, result.homeTeam, result.awayTeam),
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    stringResource(
                        Res.string.prediction_label,
                        outcomeLabel(result.predictedResult, result.homeTeam, result.awayTeam),
                    ),
                    style = MaterialTheme.typography.bodyLarge,
                )
                Text(
                    stringResource(Res.string.confidence, percentOf(result.confidence)),
                    style = MaterialTheme.typography.bodyMedium,
                )
                Text(
                    stringResource(Res.string.dataset_and_model, result.datasetVersion, result.modelVersion),
                    style = MaterialTheme.typography.labelSmall,
                )
            }
        }

        val strongest = result.allContributions.maxOfOrNull { abs(it.shapValue) } ?: 0.0

        FeatureSection(
            title = stringResource(Res.string.leans_title),
            subtitle = stringResource(Res.string.leans_subtitle),
            features = result.topPositiveFeatures,
            strongest = strongest,
            isPositive = true,
        )

        FeatureSection(
            title = stringResource(Res.string.against_title),
            subtitle = stringResource(Res.string.against_subtitle),
            features = result.topNegativeFeatures,
            strongest = strongest,
            isPositive = false,
        )
    }
}

@Composable
private fun FeatureSection(
    title: String,
    subtitle: String,
    features: List<FeatureContribution>,
    strongest: Double,
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
                FeatureRow(feature = feature, strongest = strongest, isPositive = isPositive)
            }
            if (features.isEmpty()) {
                Text(
                    stringResource(Res.string.nothing_notable),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun FeatureRow(feature: FeatureContribution, strongest: Double, isPositive: Boolean) {
    val color = if (isPositive) Color(0xFF2E7D32) else Color(0xFFC62828)
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                feature.label(),
                style = MaterialTheme.typography.bodyMedium,
            )
            Text(
                feature.valueText(),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Text(
            text = stringResource(impactText(feature.impact(strongest))),
            style = MaterialTheme.typography.bodyMedium,
            color = color,
        )
    }
}

private fun impactText(impact: Impact): StringResource = when (impact) {
    Impact.BIG -> Res.string.impact_big
    Impact.MEDIUM -> Res.string.impact_medium
    Impact.SMALL -> Res.string.impact_small
}
