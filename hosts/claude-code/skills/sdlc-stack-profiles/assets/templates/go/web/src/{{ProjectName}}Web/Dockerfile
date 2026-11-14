# Multi-stage build — Go build stage, distroless runtime stage.
# Build context is this project directory (the go profile pattern).
# Templates and static assets are embedded in the binary, so the
# runtime image is the binary and nothing else.
FROM golang:1.27 AS build
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -o /out/server ./cmd/{{project-name}}

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/server /server
EXPOSE 8080
ENTRYPOINT ["/server"]
