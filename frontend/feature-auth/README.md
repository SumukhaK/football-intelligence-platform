# :feature-auth

Invite-only sign-in, redeeming an invite, and the consent notice (ADR 022).

## Ownership

Presentation layer. Depends on `core-model`, `core-network`, `core-ui`, `core-design-system`.

## Contents

- `AuthScreen` — a green header with the Kick-off logo over a sheet with two tabs, Sign in and Invite code, which can be tapped or swiped (a `HorizontalPager` synced with a segmented button row).
- `AuthViewModel`, `AuthForm`, `AuthUiState` — the typed fields and the request state. Each backend error has its own message: 401 wrong email or password, 429 too many tries, 400 bad invite code, 422 password too short, 403 blocked; anything else uses the app's usual error wording. A new password shorter than 10 characters is caught before sending.
- `ConsentScreen`, `ConsentViewModel`, `ConsentUiState` — checks `GET /v2/me`; if the current notice needs accepting, shows the server's text with a "Store my question text" switch (off by default) and accepts with `POST /v2/me/consent`. An outdated notice (403) is fetched again. Offline, it moves on so saved data still shows.
- `SignOutViewModel` — the Sign out entry in Settings.
- `AuthRepository` — sign in, redeem invite, sign out, `me` and consent, over `AuthApiService` and `AuthSession` from `core-network`.
- `PreferencesTokenStore` — the session token in private SharedPreferences (`session`). App backup is off, so it never leaves the device.

## Constraints

- TDD: ViewModel tests written before implementation.
- No hardcoded strings; the notice text comes from the server.
- Navigation lives in `app` (`AuthRoutes.kt`): losing the session from any screen returns to sign-in.
