package com.footballintelligence.feature.assistant

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.footballintelligence.feature.assistant.resources.Res
import com.footballintelligence.feature.assistant.resources.welcome_body
import com.footballintelligence.feature.assistant.resources.welcome_title
import org.jetbrains.compose.resources.stringResource

/** Introduces the assistant when the conversation is empty. */
@Composable
internal fun WelcomeMessage() {
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
    }
}
