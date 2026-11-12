# Multi-stage build — Go build stage, distroless runtime stage.
# Build context is this project directory (the go profile pattern).
FROM golang:1.27 AS build
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -o /out/worker ./cmd/{{project-name}}

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/worker /worker
# The job database lives on a mounted volume in production (the
# <PREFIX>_DB_PATH variable points at it); the default path is for
# local runs. SIGTERM is the shutdown contract: the runner finishes
# the current job and exits.
ENTRYPOINT ["/worker"]
