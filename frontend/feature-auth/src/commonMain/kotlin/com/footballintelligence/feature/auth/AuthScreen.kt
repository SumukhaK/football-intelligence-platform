package com.footballintelligence.feature.auth

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.footballintelligence.core.designsystem.GreenOnPrimary
import com.footballintelligence.core.designsystem.GreenPrimary
import com.footballintelligence.core.designsystem.GreenSecondaryContainer
import com.footballintelligence.core.ui.errorMessage
import com.footballintelligence.feature.auth.resources.Res
import com.footballintelligence.feature.auth.resources.action_create_account
import com.footballintelligence.feature.auth.resources.action_sign_in
import com.footballintelligence.feature.auth.resources.auth_app_name
import com.footballintelligence.feature.auth.resources.auth_invite_only
import com.footballintelligence.feature.auth.resources.error_blocked
import com.footballintelligence.feature.auth.resources.error_invalid_invite
import com.footballintelligence.feature.auth.resources.error_password_too_short
import com.footballintelligence.feature.auth.resources.error_too_many_tries
import com.footballintelligence.feature.auth.resources.error_wrong_credentials
import com.footballintelligence.feature.auth.resources.ic_kickoff
import com.footballintelligence.feature.auth.resources.tab_invite_code
import com.footballintelligence.feature.auth.resources.tab_sign_in
import org.jetbrains.compose.resources.painterResource
import org.jetbrains.compose.resources.stringResource

/** Header height below the status bar; the sheet's rounded top overlaps it by [SHEET_OVERLAP]. */
private val HEADER_HEIGHT = 300.dp
private val SHEET_OVERLAP = 28.dp

/**
 * Sign in or redeem an invite (ADR 022): a green header with the Kick-off
 * logo over a sheet with two tabs, which can be tapped or swiped.
 */
@Composable
fun AuthScreen(
    form: AuthForm,
    uiState: AuthUiState,
    events: AuthEvents,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier
            .fillMaxSize()
            .background(GreenPrimary)
            .statusBarsPadding()
            .imePadding(),
    ) {
        BoxWithConstraints {
            val sheetMinHeight = maxHeight - HEADER_HEIGHT + SHEET_OVERLAP
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
                Header()
                AuthSheet(form, uiState, events, Modifier.heightIn(min = sheetMinHeight))
            }
        }
    }
}

@Composable
private fun Header() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .height(HEADER_HEIGHT - SHEET_OVERLAP),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp, Alignment.CenterVertically),
    ) {
        Image(painterResource(Res.drawable.ic_kickoff), contentDescription = null, modifier = Modifier.size(96.dp))
        Text(
            stringResource(Res.string.auth_app_name),
            fontSize = 24.sp,
            fontWeight = FontWeight.Medium,
            color = GreenOnPrimary,
        )
        Text(stringResource(Res.string.auth_invite_only), fontSize = 14.sp, color = GreenSecondaryContainer)
    }
}

@Composable
private fun AuthSheet(form: AuthForm, uiState: AuthUiState, events: AuthEvents, modifier: Modifier) {
    val loading = uiState == AuthUiState.Loading
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(topStart = 28.dp, topEnd = 28.dp))
            .background(MaterialTheme.colorScheme.surface)
            .navigationBarsPadding()
            .padding(start = 24.dp, top = 28.dp, end = 24.dp, bottom = 32.dp),
        verticalArrangement = Arrangement.SpaceBetween,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(24.dp)) {
            TabRow(form.tab, enabled = !loading, onSelect = events.onSelectTab)
            TabPager(form, events, enabled = !loading)
        }
        Column(Modifier.padding(top = 24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            SubmitButton(form, loading, events.onSubmit)
            if (uiState is AuthUiState.Error) {
                Text(
                    authErrorText(uiState),
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@Composable
private fun TabRow(selected: AuthTab, enabled: Boolean, onSelect: (AuthTab) -> Unit) {
    SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
        AuthTab.entries.forEachIndexed { index, tab ->
            SegmentedButton(
                selected = tab == selected,
                onClick = { onSelect(tab) },
                shape = SegmentedButtonDefaults.itemShape(index, AuthTab.entries.size),
                enabled = enabled,
            ) {
                Text(stringResource(tab.label()))
            }
        }
    }
}

/** The tabs' fields side by side: swiping changes the tab, and choosing a tab scrolls to it. */
@Composable
private fun TabPager(form: AuthForm, events: AuthEvents, enabled: Boolean) {
    val pagerState = rememberPagerState(initialPage = form.tab.ordinal) { AuthTab.entries.size }
    LaunchedEffect(form.tab) {
        if (pagerState.currentPage != form.tab.ordinal) pagerState.animateScrollToPage(form.tab.ordinal)
    }
    val currentTab by rememberUpdatedState(form.tab)
    val onSelectTab by rememberUpdatedState(events.onSelectTab)
    LaunchedEffect(pagerState) {
        snapshotFlow { pagerState.settledPage }.collect { page ->
            if (page != currentTab.ordinal) onSelectTab(AuthTab.entries[page])
        }
    }
    HorizontalPager(
        state = pagerState,
        userScrollEnabled = enabled,
        verticalAlignment = Alignment.Top,
        pageSpacing = 24.dp,
    ) { page ->
        when (AuthTab.entries[page]) {
            AuthTab.SIGN_IN -> SignInFields(form, events, enabled)
            AuthTab.INVITE_CODE -> InviteFields(form, events, enabled)
        }
    }
}

@Composable
private fun SubmitButton(form: AuthForm, loading: Boolean, onSubmit: () -> Unit) {
    Button(
        onClick = onSubmit,
        enabled = form.isComplete && !loading,
        modifier = Modifier.fillMaxWidth().height(48.dp),
    ) {
        if (loading) {
            CircularProgressIndicator(Modifier.size(24.dp), color = LocalContentColor.current, strokeWidth = 2.dp)
        } else {
            val label = when (form.tab) {
                AuthTab.SIGN_IN -> Res.string.action_sign_in
                AuthTab.INVITE_CODE -> Res.string.action_create_account
            }
            Text(stringResource(label), fontSize = 16.sp)
        }
    }
}

private fun AuthTab.label() = when (this) {
    AuthTab.SIGN_IN -> Res.string.tab_sign_in
    AuthTab.INVITE_CODE -> Res.string.tab_invite_code
}

@Composable
private fun authErrorText(error: AuthUiState.Error): String = when (error.problem) {
    AuthProblem.WRONG_CREDENTIALS -> stringResource(Res.string.error_wrong_credentials)
    AuthProblem.TOO_MANY_TRIES -> stringResource(Res.string.error_too_many_tries)
    AuthProblem.INVALID_INVITE -> stringResource(Res.string.error_invalid_invite)
    AuthProblem.PASSWORD_TOO_SHORT -> stringResource(Res.string.error_password_too_short)
    AuthProblem.BLOCKED -> stringResource(Res.string.error_blocked)
    AuthProblem.OTHER -> errorMessage(error.kind, error.message)
}
