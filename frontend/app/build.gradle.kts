import java.util.Properties

plugins {
    id("football.android.application")
    id("football.android.compose")
}

// The staging API's HTTPS address, kept out of Git: `staging.baseUrl` in
// local.properties, or -PstagingBaseUrl=... on the command line.
val stagingBaseUrl: String =
    providers.gradleProperty("stagingBaseUrl").orNull
        ?: Properties()
            .apply {
                rootProject
                    .file("local.properties")
                    .takeIf { it.exists() }
                    ?.reader()
                    ?.use(::load)
            }.getProperty("staging.baseUrl", "")

android {
    namespace = "com.footballintelligence.app"

    defaultConfig {
        applicationId = "com.footballintelligence.app"
        versionCode = 4
        versionName = "2.1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    // local talks to the API on this PC (the emulator's 10.0.2.2); staging is
    // a separate app beside it, pointed at the hosted staging API.
    flavorDimensions += "environment"
    productFlavors {
        create("local") {
            dimension = "environment"
            buildConfigField("String", "BASE_URL", "\"http://10.0.2.2:8000\"")
        }
        create("staging") {
            dimension = "environment"
            applicationIdSuffix = ".stg"
            versionNameSuffix = "-stg"
            buildConfigField("String", "BASE_URL", "\"$stagingBaseUrl\"")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }
}

dependencies {
    implementation(project(":core-common"))
    implementation(project(":core-model"))
    implementation(project(":core-network"))
    implementation(project(":core-design-system"))
    implementation(project(":core-navigation"))
    implementation(project(":core-ui"))
    implementation(project(":feature-home"))
    implementation(project(":feature-prediction"))
    implementation(project(":feature-assistant"))
    implementation(project(":feature-settings"))
    implementation(project(":feature-team"))
    implementation(project(":feature-auth"))

    implementation(compose.runtime)
    implementation(compose.ui)
    implementation(compose.material3)
    implementation(compose.foundation)
    implementation(compose.materialIconsExtended)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.ktor.client.android)
    implementation(libs.koin.android)
    implementation(libs.koin.androidx.compose)
    implementation(libs.bundles.lifecycle.compose)
    implementation(libs.napier)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.core.splashscreen)
    implementation(libs.kotlinx.coroutines.android)

    testImplementation(libs.junit5.api)
    testRuntimeOnly(libs.junit5.engine)
}

// A staging APK with no address would install and then fail every request,
// so asking for one by name fails at once. `assembleDebug` and the like still
// build it with an empty address, so a local build needs no staging URL.
val stagingUrlIsSet = stagingBaseUrl.startsWith("https://")
val stagingRequested = gradle.startParameter.taskNames.any { it.contains("Staging") }
tasks
    .matching { it.name.matches(Regex("(assemble|bundle|install)Staging.*")) }
    .configureEach {
        // Local copies, so the action holds Booleans, not the build script.
        val urlIsSet = stagingUrlIsSet
        val requested = stagingRequested
        doFirst {
            check(urlIsSet || !requested) {
                "Set staging.baseUrl=https://... in frontend/local.properties"
            }
        }
    }
