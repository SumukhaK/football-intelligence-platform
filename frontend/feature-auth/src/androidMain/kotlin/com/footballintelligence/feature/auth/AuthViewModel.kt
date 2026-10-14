package com.footballintelligence.feature.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.feature.auth.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * ViewModel for the sign-in and invite code screen. On success the session
 * starts and the app leaves the screen, so the spinner stays until then.
 */
class AuthViewModel(private val repository: AuthRepository) : ViewModel() {
    private val _form = MutableStateFlow(AuthForm())
    val form: StateFlow<AuthForm> = _form.asStateFlow()

    private val _state = MutableStateFlow<AuthUiState>(AuthUiState.Idle)
    val state: StateFlow<AuthUiState> = _state.asStateFlow()

    fun selectTab(tab: AuthTab) = edit { copy(tab = tab) }

    fun updateEmail(value: String) = edit { copy(email = value) }

    fun updatePassword(value: String) = edit { copy(password = value) }

    fun updateCode(value: String) = edit { copy(code = value) }

    fun updateNewPassword(value: String) = edit { copy(newPassword = value) }

    /** Signs in or redeems the invite, depending on the tab. */
    fun submit() {
        val form = _form.value
        if (_state.value == AuthUiState.Loading || !form.isComplete) return
        if (form.tab == AuthTab.INVITE_CODE && form.newPassword.length < MIN_PASSWORD_LENGTH) {
            _state.value = AuthUiState.Error(AuthProblem.PASSWORD_TOO_SHORT)
            return
        }
        _state.value = AuthUiState.Loading
        viewModelScope.launch {
            val result = when (form.tab) {
                AuthTab.SIGN_IN -> repository.signIn(form.email, form.password)
                AuthTab.INVITE_CODE -> repository.redeemInvite(form.email, form.code, form.newPassword)
            }
            if (result is NetworkResult.Error) _state.value = result.toAuthError()
        }
    }

    /** Changes the form; an old error no longer applies once the user edits. */
    private fun edit(change: AuthForm.() -> AuthForm) {
        if (_state.value == AuthUiState.Loading) return
        _form.update(change)
        _state.value = AuthUiState.Idle
    }
}
