plugins {
    id("football.kmp.library")
    id("football.android.compose")
}

android {
    namespace = "com.footballintelligence.core.ui"
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation(compose.material3)
            implementation(compose.ui)
            implementation(libs.coil.compose)
            implementation(compose.components.resources)
        }
        androidMain.dependencies {
            implementation(compose.preview)
            implementation(project(":core-design-system"))
        }
        commonTest.dependencies {
            implementation(libs.junit5.api)
        }
    }
}

compose.resources {
    packageOfResClass = "com.footballintelligence.core.ui.resources"
}

dependencies {
    debugImplementation(compose.uiTooling)
}
