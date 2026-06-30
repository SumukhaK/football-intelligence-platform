import org.gradle.api.Plugin
import org.gradle.api.Project

/**
 * Adds Compose Multiplatform and the Kotlin compose compiler plugin to a module.
 * Apply after football.android.application, football.android.library, or football.kmp.library.
 */
class ComposeConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("org.jetbrains.compose")
                apply("org.jetbrains.kotlin.plugin.compose")
            }
        }
    }
}
