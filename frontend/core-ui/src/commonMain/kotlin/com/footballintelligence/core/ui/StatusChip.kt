package com.footballintelligence.core.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.resources.Res
import com.footballintelligence.core.ui.resources.status_offline
import com.footballintelligence.core.ui.resources.status_online
import org.jetbrains.compose.resources.stringResource

/** Small coloured chip indicating an on/off status. */
@Composable
fun StatusChip(
    label: String,
    available: Boolean,
    modifier: Modifier = Modifier,
) {
    val background = if (available) Color(0xFF2E7D32) else Color(0xFFB71C1C)
    val text = stringResource(if (available) Res.string.status_online else Res.string.status_offline, label)
    Text(
        text = text,
        color = Color.White,
        style = MaterialTheme.typography.labelSmall,
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(background)
            .padding(horizontal = 12.dp, vertical = 4.dp),
    )
}
