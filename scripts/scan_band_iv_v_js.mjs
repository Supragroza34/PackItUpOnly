/**
 * Scan .js/.jsx for Band IV/V style violations using Babel parser.
 * Flags a file if any function/method has body span > 30 lines or control-flow nesting > 2.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { createRequire } from "module";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const require = createRequire(import.meta.url);
const { parse } = require(path.join(ROOT, "frontend", "node_modules", "@babel", "parser"));

const EXCLUDE_DIRS = new Set([
  "node_modules", "build", "dist", "coverage", ".git", "__pycache__",
]);

function shouldSkip(p) {
  const parts = p.split(path.sep);
  return parts.some((x) => EXCLUDE_DIRS.has(x));
}

const NEST_TYPES = new Set([
  "IfStatement",
  "ForStatement",
  "ForInStatement",
  "ForOfStatement",
  "WhileStatement",
  "DoWhileStatement",
  "SwitchStatement",
  "TryStatement",
]);

function maxNesting(node, depth = 0) {
  if (!node || typeof node !== "object") return depth;
  let m = depth;
  const t = node.type;
  const next = NEST_TYPES.has(t) ? depth + 1 : depth;
  m = Math.max(m, next);
  for (const k of Object.keys(node)) {
    if (k === "loc" || k === "type" || k === "start" || k === "end") continue;
    const v = node[k];
    if (Array.isArray(v)) {
      for (const c of v) m = Math.max(m, maxNesting(c, next));
    } else if (v && typeof v === "object" && v.type) {
      m = Math.max(m, maxNesting(v, next));
    }
  }
  return m;
}

function lineSpan(loc) {
  if (!loc || !loc.start || !loc.end) return 0;
  return loc.end.line - loc.start.line + 1;
}

function walkFunctions(node, acc, classStack = []) {
  if (!node) return;
  const t = node.type;
  if (t === "FunctionDeclaration" || t === "FunctionExpression") {
    const id = node.id && node.id.name ? node.id.name : "<anonymous>";
    const span = lineSpan(node.loc);
    const nest = maxNesting(node.body, 0);
    acc.push({ kind: "fn", name: id, className: classStack[classStack.length - 1], span, nest });
  }
  if (t === "ArrowFunctionExpression") {
    const span = lineSpan(node.loc);
    const nest = maxNesting(node.body, 0);
    acc.push({ kind: "arrow", name: "<arrow>", className: classStack[classStack.length - 1], span, nest });
  }
  if (t === "ClassDeclaration" || t === "ClassExpression") {
    const cname = node.id && node.id.name ? node.id.name : "<class>";
    classStack.push(cname);
    for (const el of node.body.body || []) {
      if (el.type === "ClassMethod" || el.type === "ClassPrivateMethod") {
        const mname =
          el.key && el.key.name
            ? el.key.name
            : el.key && el.key.value
              ? String(el.key.value)
              : "<method>";
        const span = lineSpan(el.loc);
        const nest = maxNesting(el.body, 0);
        acc.push({ kind: "method", name: mname, className: cname, span, nest });
      }
    }
    classStack.pop();
  }
  for (const k of Object.keys(node)) {
    if (k === "loc" || k === "type" || k === "start" || k === "end") continue;
    const v = node[k];
    if (Array.isArray(v)) {
      for (const c of v) walkFunctions(c, acc, classStack);
    } else if (v && typeof v === "object" && v.type) {
      walkFunctions(v, acc, classStack);
    }
  }
}

function scanFile(filePath) {
  const src = fs.readFileSync(filePath, "utf8");
  const ast = parse(src, {
    sourceType: "module",
    allowReturnOutsideFunction: true,
    errorRecovery: true,
    plugins: ["jsx", "classProperties", "optionalChaining", "nullishCoalescingOperator"],
  });
  const acc = [];
  walkFunctions(ast, acc);
  return acc.filter((x) => x.span > 30 || x.nest > 2);
}

function main() {
  const violFiles = new Set();
  function walkDir(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const e of entries) {
      const full = path.join(dir, e.name);
      if (e.isDirectory()) {
        if (EXCLUDE_DIRS.has(e.name)) continue;
        walkDir(full);
      } else if (/\.(js|jsx)$/.test(e.name) && !e.name.endsWith(".min.js")) {
        if (shouldSkip(full)) continue;
        try {
          const bad = scanFile(full);
          if (bad.length) violFiles.add(path.relative(ROOT, full));
        } catch (err) {
          console.error("// parse failed:", full, err.message);
        }
      }
    }
  }
  walkDir(path.join(ROOT, "frontend", "src"));
  for (const f of [...violFiles].sort()) {
    console.log(f.replace(/\\/g, "/"));
  }
}

main();
