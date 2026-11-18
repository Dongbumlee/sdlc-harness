#!/usr/bin/env node
/**
 * check-bans.mjs — the harness's edit-time mechanical gate (ban-ast layer).
 *
 * A Copilot preToolUse hook: for create / edit / apply_patch tool calls it
 * parses the incoming code with Tree Sitter (WASM grammars, vendored — no
 * install step) and denies the edit when it matches a rule in a
 * BANNED_AST.md rule file. Rule lookup, in order:
 *
 *   1. BANNED_AST.md files walking up from the edited file's directory
 *   2. ~/.BANNED_AST.md (the user's global file)
 *   3. the shipped BANNED_AST.md beside this script (the starter set)
 *
 * Escape hatch: a comment in the edited region containing
 * `<rule-name> justification: <reason>` on the matched line or up to
 * three lines above it allows that one match; the comment stays in the
 * code as the record of why.
 *
 * Failure posture: a rule MATCH is the only deny. Infrastructure failure
 * (no rule files, a grammar that fails to load, an unparseable event)
 * warns on stderr and allows the edit — a broken gate must not brick
 * every edit, and the failure is visible, never silent.
 *
 * Contract: stdin carries the hook event JSON ({toolName, toolArgs,
 * cwd}); stdout is `{}` to allow, or
 * {"permissionDecision":"deny","permissionDecisionReason":"..."}.
 */
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve, extname } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const VENDOR = join(HERE, 'vendor');

const EXT_TO_LANGUAGE = {
  '.py': 'python',
  '.ts': 'typescript',
  '.js': 'typescript',
  '.mjs': 'typescript',
  '.cjs': 'typescript',
  '.tsx': 'tsx',
  '.jsx': 'tsx',
};

// ---------- rule files ----------

function parseRuleFile(path) {
  let text;
  try {
    text = readFileSync(path, 'utf-8');
  } catch {
    return [];
  }
  const rules = [];
  const blocks = text.split(/^---\s*$/m);
  for (const block of blocks) {
    const name = block.match(/^name:\s*(\S+)\s*$/m)?.[1];
    if (!name) continue;
    const languages = (block.match(/^languages:\s*(.+)$/m)?.[1] ?? '')
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    const message = block.match(/^message:\s*(.+)$/m)?.[1]?.trim() ?? name;
    const minLen = Number(block.match(/^value-min-length:\s*(\d+)\s*$/m)?.[1] ?? 0);
    const queryMatch = block.match(/^query:\s*\|\s*\n((?:[ \t]+.*(?:\n|$))*)/m);
    if (!languages.length || !queryMatch) continue;
    const query = queryMatch[1]
      .split('\n')
      .map((line) => line.replace(/^[ \t]{1,4}/, ''))
      .join('\n')
      .trim();
    if (query) rules.push({ name, languages, message, query, minLen, source: path });
  }
  return rules;
}

