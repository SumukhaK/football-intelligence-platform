plugins {
    `kotlin-dsl`
}

group = "com.footballintelligence.buildlogic"

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

dependencies {
    compileOnly(libs.android.gradlePlugin)
    compileOnly(libs.kotlin.gradlePlugin)
    compileOnly(libs.compose.gradlePlugin)
}

gradlePlugin {
    plugins {
        register("androidApplication") {
            id = "football.android.application"
            implementationClass = "AndroidApplicationConventionPlugin"
        }
        register("androidLibrary") {
            id = "football.android.library"
            implementationClass = "AndroidLibraryConventionPlugin"
        }
        register("kmpLibrary") {
            id = "football.kmp.library"
            implementationClass = "KmpLibraryConventionPlugin"
        }
        register("androidCompose") {
            id = "football.android.compose"
            implementationClass = "ComposeConventionPlugin"
        }
    }
}
