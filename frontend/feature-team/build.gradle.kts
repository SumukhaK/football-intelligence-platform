plugins {
    id("football.kmp.library")
    id("football.android.compose")
}

android {
    namespace = "com.footballintelligence.feature.team"
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            implementation(project(":core-common"))
            implementation(project(":core-model"))
            implementation(project(":core-network"))
            implementation(project(":core-ui"))
            implementation(project(":core-design-system"))
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation(compose.material3)
            implementation(compose.materialIconsExtended)
            implementation(compose.ui)
            implementation(compose.animation)
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
        }
    }
}

compose.resources {
    packageOfResClass = "com.footballintelligence.feature.team.resources"
}

dependencies {
    debugImplementation(compose.uiTooling)
}
