# Build context is this project directory:
#   docker build -f src/{{ProjectName}}Worker/Dockerfile src/{{ProjectName}}Worker
FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
COPY package.json ./
RUN pnpm install --no-frozen-lockfile
COPY . .
RUN pnpm build

FROM node:22-alpine AS final
WORKDIR /app
COPY --from=build /app/dist ./dist
# The job database lives on a mounted volume in production (the
# <PREFIX>_DB_PATH variable points at it); the default path is for
# local runs. SIGTERM is the shutdown contract: the runner finishes
# the current job and exits.
USER node
CMD ["node", "dist/index.js"]
