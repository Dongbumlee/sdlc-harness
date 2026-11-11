# Multi-stage build — cargo release build stage, distroless cc runtime.
FROM rust:1.99 AS build
WORKDIR /app
COPY . .
RUN cargo build --release

FROM gcr.io/distroless/cc-debian12:nonroot
COPY --from=build /app/target/release/{{project-name}} /server
EXPOSE 8080
ENTRYPOINT ["/server"]
