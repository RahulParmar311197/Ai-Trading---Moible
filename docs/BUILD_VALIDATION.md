# Build Validation

## Android

- Java: 17
- Android Gradle Plugin: 8.7.3
- Kotlin: 2.0.21
- Gradle distribution: 8.10.2
- CI build command: `gradle --no-daemon assembleDebug` from `android/`

The pinned Gradle distribution is recorded in `android/gradle/wrapper/gradle-wrapper.properties`.

The official Gradle wrapper scripts/JAR are still pending. Until they are checked in and `./gradlew assembleDebug` is validated, the Android foundation is not considered fully buildable locally.

## Backend

CI installs `backend/requirements.txt` with Python 3.12 and runs `pytest -q`.

## Completion rule

Do not mark Stage 0 build validation complete based only on configuration files. The actual build/test command must pass.
