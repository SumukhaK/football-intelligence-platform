package com.footballintelligence.core.ui

import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.TopAppBarColors
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import com.footballintelligence.core.designsystem.GreenOnPrimary
import com.footballintelligence.core.designsystem.GreenPrimary

/**
 * The brand-green top bar every screen shares, so the colour never changes between screens.
 * The deep green is used in dark mode too: the dark scheme's bright primary glared on a phone.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun appBarColors(): TopAppBarColors = TopAppBarDefaults.topAppBarColors(
    containerColor = GreenPrimary,
    titleContentColor = GreenOnPrimary,
    navigationIconContentColor = GreenOnPrimary,
    actionIconContentColor = GreenOnPrimary,
)
