# frontend — Compose Multiplatform Android Application

Android client for the Football Intelligence Platform. Built with Compose Multiplatform (KMP), targeting Android API 26+.

## Stack

| Tool | Version | Role |
|---|---|---|
| Kotlin Multiplatform | 2.0.20 | Shared source across Android targets |
| Compose Multiplatform | 1.7.0 | Shared UI in `commonMain` |
| Ktor | 2.3.12 | HTTP client for FastAPI backend |
| Koin | 3.5.6 | Dependency injection |
| AndroidX Navigation Compose | 2.8.3 | Route-based navigation |
| AndroidX ViewModel | 2.8.3 | Lifecycle-scoped state holders |
| Kotlinx Serialization | 1.7.1 | JSON serialisation for API DTOs |
| Napier | 2.7.1 | KMP-compatible logging |
| JUnit 5 + MockK + Turbine | — | Unit testing |

## Module Structure

```
app/                   — Application entry point, NavHost, Koin assembly
feature-home/          — Home screen: backend health status
feature-prediction/    — Prediction, Result, and Explain screens
feature-assistant/     — AI Assistant chat screen
feature-settings/      — Settings, Model Information, and About screens
core-network/          — Ktor API service and HTTP client factory
core-model/            — Domain models and network result types
core-design-system/    — Material 3 theme and colour palette
core-navigation/       — Screen routes sealed class
core-ui/               — Shared UI components (LoadingView, ErrorView, StatusChip)
core-common/           — DispatcherProvider interface
```

## Running Locally

1. Start the FastAPI backend (see `backend/README.md`). It must be reachable on `localhost:8000`.

2. Launch an Android emulator (API 26+). The app connects to `http://10.0.2.2:8000` (emulator localhost alias).

3. Build and install:
   ```bash
   cd frontend
   ./gradlew assembleDebug
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```

## Running Tests

```bash
./gradlew test
```

Tests live in `src/commonTest/` for each feature and core module.

## Architecture

The app follows MVVM with strict layer separation:

- **Composables** (`commonMain`) — receive `UiState` and callbacks, contain no logic
- **ViewModels** (`androidMain`) — own `StateFlow<UiState>`, use `viewModelScope`
- **Repositories** (`commonMain`) — suspend functions returning `NetworkResult<T>`
- **API Service** (`commonMain`) — `FootballApiService` interface, `KtorFootballApiService` impl

UI state is a sealed class per screen with `Loading`, `Success`, and `Error` variants.

## Backend Base URL

The base URL is configured in `core-network/src/commonMain/.../NetworkConfig.kt`:

```kotlin
data class NetworkConfig(val baseUrl: String = "http://10.0.2.2:8000")
```

Change this for physical device testing (use your machine's LAN IP).
