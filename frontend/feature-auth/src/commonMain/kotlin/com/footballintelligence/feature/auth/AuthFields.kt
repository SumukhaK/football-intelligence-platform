package com.footballintelligence.feature.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.footballintelligence.feature.auth.resources.Res
import com.footballintelligence.feature.auth.resources.cd_hide_password
import com.footballintelligence.feature.auth.resources.cd_show_password
import com.footballintelligence.feature.auth.resources.field_email
import com.footballintelligence.feature.auth.resources.field_invite_code
import com.footballintelligence.feature.auth.resources.field_new_password
import com.footballintelligence.feature.auth.resources.field_password
import com.footballintelligence.feature.auth.resources.forgot_password
import com.footballintelligence.feature.auth.resources.new_password_hint
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.stringResource

/** The sign-in tab: email and password, then a hint for a forgotten password. */
@Composable
internal fun SignInFields(form: AuthForm, events: AuthEvents, enabled: Boolean) {
    Column(verticalArrangement = Arrangement.spacedBy(24.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(20.dp)) {
            EmailField(form.email, events.onEmailChange, enabled)
            PasswordField(
                value = form.password,
                onValueChange = events.onPasswordChange,
                label = Res.string.field_password,
                enabled = enabled,
                onDone = events.onSubmit,
            )
        }
        Text(
            stringResource(Res.string.forgot_password),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

/** The invite code tab: email, the code from the owner, and a new password. */
@Composable
internal fun InviteFields(form: AuthForm, events: AuthEvents, enabled: Boolean) {
    Column(verticalArrangement = Arrangement.spacedBy(20.dp)) {
        EmailField(form.email, events.onEmailChange, enabled)
        // The code is a case-sensitive random string: no capitals, corrections or suggestions.
        OutlinedTextField(
            value = form.code,
            onValueChange = events.onCodeChange,
            label = { Text(stringResource(Res.string.field_invite_code)) },
            singleLine = true,
            enabled = enabled,
            keyboardOptions = KeyboardOptions(
                capitalization = KeyboardCapitalization.None,
                autoCorrectEnabled = false,
                keyboardType = KeyboardType.Ascii,
                imeAction = ImeAction.Next,
            ),
            modifier = Modifier.fillMaxWidth(),
        )
        PasswordField(
            value = form.newPassword,
            onValueChange = events.onNewPasswordChange,
            label = Res.string.field_new_password,
            enabled = enabled,
            onDone = events.onSubmit,
            supportingText = Res.string.new_password_hint,
        )
    }
}

@Composable
private fun EmailField(value: String, onValueChange: (String) -> Unit, enabled: Boolean) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(stringResource(Res.string.field_email)) },
        singleLine = true,
        enabled = enabled,
        keyboardOptions = KeyboardOptions(
            autoCorrectEnabled = false,
            keyboardType = KeyboardType.Email,
            imeAction = ImeAction.Next,
        ),
        modifier = Modifier.fillMaxWidth(),
    )
}

/** A password field with a show/hide toggle; whether it is shown is only this field's concern. */
@Composable
private fun PasswordField(
    value: String,
    onValueChange: (String) -> Unit,
    label: StringResource,
    enabled: Boolean,
    onDone: () -> Unit,
    supportingText: StringResource? = null,
) {
    var visible by rememberSaveable { mutableStateOf(false) }
    val toggleDescription = stringResource(if (visible) Res.string.cd_hide_password else Res.string.cd_show_password)
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(stringResource(label)) },
        supportingText = supportingText?.let { { Text(stringResource(it)) } },
        singleLine = true,
        enabled = enabled,
        visualTransformation = if (visible) VisualTransformation.None else PasswordVisualTransformation(),
        trailingIcon = {
            IconButton(onClick = { visible = !visible }) {
                Icon(
                    if (visible) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                    contentDescription = toggleDescription,
                )
            }
        },
        keyboardOptions = KeyboardOptions(
            autoCorrectEnabled = false,
            keyboardType = KeyboardType.Password,
            imeAction = ImeAction.Done,
        ),
        keyboardActions = KeyboardActions(onDone = { onDone() }),
        modifier = Modifier.fillMaxWidth(),
    )
}
