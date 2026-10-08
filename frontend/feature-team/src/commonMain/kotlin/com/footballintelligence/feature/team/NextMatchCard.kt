package com.footballintelligence.feature.team

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.next_match_clean_sheet
import com.footballintelligence.feature.team.resources.next_match_draw_possible
import com.footballintelligence.feature.team.resources.next_match_heading
import com.footballintelligence.feature.team.resources.next_match_pick
import com.footballintelligence.feature.team.resources.next_match_pick_chance
import com.footballintelligence.feature.team.resources.next_match_reasons
import com.footballintelligence.feature.team.resources.next_match_scoreline
import com.footballintelligence.feature.team.resources.next_match_scoreline_chance
import com.footballintelligence.feature.team.resources.next_match_scorelines
import com.footballintelligence.feature.team.resources.next_match_time_tbc
import com.footballintelligence.feature.team.resources.next_match_versus
import com.footballintelligence.feature.team.resources.next_match_when
import com.footballintelligence.feature.team.resources.outcome_draw
import com.footballintelligence.feature.team.resources.outcome_loss
import com.footballintelligence.feature.team.resources.outcome_win
import org.jetbrains.compose.resources.stringResource

/** "Your next match": fixture, pick, reasons, likeliest scores and clean-sheet chance. */
@Composable
fun NextMatchCard(match: NextMatch, modifier: Modifier = Modifier) {
    Card(modifier = modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(
                stringResource(Res.string.next_match_heading),
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.semantics { heading() },
            )
            Fixture(match)
            Pick(match)
            if (match.reasons.isNotEmpty()) {
                HorizontalDivider()
                Reasons(match.reasons)
            }
            if (match.scorelines.isNotEmpty()) {
                HorizontalDivider()
                Scorelines(match.scorelines)
            }
            match.cleanSheetPercent?.let {
                Text(stringResource(Res.string.next_match_clean_sheet, it), style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Composable
private fun Fixture(match: NextMatch) {
    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text(
            stringResource(Res.string.next_match_versus, match.homeTeam, match.awayTeam),
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.SemiBold,
        )
        val time = match.time ?: stringResource(Res.string.next_match_time_tbc)
        Text(
            stringResource(Res.string.next_match_when, match.day, time),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun Pick(match: NextMatch) {
    val outcome = stringResource(
        when (match.pick) {
            TeamOutcome.WIN -> Res.string.outcome_win
            TeamOutcome.DRAW -> Res.string.outcome_draw
            TeamOutcome.LOSS -> Res.string.outcome_loss
        },
    )
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Column(Modifier.weight(1f)) {
            Text(stringResource(Res.string.next_match_pick, outcome), style = MaterialTheme.typography.titleMedium)
            Text(
                stringResource(Res.string.next_match_pick_chance, match.pickPercent),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        if (match.drawPossible) {
            Surface(shape = RoundedCornerShape(12.dp), color = MaterialTheme.colorScheme.tertiaryContainer) {
                Text(
                    stringResource(Res.string.next_match_draw_possible),
                    style = MaterialTheme.typography.labelMedium,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                )
            }
        }
    }
}

@Composable
private fun Reasons(reasons: List<MatchReason>) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(stringResource(Res.string.next_match_reasons), style = MaterialTheme.typography.titleSmall)
        reasons.forEach { reason ->
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(reason.label, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                Text(reason.value, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
            }
        }
    }
}

@Composable
private fun Scorelines(scorelines: List<Scoreline>) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(stringResource(Res.string.next_match_scorelines), style = MaterialTheme.typography.titleSmall)
        Row(Modifier.fillMaxWidth()) {
            scorelines.forEach { score ->
                Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        stringResource(Res.string.next_match_scoreline, score.home, score.away),
                        style = MaterialTheme.typography.titleLarge,
                        textAlign = TextAlign.Center,
                    )
                    Text(
                        stringResource(Res.string.next_match_scoreline_chance, score.percent),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}
