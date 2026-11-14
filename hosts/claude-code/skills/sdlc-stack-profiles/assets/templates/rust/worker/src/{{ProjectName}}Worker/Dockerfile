# Multi-stage build — Cargo build stage, slim runtime stage.
# Build context is this project directory (the rust profile pattern).
FROM rust:1.99 AS build
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=build /app/target/release/{{project-name}}-worker ./worker
# The job database lives on a mounted volume in production (the
# <PREFIX>_DB_PATH variable points at it); the default path is for
# local runs. SIGTERM is the shutdown contract: the runner finishes
# the current job and exits.
USER 1000
ENTRYPOINT ["./worker"]