function loadRulesFor(filePath) {
  const byName = new Map();
  const add = (rules) => {
    for (const rule of rules) {
      const key = `${rule.name}|${rule.languages.join(',')}|${rule.query}`;
      if (!byName.has(key)) byName.set(key, rule);
    }
  };
  // 1. walk up from the edited file
  let dir = dirname(resolve(filePath));
  for (let i = 0; i < 64; i++) {
    const candidate = join(dir, 'BANNED_AST.md');
    if (existsSync(candidate)) add(parseRuleFile(candidate));
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  // 2. the user's global file
  const global = join(homedir(), '.BANNED_AST.md');
  if (existsSync(global)) add(parseRuleFile(global));
  // 3. the shipped starter set
  add(parseRuleFile(join(HERE, 'BANNED_AST.md')));
  return [...byName.values()];
}

// ---------- event fragments ----------

function extractFragments(toolName, toolArgs) {
  const args = toolArgs ?? {};
  const name = String(toolName ?? '');
  const fragments = [];
  const push = (filePath, text) => {
    if (filePath && typeof text === 'string' && text.length) {
      fragments.push({ filePath, text });
    }
  };
  if (name.includes('apply_patch')) {
    const patch = args.patch ?? args.input ?? '';
    let current = null;
    let buffer = [];
    const flush = () => {
      if (current) push(current, buffer.join('\n'));
      buffer = [];
    };
    for (const line of String(patch).split('\n')) {
      const header = line.match(/^\*\*\* (?:Update|Add) File:\s*(.+)$/);
      if (header) {
        flush();
        current = header[1].trim();
      } else if (line.startsWith('+') && !line.startsWith('+++')) {
        buffer.push(line.slice(1));
      }
    }
    flush();
    return fragments;
  }
  const filePath = args.filePath ?? args.path ?? args.file_path;
  if (typeof args.content === 'string') push(filePath, args.content);
  if (typeof args.newString === 'string') push(filePath, args.newString);
  if (typeof args.newText === 'string') push(filePath, args.newText);
  if (Array.isArray(args.edits)) {
    for (const edit of args.edits) {
      if (typeof edit?.newString === 'string') push(filePath, edit.newString);
      if (typeof edit?.newText === 'string') push(filePath, edit.newText);
    }
  }
  return fragments;
}

// ---------- checking ----------

let parserModule = null;
const languages = new Map();

async function getLanguage(language) {
  if (languages.has(language)) return languages.get(language);
  if (!parserModule) {
    parserModule = await import('./vendor/web-tree-sitter.js');
    await parserModule.Parser.init({
      locateFile: (name) => join(VENDOR, name),
    });
  }
  const lang = await parserModule.Language.load(
    join(VENDOR, `tree-sitter-${language}.wasm`),
  );
  languages.set(language, lang);
  return lang;
}

function isJustified(lines, row, ruleName) {
  const needle = `${ruleName} justification:`;
  for (let i = Math.max(0, row - 3); i <= row && i < lines.length; i++) {
    if (lines[i].includes(needle)) return true;
  }
  return false;
}

async function checkFragment(fragment, rules, warnings) {
  const language = EXT_TO_LANGUAGE[extname(fragment.filePath).toLowerCase()];
  if (!language) return [];
  const applicable = rules.filter((r) => r.languages.includes(language));
  if (!applicable.length) return [];
  let lang;
  try {
    lang = await getLanguage(language);
  } catch (err) {
    warnings.push(`ban-ast: grammar '${language}' failed to load (${err.message}); edit allowed`);
    return [];
  }
  const { Parser, Query } = parserModule;
  const parser = new Parser();
  parser.setLanguage(lang);
  const tree = parser.parse(fragment.text);
  const lines = fragment.text.split('\n');
  const violations = [];
  for (const rule of applicable) {
    let query;
    try {
      query = new Query(lang, rule.query);
    } catch (err) {
      warnings.push(`ban-ast: rule '${rule.name}' has an invalid query (${err.message}); skipped`);
      continue;
    }
    for (const match of query.matches(tree.rootNode)) {
      const root = match.captures.find((c) => c.name === 'match')?.node;
      if (!root) continue;
      if (rule.minLen > 0) {
        const value = match.captures.find((c) => c.name === 'value')?.node;
        if (!value) continue;
        const unquoted = value.text.replace(/^['"`]|['"`]$/g, '');
        if (unquoted.length < rule.minLen) continue;
      }
      const row = root.startPosition.row;
      if (isJustified(lines, row, rule.name)) continue;
      violations.push({
        rule: rule.name,
        message: rule.message,
        filePath: fragment.filePath,
        line: row + 1,
      });
    }
  }
  return violations;
}

// ---------- main ----------

async function main() {
  const warnings = [];
  let raw = '';
  process.stdin.setEncoding('utf-8');
  for await (const chunk of process.stdin) raw += chunk;
  let event;
  try {
    event = JSON.parse(raw);
  } catch {
    process.stderr.write('ban-ast: unparseable hook event; edit allowed\n');
    process.stdout.write('{}');
    return;
  }
  const cwd = event.cwd ?? process.cwd();
  const fragments = extractFragments(event.toolName, event.toolArgs).map((f) => ({
    ...f,
    filePath: resolve(cwd, f.filePath),
  }));
  if (!fragments.length) {
    process.stdout.write('{}');
    return;
  }
  const violations = [];
  for (const fragment of fragments) {
    const rules = loadRulesFor(fragment.filePath);
    if (!rules.length) continue;
    try {
      violations.push(...(await checkFragment(fragment, rules, warnings)));
    } catch (err) {
      warnings.push(`ban-ast: check failed for ${fragment.filePath} (${err.message}); edit allowed`);
    }
  }
  for (const warning of warnings) process.stderr.write(`${warning}\n`);
  if (violations.length) {
    const details = violations
      .map((v) => `- **${v.rule}** in \`${v.filePath}\` line ${v.line}: ${v.message}`)
      .join('\n');
    const hint =
      'If this usage is strictly necessary, retry the edit with a comment ' +
      'containing `<rule-name> justification: <reason>` on the matched line ' +
      'or just above it — the comment stays in the code as the record.';
    process.stdout.write(
      JSON.stringify({
        permissionDecision: 'deny',
        permissionDecisionReason: `Banned AST pattern(s) detected:\n\n${details}\n\n${hint}\n`,
      }),
    );
    return;
  }
  process.stdout.write('{}');
}

main().catch((err) => {
  process.stderr.write(`ban-ast: unexpected failure (${err.message}); edit allowed\n`);
  process.stdout.write('{}');
});
