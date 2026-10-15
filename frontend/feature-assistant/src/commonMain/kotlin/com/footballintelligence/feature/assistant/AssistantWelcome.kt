package com.footballintelligence.feature.assistant

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SuggestionChip
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.footballintelligence.feature.assistant.resources.Res
import com.footballintelligence.feature.assistant.resources.starter_draw_tag
import com.footballintelligence.feature.assistant.resources.starter_next_match
import com.footballintelligence.feature.assistant.resources.starter_pick
import com.footballintelligence.feature.assistant.resources.starters_heading
import com.footballintelligence.feature.assistant.resources.welcome_body
import com.footballintelligence.feature.assistant.resources.welcome_title
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.stringResource

// Checked against the local assistant: each gets a grounded answer (the next-match
// one uses the saved team, ADR 031). A scoreline-vs-result question did not, so
// that explanation lives on the result screens instead.
private val STARTERS: List<StringResource> = listOf(
    Res.string.starter_pick,
    Res.string.starter_next_match,
    Res.string.starter_draw_tag,
)

/** The empty chat: what the assistant is for, and starter questions that send on a tap. */
@Composable
internal fun WelcomeMessage(onAsk: (String) -> Unit) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Spacer(Modifier.height(32.dp))
        Text(stringResource(Res.string.welcome_title), style = MaterialTheme.typography.titleMedium)
        Text(
            stringResource(Res.string.welcome_body),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(8.dp))
        Text(stringResource(Res.string.starters_heading), style = MaterialTheme.typography.labelLarge)
        STARTERS.forEach { starter ->
            val question = stringResource(starter)
            SuggestionChip(onClick = { onAsk(question) }, label = { Text(question) })
        }
    }
}
