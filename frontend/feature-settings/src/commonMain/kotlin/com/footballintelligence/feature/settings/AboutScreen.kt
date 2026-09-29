package com.footballintelligence.feature.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.SportsSoccer
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.feature.settings.resources.Res
import com.footballintelligence.feature.settings.resources.about_title
import com.footballintelligence.feature.settings.resources.app_description
import com.footballintelligence.feature.settings.resources.app_name
import com.footballintelligence.feature.settings.resources.app_version
import com.footballintelligence.feature.settings.resources.dataset_features_label
import com.footballintelligence.feature.settings.resources.dataset_features_value
import com.footballintelligence.feature.settings.resources.dataset_leagues_label
import com.footballintelligence.feature.settings.resources.dataset_leagues_value
import com.footballintelligence.feature.settings.resources.dataset_matches_label
import com.footballintelligence.feature.settings.resources.dataset_matches_value
import com.footballintelligence.feature.settings.resources.section_dataset
import com.footballintelligence.feature.settings.resources.section_stack
import com.footballintelligence.feature.settings.resources.stack_android_label
import com.footballintelligence.feature.settings.resources.stack_android_value
import com.footballintelligence.feature.settings.resources.stack_assistant_label
import com.footballintelligence.feature.settings.resources.stack_assistant_value
import com.footballintelligence.feature.settings.resources.stack_backend_label
import com.footballintelligence.feature.settings.resources.stack_backend_value
import com.footballintelligence.feature.settings.resources.stack_database_label
import com.footballintelligence.feature.settings.resources.stack_database_value
import com.footballintelligence.feature.settings.resources.stack_di_label
import com.footballintelligence.feature.settings.resources.stack_di_value
import com.footballintelligence.feature.settings.resources.stack_model_label
import com.footballintelligence.feature.settings.resources.stack_model_value
import com.footballintelligence.feature.settings.resources.stack_networking_label
import com.footballintelligence.feature.settings.resources.stack_networking_value
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.stringResource

/** About screen: app version, technology stack, and project description. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AboutScreen(
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(Res.string.about_title)) },
                navigationIcon = { BackButton(onClick = onBack) },
            )
        },
        modifier = modifier,
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Spacer(Modifier.height(16.dp))
            Icon(
                imageVector = Icons.Default.SportsSoccer,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.height(64.dp),
            )
            Text(stringResource(Res.string.app_name), style = MaterialTheme.typography.headlineSmall)
            Text(
                stringResource(Res.string.app_version, APP_VERSION),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(
                stringResource(Res.string.app_description),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text(stringResource(Res.string.section_stack), style = MaterialTheme.typography.titleSmall)
                    HorizontalDivider()
                    StackItem(Res.string.stack_model_label, Res.string.stack_model_value)
                    StackItem(Res.string.stack_assistant_label, Res.string.stack_assistant_value)
                    StackItem(Res.string.stack_backend_label, Res.string.stack_backend_value)
                    StackItem(Res.string.stack_database_label, Res.string.stack_database_value)
                    StackItem(Res.string.stack_android_label, Res.string.stack_android_value)
                    StackItem(Res.string.stack_networking_label, Res.string.stack_networking_value)
                    StackItem(Res.string.stack_di_label, Res.string.stack_di_value)
                }
            }
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                ) {
                    Text(stringResource(Res.string.section_dataset), style = MaterialTheme.typography.titleSmall)
                    HorizontalDivider()
                    StackItem(Res.string.dataset_leagues_label, Res.string.dataset_leagues_value)
                    StackItem(Res.string.dataset_matches_label, Res.string.dataset_matches_value)
                    StackItem(Res.string.dataset_features_label, Res.string.dataset_features_value)
                }
            }
        }
    }
}

@Composable
private fun StackItem(label: StringResource, value: StringResource) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(
            stringResource(label),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(stringResource(value), style = MaterialTheme.typography.bodySmall)
    }
}

/** Matches versionName in app/build.gradle.kts. */
private const val APP_VERSION = "2.1.0"
