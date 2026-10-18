# Build context is the repository root:
#   docker build -f src/{{ProjectName}}API/Dockerfile .
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY ["src/{{ProjectName}}API/{{ProjectName}}API.csproj", "{{ProjectName}}API/"]
RUN dotnet restore "{{ProjectName}}API/{{ProjectName}}API.csproj"
COPY src/{{ProjectName}}API/ {{ProjectName}}API/
RUN dotnet publish "{{ProjectName}}API/{{ProjectName}}API.csproj" -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app
COPY --from=build /app/publish .
USER $APP_UID
EXPOSE 8080
ENTRYPOINT ["dotnet", "{{ProjectName}}API.dll"]
