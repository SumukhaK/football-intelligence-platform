package com.footballintelligence.core.ui

import androidx.compose.runtime.Composable
import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.ui.resources.Res
import com.footballintelligence.core.ui.resources.error_offline
import com.footballintelligence.core.ui.resources.error_server_busy
import com.footballintelligence.core.ui.resources.error_unknown
import org.jetbrains.compose.resources.stringResource

/**
 * Plain-language text for an error.
 *
 * A rejected request shows the server's own reason (for example, a team that
 * is not in the chosen league); everything else gets friendly fixed wording.
 */
@Composable
fun errorMessage(kind: ErrorKind, serverMessage: String): String = when (kind) {
    ErrorKind.OFFLINE -> stringResource(Res.string.error_offline)
    ErrorKind.SERVER_BUSY -> stringResource(Res.string.error_server_busy)
    ErrorKind.REJECTED -> serverMessage
    ErrorKind.UNKNOWN -> stringResource(Res.string.error_unknown)
}
