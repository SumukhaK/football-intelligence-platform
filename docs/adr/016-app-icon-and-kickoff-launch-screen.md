# ADR 016 — App Icon and the Kick-off Launch Screen

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The app shipped with Android's default launcher icon and no launch screen, and
every loading state used a generic Material spinner. Five icon and five launch
screen concepts were reviewed
([concepts page](../design/icon-splash-concepts.html)). The owner chose icon 3
(Tactics Board) and launch screen S4 (Kick-off), and asked for the Kick-off
animation to be used wherever the app shows loading.

## Decision

1. **Launcher icon.** An adaptive icon, `mipmap-anydpi-v26/ic_launcher`, with a
   pitch-green background, the Tactics Board vector foreground, and a
   monochrome layer so Android 13+ can tint it as a themed icon. Everything
   sits inside the 66dp safe zone of the 108dp canvas. The app's minimum is
   API 26, so no bitmap icons are needed.
2. **Launch screen.** AndroidX `core-splashscreen` 1.0.1 shows the Kick-off
   ring on brand green. On Android 12+ it is an animated vector, where home,
   draw and away arcs fill in under a second. On Android 8 to 11 the library
   shows the finished ring as a still image. Using the library gives one code
   path for every version and avoids a separate launch activity.
3. **Loading indicator.** `KickoffLoader` in `core-ui` draws the same ring
   animation in Compose. It replaces every `CircularProgressIndicator` and the
   pull-to-refresh spinner. It reports itself to accessibility services as an
   indeterminate progress bar labelled "Loading". The probability bars stay as
   they are, because they show values, not loading.

## Alternatives rejected

- **A launch Activity with its own layout.** It adds a screen to the back stack
  and still shows the system's own splash first on Android 12+.
- **Material's default spinner for loading.** It works, but it misses the
  chance to repeat the brand motion the owner picked.

## Consequences

- New dependency: `androidx.core:core-splashscreen`.
- The launch animation and `KickoffLoader` are separate implementations of the
  same motion (vector XML and Compose). A change to one should be mirrored in
  the other.
