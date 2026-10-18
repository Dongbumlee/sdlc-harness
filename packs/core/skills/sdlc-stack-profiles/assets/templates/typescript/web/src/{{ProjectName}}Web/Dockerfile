# Build stage (context is this project directory)
FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
COPY package.json ./
RUN pnpm install --no-frozen-lockfile
COPY . .
RUN pnpm build

# Serve stage: static export served by nginx (typescript profile pattern)
FROM nginx:alpine AS final
COPY --from=build /app/out /usr/share/nginx/html
EXPOSE 80
