package com.footballintelligence.feature.prediction

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.model.Insights
import com.footballintelligence.core.model.ScoreProbability
import com.footballintelligence.core.ui.KickoffLoader
import com.footballintelligence.feature.prediction.resources.Res
import com.footballintelligence.feature.prediction.resources.cd_market_row
import com.footballintelligence.feature.prediction.resources.cd_score_row
import com.footballintelligence.feature.prediction.resources.expected_goals_line
import com.footballintelligence.feature.prediction.resources.expected_goals_title
import com.footballintelligence.feature.prediction.resources.insights_disclaimer
import com.footballintelligence.feature.prediction.resources.insights_loading
import com.footballintelligence.feature.prediction.resources.insights_unavailable
import com.footballintelligence.feature.prediction.resources.market_btts
import com.footballintelligence.feature.prediction.resources.market_clean_sheet
import com.footballintelligence.feature.prediction.resources.market_over_1_5
import com.footballintelligence.feature.prediction.resources.market_over_2_5
import com.footballintelligence.feature.prediction.resources.market_over_3_5
import com.footballintelligence.feature.prediction.resources.markets_title
import com.footballintelligence.feature.prediction.resources.percent
import com.footballintelligence.feature.prediction.resources.reason_bullet
import com.footballintelligence.feature.prediction.resources.score_line
import com.footballintelligence.feature.prediction.resources.top_scores_title
import com.footballintelligence.feature.prediction.resources.why_title
import org.jetbrains.compose.resources.stringResource

/** Goals-model sections under a prediction: scores, goals, markets and reasons. */
@Composable
fun InsightsSection(state: InsightsUiState, modifier: Modifier = Modifier) {
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(16.dp)) {
        when (state) {
            is InsightsUiState.Idle -> Unit
            is InsightsUiState.Loading -> InsightsLoading()
            is InsightsUiState.Error -> MutedText(stringResource(Res.string.insights_unavailable))
            is InsightsUiState.Success -> InsightsContent(state.insights)
        }
    }
}

@Composable
private fun InsightsContent(insights: Insights) {
    TopScoresCard(insights)
    SectionCard(title = stringResource(Res.string.expected_goals_title)) {
        Text(
            stringResource(
                Res.string.expected_goals_line,
                insights.homeTeam,
                oneDecimal(insights.expectedGoals.home),
                oneDecimal(insights.expectedGoals.away),
                insights.awayTeam,
            ),
            style = MaterialTheme.typography.titleMedium,
        )
    }
    MarketsCard(insights)
    if (insights.reasons.isNotEmpty()) {
        SectionCard(title = stringResource(Res.string.why_title)) {
            insights.reasons.forEach { reason ->
                Text(
                    stringResource(Res.string.reason_bullet, reason),
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
    MutedText(stringResource(Res.string.insights_disclaimer))
}

@Composable
private fun TopScoresCard(insights: Insights) {
    val top = insights.topScores.maxOfOrNull { it.probability } ?: 0.0
    SectionCard(title = stringResource(Res.string.top_scores_title)) {
        insights.topScores.forEach { score ->
            ScoreRow(score = score, insights = insights, scale = top)
        }
    }
}

@Composable
private fun ScoreRow(score: ScoreProbability, insights: Insights, scale: Double) {
    val percentText = stringResource(Res.string.percent, percentOf(score.probability))
    val description = stringResource(
        Res.string.cd_score_row,
        insights.homeTeam,
        score.home,
        insights.awayTeam,
        score.away,
        percentOf(score.probability),
    )
    Column(
        modifier = Modifier.clearAndSetSemantics { contentDescription = description },
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(
                stringResource(Res.string.score_line, score.home, score.away),
                style = MaterialTheme.typography.bodyLarge,
            )
            Text(percentText, style = MaterialTheme.typography.titleSmall)
        }
        LinearProgressIndicator(
            progress = { if (scale > 0) (score.probability / scale).toFloat() else 0f },
            modifier = Modifier.fillMaxWidth(),
        )
    }
}

@Composable
private fun MarketsCard(insights: Insights) {
    val markets = insights.markets
    SectionCard(title = stringResource(Res.string.markets_title)) {
        MarketRow(stringResource(Res.string.market_btts), markets.btts)
        MarketRow(stringResource(Res.string.market_over_1_5), markets.over15)
        MarketRow(stringResource(Res.string.market_over_2_5), markets.over25)
        MarketRow(stringResource(Res.string.market_over_3_5), markets.over35)
        MarketRow(
            stringResource(Res.string.market_clean_sheet, insights.homeTeam),
            markets.homeCleanSheet,
        )
        MarketRow(
            stringResource(Res.string.market_clean_sheet, insights.awayTeam),
            markets.awayCleanSheet,
        )
    }
}

@Composable
private fun MarketRow(label: String, probability: Double) {
    val description = stringResource(Res.string.cd_market_row, label, percentOf(probability))
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clearAndSetSemantics { contentDescription = description },
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Text(
            stringResource(Res.string.percent, percentOf(probability)),
            style = MaterialTheme.typography.titleSmall,
        )
    }
}

@Composable
private fun SectionCard(title: String, content: @Composable () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(title, style = MaterialTheme.typography.titleSmall)
            content()
        }
    }
}

@Composable
private fun InsightsLoading() {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        KickoffLoader(size = 24.dp)
        MutedText(stringResource(Res.string.insights_loading))
    }
}

@Composable
private fun MutedText(text: String) {
    Text(
        text,
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}
