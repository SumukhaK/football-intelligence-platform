// CI-only init script: writes the shipped app's release runtime dependencies,
// every module's included, to app/gradle.lockfile so OSV-Scanner can check
// them. The build itself does not use dependency locking.
allprojects {
    if (path == ":app") {
        dependencyLocking { lockAllConfigurations() }
        tasks.register("resolveReleaseDependencies") {
            notCompatibleWithConfigurationCache("resolves configurations at execution")
            doLast {
                configurations
                    .filter { it.isCanBeResolved && it.name.endsWith("ReleaseRuntimeClasspath") }
                    // The graph is enough for the lockfile; no artifact variant is picked.
                    .forEach { it.incoming.resolutionResult.allComponents }
            }
        }
    }
}
