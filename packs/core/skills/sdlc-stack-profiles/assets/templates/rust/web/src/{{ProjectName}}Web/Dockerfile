# Multi-stage build — Cargo build stage, slim runtime stage.
# Build context is this project directory (the rust profile pattern).
FROM rust:1.99 AS build
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=build /app/target/release/{{project-name}}-web ./server
EXPOSE 8080
# Templates and the stylesheet are compiled into the binary.
USER 1000
ENTRYPOINT ["./server"]
