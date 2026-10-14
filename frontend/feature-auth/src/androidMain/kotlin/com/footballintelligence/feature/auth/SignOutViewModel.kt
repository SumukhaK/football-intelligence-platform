package com.footballintelligence.feature.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.footballintelligence.feature.auth.repository.AuthRepository
import kotlinx.coroutines.launch

/** Sign out from Settings; the app returns to sign-in once the session ends. */
class SignOutViewModel(private val repository: AuthRepository) : ViewModel() {
    fun signOut() {
        viewModelScope.launch { repository.signOut() }
    }
}
