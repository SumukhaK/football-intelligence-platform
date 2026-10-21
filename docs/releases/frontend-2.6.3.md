# Android 2.6.3

21 October 2026. Frontend patch: version 2.6.3, code 13; staging is
`2.6.3-stg`. No tag or GitHub Release is created.

This build also carries the app side of server-saved favourites (#157,
ADR 035). It calls `GET /v2/me/preferences` after sign-in, so it needs an API
built from develop; staging's 2.6.0 API returns 404 there until it is
redeployed.

The changes come from the 21 October UX review:

- **One colour scheme.** The green top bar now draws under the status bar,
  with light status icons, on every screen. Both colour schemes set every
  neutral role (background, surface variants, containers, outlines) to
  grey-green values, so Material's default lavender no longer shows in cards,
  menus or the bottom bar.
- **Shared top bar everywhere.** Settings > My Team and the first-launch team
  picker were the only screens without `appBarColors()`; they showed a black
  (dark mode) or grey (light mode) bar. The consent screen now uses the shared
  colours too instead of its own copy.
- **Predict is a normal tab.** It no longer shows a back arrow.
- **A way out of the account check.** When the server can't confirm the
  account, the screen offers Sign out under Retry.
- **Dark mode.** Explain's factor colours use the theme's primary and error
  roles; the fixed greens were hard to read on the dark surface. Status chips
  use the design tokens instead of hex values.
- **Wording.** Titles match their tabs (Fixtures, Predict, Assistant) and every
  title and label uses sentence case. Settings rows use the Android chevron,
  and Season outlook says Retry like every other screen.

Not in this patch: opening a fixture's prediction inside the Fixtures tab,
one shared prediction summary across My Team, Result and Explain, crest
placeholders, and the larger usability items in the review.

Validation: all Android unit tests, Spotless and Detekt pass. Pixel 7
(API 35) emulator checks against a local API built from develop: Fixtures,
Settings, the team picker and Predict in light and dark mode.
