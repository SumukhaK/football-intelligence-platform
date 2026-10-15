package com.footballintelligence.feature.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.Cloud
import androidx.compose.material.icons.outlined.Insights
import androidx.compose.material.icons.outlined.Language
import androidx.compose.material.icons.outlined.PhoneAndroid
import androidx.compose.material.icons.outlined.Scoreboard
import androidx.compose.material.icons.outlined.SportsSoccer
import androidx.compose.material.icons.outlined.Storage
import androidx.compose.material.icons.outlined.TableChart
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.BackButton
import com.footballintelligence.core.ui.appBarColors
import com.footballintelligence.feature.settings.resources.Res
import com.footballintelligence.feature.settings.resources.about_title
import com.footballintelligence.feature.settings.resources.app_description
import com.footballintelligence.feature.settings.resources.app_name
import com.footballintelligence.feature.settings.resources.app_version
import com.footballintelligence.feature.settings.resources.built_by
import com.footballintelligence.feature.settings.resources.cd_open_website
import com.footballintelligence.feature.settings.resources.data_leagues_label
import com.footballintelligence.feature.settings.resources.data_leagues_value
import com.footballintelligence.feature.settings.resources.data_matches_label
import com.footballintelligence.feature.settings.resources.data_matches_value
import com.footballintelligence.feature.settings.resources.data_refresh_label
import com.footballintelligence.feature.settings.resources.data_refresh_value
import com.footballintelligence.feature.settings.resources.how_assistant_label
import com.footballintelligence.feature.settings.resources.how_assistant_value
import com.footballintelligence.feature.settings.resources.how_predictions_label
import com.footballintelligence.feature.settings.resources.how_predictions_value
import com.footballintelligence.feature.settings.resources.how_scores_label
import com.footballintelligence.feature.settings.resources.how_scores_value
import com.footballintelligence.feature.settings.resources.section_built_with
import com.footballintelligence.feature.settings.resources.section_data
import com.footballintelligence.feature.settings.resources.section_how
import com.footballintelligence.feature.settings.resources.stack_app_label
import com.footballintelligence.feature.settings.resources.stack_app_value
import com.footballintelligence.feature.settings.resources.stack_server_label
import com.footballintelligence.feature.settings.resources.stack_server_value
import com.footballintelligence.feature.settings.resources.stack_storage_label
import com.footballintelligence.feature.settings.resources.stack_storage_value
import com.footballintelligence.feature.settings.resources.website_label
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.stringResource

/** The project's website, also on the README. */
const val PROJECT_WEBSITE = "https://fip-ai.dev"

/** One line of an About section: an icon, a label and what it means. */
private data class AboutItem(val icon: ImageVector, val label: StringResource, val value: StringResource)

private val HOW_IT_WORKS = listOf(
    AboutItem(Icons.Outlined.Insights, Res.string.how_predictions_label, Res.string.how_predictions_value),
    AboutItem(Icons.Outlined.Scoreboard, Res.string.how_scores_label, Res.string.how_scores_value),
    AboutItem(Icons.Outlined.AutoAwesome, Res.string.how_assistant_label, Res.string.how_assistant_value),
)

private val DATA = listOf(
    AboutItem(Icons.Outlined.SportsSoccer, Res.string.data_leagues_label, Res.string.data_leagues_value),
    AboutItem(Icons.Outlined.TableChart, Res.string.data_matches_label, Res.string.data_matches_value),
    AboutItem(Icons.Outlined.Cloud, Res.string.data_refresh_label, Res.string.data_refresh_value),
)

private val BUILT_WITH = listOf(
    AboutItem(Icons.Outlined.PhoneAndroid, Res.string.stack_app_label, Res.string.stack_app_value),
    AboutItem(Icons.Outlined.Cloud, Res.string.stack_server_label, Res.string.stack_server_value),
    AboutItem(Icons.Outlined.Storage, Res.string.stack_storage_label, Res.string.stack_storage_value),
)

/** About screen: what the app is, how it works, its data and how it's built. Scrolls. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AboutScreen(
    versionName: String,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                colors = appBarColors(),
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
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            AboutHeader(versionName)
            AboutSection(Res.string.section_how, HOW_IT_WORKS)
            AboutSection(Res.string.section_data, DATA)
            AboutSection(Res.string.section_built_with, BUILT_WITH)
            AboutFooter()
        }
    }
}

@Composable
private fun AboutHeader(versionName: String) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Box(
            modifier = Modifier
                .size(72.dp)
                .background(MaterialTheme.colorScheme.primaryContainer, CircleShape),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = Icons.Outlined.SportsSoccer,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onPrimaryContainer,
                modifier = Modifier.size(40.dp),
            )
        }
        Text(stringResource(Res.string.app_name), style = MaterialTheme.typography.headlineSmall)
        // A plain pill, not a chip: a disabled chip would grey the version out.
        Surface(shape = CircleShape, color = MaterialTheme.colorScheme.secondaryContainer) {
            Text(
                stringResource(Res.string.app_version, versionName),
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.onSecondaryContainer,
                modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
            )
        }
        Text(
            stringResource(Res.string.app_description),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
    }
}

@Composable
private fun AboutSection(title: StringResource, items: List<AboutItem>) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Text(
                stringResource(title),
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.semantics { heading() },
            )
            items.forEach { AboutRow(it) }
        }
    }
}

@Composable
private fun AboutRow(item: AboutItem) {
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Top) {
        Icon(
            imageVector = item.icon,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary,
            modifier = Modifier.size(20.dp),
        )
        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(stringResource(item.label), style = MaterialTheme.typography.labelLarge)
            Text(
                stringResource(item.value),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun AboutFooter() {
    val uriHandler = LocalUriHandler.current
    val description = stringResource(Res.string.cd_open_website)
    Column(modifier = Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
        TextButton(
            onClick = { uriHandler.openUri(PROJECT_WEBSITE) },
            modifier = Modifier.semantics { contentDescription = description },
        ) {
            Icon(Icons.Outlined.Language, contentDescription = null, modifier = Modifier.size(18.dp))
            Text(stringResource(Res.string.website_label), modifier = Modifier.padding(start = 8.dp))
        }
        Text(
            stringResource(Res.string.built_by),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
