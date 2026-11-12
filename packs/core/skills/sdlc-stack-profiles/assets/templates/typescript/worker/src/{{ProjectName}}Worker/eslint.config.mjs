// ESLint flat config — the pinned lint baseline for every scaffolded
// TypeScript library (typescript-eslint recommended set).
// CI runs `pnpm lint`; do not run a second linter alongside it.
import { defineConfig, globalIgnores } from "eslint/config";
import tseslint from "typescript-eslint";

const eslintConfig = defineConfig([
  ...tseslint.configs.recommended,
  globalIgnores(["dist/**", "coverage/**", "etc/**"]),
]);

export default eslintConfig;
