package com.footballintelligence.core.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview

@Preview
@Composable
private fun ErrorViewPreview() {
    PreviewSurface {
        ErrorView(message = "Could not reach the server.", onRetry = {})
    }
}

@Preview
@Composable
private fun LoadingViewPreview() {
    PreviewSurface {
        LoadingView()
    }
}

@Preview
@Composable
private fun StatusChipPreview() {
    PreviewSurface {
        Column {
            StatusChip(label = "Prediction API", available = true)
            StatusChip(label = "AI Assistant", available = false)
        }
    }
}

@Preview
@Composable
private fun BackButtonPreview() {
    PreviewSurface {
        BackButton(onClick = {})
    }
}
