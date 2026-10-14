package com.footballintelligence.feature.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.footballintelligence.core.designsystem.GreenOnPrimary
import com.footballintelligence.core.designsystem.GreenPrimary
import com.footballintelligence.core.ui.ErrorView
import com.footballintelligence.core.ui.LoadingView
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.auth.resources.Res
import com.footballintelligence.feature.auth.resources.action_accept
import com.footballintelligence.feature.auth.resources.action_sign_out
import com.footballintelligence.feature.auth.resources.consent_store_questions
import com.footballintelligence.feature.auth.resources.consent_store_questions_hint
import com.footballintelligence.feature.auth.resources.consent_title
import org.jetbrains.compose.resources.stringResource

/**
 * The notice shown after sign-in (ADR 022). Its text comes from the server;
 * storing question text is off unless the user turns it on.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConsentScreen(
    uiState: ConsentUiState,
    onStoreQuestionsChange: (Boolean) -> Unit,
    onAccept: () -> Unit,
    onSignOut: () -> Unit,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(Res.string.consent_title)) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = GreenPrimary,
                    titleContentColor = GreenOnPrimary,
                ),
            )
        },
        modifier = modifier,
    ) { padding ->
        val content = Modifier.padding(padding)
        when (uiState) {
            is ConsentUiState.Loading, is ConsentUiState.Accepted -> LoadingView(content)
            is ConsentUiState.Error -> ErrorView(errorMessage(uiState.kind, uiState.message), onRetry, content)
            is ConsentUiState.Ready -> ConsentContent(uiState, onStoreQuestionsChange, onAccept, onSignOut, content)
        }
    }
}

@Composable
private fun ConsentContent(
    state: ConsentUiState.Ready,
    onStoreQuestionsChange: (Boolean) -> Unit,
    onAccept: () -> Unit,
    onSignOut: () -> Unit,
    modifier: Modifier,
) {
    Column(modifier.fillMaxSize()) {
        Text(
            state.text,
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
                .padding(start = 20.dp, top = 24.dp, end = 20.dp),
        )
        Column(
            modifier = Modifier.padding(start = 16.dp, top = 16.dp, end = 16.dp, bottom = 24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            StoreQuestionsCard(state.storeQuestions, enabled = !state.isSubmitting, onStoreQuestionsChange)
            Button(
                onClick = onAccept,
                enabled = !state.isSubmitting,
                modifier = Modifier.fillMaxWidth().height(48.dp),
            ) {
                if (state.isSubmitting) {
                    CircularProgressIndicator(
                        Modifier.size(24.dp),
                        color = LocalContentColor.current,
                        strokeWidth = 2.dp,
                    )
                } else {
                    Text(stringResource(Res.string.action_accept), fontSize = 16.sp)
                }
            }
            state.error?.let {
                Text(
                    errorMessage(it.kind, it.message),
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
            TextButton(onClick = onSignOut, modifier = Modifier.fillMaxWidth().height(44.dp)) {
                Text(stringResource(Res.string.action_sign_out))
            }
        }
    }
}

/** The whole card toggles the switch, so it reads as one control to TalkBack. */
@Composable
private fun StoreQuestionsCard(checked: Boolean, enabled: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
    ) {
        Row(
            modifier = Modifier
                .toggleable(checked, enabled = enabled, role = Role.Switch, onValueChange = onCheckedChange)
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(stringResource(Res.string.consent_store_questions), style = MaterialTheme.typography.titleMedium)
                Text(
                    stringResource(Res.string.consent_store_questions_hint),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Switch(checked = checked, onCheckedChange = null, enabled = enabled)
        }
    }
}
