# Build context is the repository root:
#   docker build -f src/{{ProjectName}}Web/Dockerfile .
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY ["src/{{ProjectName}}Web/{{ProjectName}}Web.csproj", "{{ProjectName}}Web/"]
RUN dotnet restore "{{ProjectName}}Web/{{ProjectName}}Web.csproj"
COPY src/{{ProjectName}}Web/ {{ProjectName}}Web/
RUN dotnet publish "{{ProjectName}}Web/{{ProjectName}}Web.csproj" -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app
COPY --from=build /app/publish .
USER $APP_UID
EXPOSE 8080
ENTRYPOINT ["dotnet", "{{ProjectName}}Web.dll"]
