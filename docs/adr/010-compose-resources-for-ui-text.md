# ADR 010 — Keep UI Text in Compose Multiplatform Resources

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The project standards require all user-facing text to live in `strings.xml`
and every Composable to have a `@Preview`. The app broke both rules: about
120 strings were hard-coded across ten screens, and there were no previews.

The screens live in `commonMain` source sets of Kotlin Multiplatform modules.
Android's `res/values/strings.xml` and its generated `R` class are only
visible from Android source sets, so common code cannot use them.

## Decision

1. **Text.** Each module with UI keeps its text in
   `src/commonMain/composeResources/values/strings.xml`. Compose Multiplatform
   generates a typed `Res` class, and screens read text with
   `stringResource(Res.string.key)`. `compose.components.resources` is part
   of Compose Multiplatform and was already declared in the design-system
   module, so no new library enters the project.
2. **Package.** Each module sets `packageOfResClass` to
   `<module package>.resources`, so modules do not collide and imports are
   predictable.
3. **Shared text.** Text used by several screens (the error view, status
   chips, the back button) lives in `core-ui`, next to the shared component.
4. **Previews.** Previews live in each module's `androidMain` source set,
   using the AndroidX `@Preview` annotation that Android Studio renders. They
   wrap content in `PreviewSurface` from `core-ui`, which applies the app
   theme and supplies the Android context Compose resources need in a preview.
5. **App module.** `app/src/main/res/values/strings.xml` keeps only
   `app_name`, which the Android manifest needs.

## Consequences

- A missing or misspelt key fails compilation instead of showing wrong text.
- Text can be translated later by adding `values-<locale>/strings.xml`
  folders, without code changes.
- Placeholders use `%1$s` style. Compose resources do not unescape `%%`, so
  a literal percent sign is written as a single `%`.
- Error messages built by ViewModels (for example the text of a server
  error) are still plain strings. Moving them needs typed error states,
  which is a separate change.
- Detekt ignores `UnusedPrivateMember` and `TooManyFunctions` for
  `@Preview` functions, because only the preview renderer calls them.
