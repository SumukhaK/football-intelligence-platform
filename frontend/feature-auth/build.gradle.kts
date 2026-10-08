plugins {
    id("football.kmp.library")
    id("football.android.compose")
}

android {
    namespace = "com.footballintelligence.feature.auth"
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            implementation(project(":core-model"))
            implementation(project(":core-network"))
            implementation(project(":core-ui"))
            implementation(project(":core-design-system"))
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation(compose.material3)
            implementation(compose.materialIconsExtended)
            implementation(compose.ui)
            implementation(compose.components.resources)
            implementation(libs.kotlinx.coroutines.core)
        }
        androidMain.dependencies {
            implementation(compose.preview)
            implementation(libs.koin.android)
            implementation(libs.bundles.lifecycle.compose)
        }
        commonTest.dependencies {
            implementation(libs.bundles.testing.unit)
            implementation(libs.kotlinx.coroutines.test)
            implementation(libs.ktor.client.mock)
            implementation(libs.ktor.client.content.negotiation)
            implementation(libs.ktor.serialization.kotlinx.json)
        }
    }
}

compose.resources {
    packageOfResClass = "com.footballintelligence.feature.auth.resources"
}

dependencies {
    debugImplementation(compose.uiTooling)
}
