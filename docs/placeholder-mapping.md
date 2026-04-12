# Placeholder-to-Config Mapping

All placeholder tokens used in templates and their corresponding `harness-config.yml` paths.

| Placeholder | Config Path | Example Value | Filled When |
|---|---|---|---|
| `{{PROJECT_NAME}}` | `project.name` | "MyApp" | Bootstrap |
| `{{BUSINESS_DOMAIN}}` | `project.domain` | "E-commerce" | Bootstrap/Requirements |
| `{{ORG_NAME}}` | `project.org` | "Contoso" | Bootstrap |
| `{{TECH_STACK}}` | `stack.language` | "python" | Bootstrap |
| `{{FRAMEWORK}}` | `stack.framework` | "fastapi" | Bootstrap |
| `{{TEST_FRAMEWORK}}` | `stack.test_framework` | "pytest" | Bootstrap |
| `{{PACKAGE_MANAGER}}` | `stack.package_manager` | "uv" | Bootstrap |
| `{{CLOUD_PROVIDER}}` | `cloud.provider` | "azure" | Bootstrap |
| `{{IAC_TOOL}}` | `cloud.iac` | "bicep" | Bootstrap |
| `{{CI_CD}}` | `cloud.ci_cd` | "github-actions" | Bootstrap |
| `{{REGISTRY}}` | `cloud.registry` | "acr" | Bootstrap |
| `{{ARCH_STYLE}}` | `architecture.style` | "clean" | Bootstrap |

## Usage

Templates use `{{PLACEHOLDER}}` syntax. The bootstrap pipeline (`tools/bootstrap.py`) reads `harness-config.yml` and replaces all placeholders with config values.

## Files Using Placeholders

- `copilot-instructions.template.md` — Main session instructions
- `.mcp.json` / `.vscode/mcp.json` — MCP server configuration (uses `{{ORG_NAME}}` in server args)
