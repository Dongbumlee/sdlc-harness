# Multi-stage build — Go build stage, distroless runtime stage.
FROM golang:1.27 AS build
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -o /out/server ./cmd/{{project-name}}

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/server /server
EXPOSE 8080
ENTRYPOINT ["/server"]
