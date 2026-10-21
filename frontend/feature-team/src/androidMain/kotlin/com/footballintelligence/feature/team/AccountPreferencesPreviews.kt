package com.footballintelligence.feature.team

import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.ui.PreviewSurface

@Preview
@Composable
private fun PreferencesLoadingPreview() = PreviewSurface {
    AccountPreferencesScreen(AccountPreferencesUiState.Loading, onRetry = {}, onSignOut = {})
}

@Preview
@Composable
private fun PreferencesErrorPreview() = PreviewSurface {
    AccountPreferencesScreen(
        AccountPreferencesUiState.Error("Unavailable", ErrorKind.OFFLINE),
        onRetry = {},
        onSignOut = {},
    )
}
