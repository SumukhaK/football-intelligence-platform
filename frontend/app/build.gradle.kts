plugins {
    id("football.android.application")
    id("football.android.compose")
}

android {
    namespace = "com.footballintelligence.app"

    defaultConfig {
        applicationId = "com.footballintelligence.app"
        versionCode = 1
        versionName = "0.2.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
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

    implementation(compose.runtime)
    implementation(compose.ui)
    implementation(compose.material3)
    implementation(compose.foundation)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.ktor.client.android)
    implementation(libs.koin.android)
    implementation(libs.koin.androidx.compose)
    implementation(libs.bundles.lifecycle.compose)
    implementation(libs.napier)
    implementation(libs.androidx.core.ktx)
    implementation(libs.kotlinx.coroutines.android)

    testImplementation(libs.junit5.api)
    testRuntimeOnly(libs.junit5.engine)
}
