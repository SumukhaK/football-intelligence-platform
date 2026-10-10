# Ktor's logging references SLF4J's binder, which Android doesn't ship; the
# app logs through Napier, so the missing class is never loaded.
-dontwarn org.slf4j.impl.StaticLoggerBinder
