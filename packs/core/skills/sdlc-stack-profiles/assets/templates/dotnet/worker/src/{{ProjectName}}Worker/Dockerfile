# Build context is the repository root:
#   docker build -f src/{{ProjectName}}Worker/Dockerfile .
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY ["src/{{ProjectName}}Worker/{{ProjectName}}Worker.csproj", "{{ProjectName}}Worker/"]
RUN dotnet restore "{{ProjectName}}Worker/{{ProjectName}}Worker.csproj"
COPY src/{{ProjectName}}Worker/ {{ProjectName}}Worker/
RUN dotnet publish "{{ProjectName}}Worker/{{ProjectName}}Worker.csproj" -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/runtime:10.0 AS final
WORKDIR /app
COPY --from=build /app/publish .
USER $APP_UID
# The job database lives on a mounted volume in production (the
# <PREFIX>_DB_PATH variable points at it); the default path is for
# local runs. SIGTERM is the shutdown contract: the runner finishes
# the current job and exits.
ENTRYPOINT ["dotnet", "{{ProjectName}}Worker.dll"]
