package com.footballintelligence.feature.settings

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForwardIos
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.QueryStats
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.feature.settings.resources.Res
import com.footballintelligence.feature.settings.resources.about_summary
import com.footballintelligence.feature.settings.resources.about_title
import com.footballintelligence.feature.settings.resources.cd_open_about
import com.footballintelligence.feature.settings.resources.cd_open_model_info
import com.footballintelligence.feature.settings.resources.model_info_summary
import com.footballintelligence.feature.settings.resources.model_info_title
import com.footballintelligence.feature.settings.resources.section_analytics
import com.footballintelligence.feature.settings.resources.settings_title
import org.jetbrains.compose.resources.stringResource

/**
 * Settings screen with links to Model Info and About. [status] is shown first;
 * the app passes the backend status card.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onModelInfoClick: () -> Unit,
    onAboutClick: () -> Unit,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    status: @Composable () -> Unit = {},
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(Res.string.settings_title)) },
                navigationIcon = { BackButton(onClick = onBack) },
            )
        },
        modifier = modifier,
    ) { padding ->
        val modelInfoDescription = stringResource(Res.string.cd_open_model_info)
        val aboutDescription = stringResource(Res.string.cd_open_about)
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            status()
            Text(stringResource(Res.string.section_analytics), style = MaterialTheme.typography.labelMedium)
            Card(modifier = Modifier.fillMaxWidth()) {
                Column {
                    ListItem(
                        headlineContent = { Text(stringResource(Res.string.model_info_title)) },
                        supportingContent = { Text(stringResource(Res.string.model_info_summary)) },
                        leadingContent = {
                            Icon(Icons.Default.QueryStats, contentDescription = null)
                        },
                        trailingContent = {
                            Icon(
                                Icons.AutoMirrored.Filled.ArrowForwardIos,
                                contentDescription = null,
                            )
                        },
                        modifier = Modifier
                            .clickable(onClick = onModelInfoClick)
                            .semantics { contentDescription = modelInfoDescription },
                    )
                    HorizontalDivider()
                    ListItem(
                        headlineContent = { Text(stringResource(Res.string.about_title)) },
                        supportingContent = { Text(stringResource(Res.string.about_summary)) },
                        leadingContent = {
                            Icon(Icons.Default.Info, contentDescription = null)
                        },
                        trailingContent = {
                            Icon(
                                Icons.AutoMirrored.Filled.ArrowForwardIos,
                                contentDescription = null,
                            )
                        },
                        modifier = Modifier
                            .clickable(onClick = onAboutClick)
                            .semantics { contentDescription = aboutDescription },
                    )
                }
            }
        }
    }
}
