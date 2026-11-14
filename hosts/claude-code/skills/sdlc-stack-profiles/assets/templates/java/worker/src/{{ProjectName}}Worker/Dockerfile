# Multi-stage build — Maven build stage, JRE runtime stage.
# Build context is this project directory (the java profile pattern):
#   docker build -t {{project-name}}-worker src/{{ProjectName}}Worker
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY . .
RUN mvn -B -q package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app app
COPY --from=build /app/target/{{project-name}}-worker-0.1.0.jar app.jar
# The job database lives on a mounted volume in production (the
# <PREFIX>_DB_PATH variable points at it); the default path is for
# local runs. SIGTERM is the shutdown contract: the runner finishes
# the current job and exits.
USER app
ENTRYPOINT ["java", "-jar", "app.jar"]
