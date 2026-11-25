<!-- SPDX-License-Identifier: LicenseRef-TOKEN-NC-Research-1.0 -->
# Dependency licences (M6, 2026-11-25)

Generated in this session from installed metadata: Python packages from the repository `.venv` after `uv sync --frozen --all-groups --all-extras` (`importlib.metadata`: `License-Expression`, else the licence classifiers); npm packages from every `package.json` under `demo/node_modules` after `npm ci --prefer-offline` in a clean clone (the `license` field). No dependency is committed or redistributed by this repository: `.venv/` and `node_modules/` are ignored, and the demo build bundles only React and React DOM (MIT).

Accepted without a flag: MIT, BSD, ISC, Apache-2.0, PSF-2.0, MPL-2.0. Anything else is flagged below.

## Flags

- **numpy 2.3.4 (runtime):** the package licence is BSD-3-Clause, but the wheel's `LICENSE.txt` lists bundled third-party components, including libgfortran under GPL-3.0-or-later WITH GCC-exception-3.1. The runtime library exception permits use by non-GPL programs; this repository neither modifies nor redistributes numpy. Noted for the owner, not a blocker.
- **MPL-2.0 (lightningcss, lightningcss-darwin-arm64; build only):** weak copyleft on the files of those packages; used by the Vite build, not modified or redistributed. Accepted by the brief's list; noted.
- **token-lab 0.1.0 (this project):** TOKEN Source-Available Non-Commercial Research License v1.0 (`LICENSE`), the repository's own licence.
- **Build toolchain outside the repository (read-only, not dependencies of the package):** pandoc 3.6.3 (prints "free software; see the source for copying conditions"; its upstream licence is GPL-2.0-or-later, from the pandoc project, not re-verified in this session), typst 0.15.0 (Apache-2.0, from metadata), pypdf 6.20.0 (BSD-3-Clause, from metadata). Their output (PDFs) is not covered by their licences.
- No package reports an unknown or missing licence.

## Python (14 distributions in `.venv`)

| Package | Version | Licence (metadata) | Role |
|---|---|---|---|
| attrs | 26.1.0 | MIT | runtime (via jsonschema) |
| iniconfig | 2.3.1 | MIT | dev (via pytest) |
| jsonschema | 4.25.1 | MIT | runtime |
| jsonschema-specifications | 2025.9.1 | MIT | runtime (via jsonschema) |
| numpy | 2.3.4 | BSD License | runtime |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | dev (via pytest) |
| pluggy | 1.7.0 | MIT License | dev (via pytest) |
| psutil | 7.1.0 | BSD-3-Clause | runtime |
| Pygments | 2.21.0 | BSD-2-Clause | dev (via pytest) |
| pytest | 8.4.2 | MIT License | dev (tests) |
| referencing | 0.37.0 | MIT | runtime (via jsonschema) |
| rpds-py | 2026.9.1 | MIT | runtime (via jsonschema) |
| token-lab | 0.1.0 | TOKEN SOURCE-AVAILABLE NON-COMMERCIAL RESEARCH LICENSE | this project |
| typing_extensions | 4.16.0 | PSF-2.0 | runtime (via referencing) |

## npm (53 packages in `demo/node_modules`)

| Package | Version | Licence (package.json) | Role |
|---|---|---|---|
| @jridgewell/sourcemap-codec | 1.6.0 | MIT | build or test only |
| @oxc-project/types | 0.156.0 | MIT | build or test only |
| @rolldown/binding-darwin-arm64 | 1.2.19 | MIT | build or test only |
| @rolldown/pluginutils | 1.1.1 | MIT | build or test only |
| @standard-schema/spec | 1.1.0 | MIT | build or test only |
| @types/chai | 5.2.3 | MIT | build or test only |
| @types/deep-eql | 4.0.2 | MIT | build or test only |
| @types/estree | 1.0.11 | MIT | build or test only |
| @types/react | 19.3.0 | MIT | build or test only |
| @types/react-dom | 19.3.0 | MIT | build or test only |
| @vitejs/plugin-react | 6.1.2 | MIT | build or test only |
| @vitest/expect | 4.1.12 | MIT | build or test only |
| @vitest/mocker | 4.1.12 | MIT | build or test only |
| @vitest/pretty-format | 4.1.12 | MIT | build or test only |
| @vitest/runner | 4.1.12 | MIT | build or test only |
| @vitest/snapshot | 4.1.12 | MIT | build or test only |
| @vitest/spy | 4.1.12 | MIT | build or test only |
| @vitest/utils | 4.1.12 | MIT | build or test only |
| assertion-error | 2.0.1 | MIT | build or test only |
| chai | 6.3.0 | MIT | build or test only |
| convert-source-map | 2.0.0 | MIT | build or test only |
| csstype | 3.2.4 | MIT | build or test only |
| detect-libc | 2.1.2 | Apache-2.0 | build or test only |
| es-module-lexer | 2.3.2 | MIT | build or test only |
| estree-walker | 3.0.3 | MIT | build or test only |
| expect-type | 1.4.0 | Apache-2.0 | build or test only |
| fdir | 6.5.0 | MIT | build or test only |
| fsevents | 2.3.3 | MIT | build or test only |
| lightningcss | 1.33.0 | MPL-2.0 | build or test only |
| lightningcss-darwin-arm64 | 1.33.0 | MPL-2.0 | build or test only |
| magic-string | 0.30.21 | MIT | build or test only |
| nanoid | 3.3.20 | MIT | build or test only |
| obug | 2.2.1 | MIT | build or test only |
| pathe | 2.0.3 | MIT | build or test only |
| picocolors | 1.1.1 | ISC | build or test only |
| picomatch | 4.0.7 | MIT | build or test only |
| postcss | 8.5.33 | MIT | build or test only |
| react | 19.3.1 | MIT | runtime (bundled in the demo) |
| react-dom | 19.3.1 | MIT | runtime (bundled in the demo) |
| rolldown | 1.2.19 | MIT | build or test only |
| scheduler | 0.28.0 | MIT | build or test only |
| siginfo | 2.0.0 | ISC | build or test only |
| source-map-js | 1.2.4 | BSD-3-Clause | build or test only |
| stackback | 0.0.2 | MIT | build or test only |
| std-env | 4.3.0 | MIT | build or test only |
| tinybench | 2.9.0 | MIT | build or test only |
| tinyexec | 1.4.0 | MIT | build or test only |
| tinyglobby | 0.2.17 | MIT | build or test only |
| tinyrainbow | 3.2.0 | MIT | build or test only |
| typescript | 5.9.3 | Apache-2.0 | build or test only |
| vite | 8.3.5 | MIT | build or test only |
| vitest | 4.1.12 | MIT | build or test only |
| why-is-node-running | 2.3.0 | MIT | build or test only |
