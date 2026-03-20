---
title: "Missing ES module re-export causes SyntaxError in browser"
category: build-errors
date: 2026-03-20
tags: [javascript, es-modules, import-export, static-site, chart.js]
component: dashboard
---

## Problem

Browser console shows:
```
Uncaught SyntaxError: The requested module '../charts.js' does not provide an export named 'COLORS'
```
Dashboard fails to load — blank page after login.

## Root Cause

`COLORS` was defined and exported in `utils.js`. `charts.js` imported it for internal use but did not re-export it. Multiple view files (`overview.js`, `dm-detail.js`, `compare.js`, `housing.js`) imported `COLORS` from `charts.js` instead of `utils.js`, assuming it was re-exported.

ES modules are statically analyzed — the browser rejects the import at parse time before any code runs.

## Solution

Add a re-export in `charts.js`:

```js
import { COLORS, ETHNICITY_COLORS, ... } from "./utils.js";
export { COLORS };
```

This is simpler than updating all 4+ view files to import from `utils.js` directly.

## Prevention

When a module imports constants from a utility module and multiple downstream consumers need those same constants, either:
1. **Re-export explicitly** from the intermediary module
2. **Import from the source** (`utils.js`) in all consumers — don't assume intermediaries re-export

A quick grep for the export name across all files catches this before it hits the browser:
```bash
grep -r "COLORS" dashboard/js/ --include="*.js"
```
