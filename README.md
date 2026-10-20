# Token Pattern Monitor

![Language: JavaScript](https://img.shields.io/badge/Language-JavaScript-F7DF1E?style=flat-square&logo=javascript) ![Chain: ethers](https://img.shields.io/badge/Chain-ethers-555555?style=flat-square) [![License: MIT](https://img.shields.io/badge/License-MIT-555555?style=flat-square)](LICENSE)

Research EVM token-contract similarities by extracting selector-like bytecode patterns, computing a compact signature and comparing deployed contracts.

The repository includes Base/Ethereum/BSC analysis scripts and a BSC event-monitoring path. Some entrypoints contain selected example addresses and providers, so inspect their constants before using them for a different investigation.

## How the compact checksum is built

In [compare_contracts.js](compare_contracts.js):

1. Scan bytecode for `PUSH4`-shaped selector candidates.
2. Deduplicate and sort the candidate selectors.
3. Concatenate their bytes and compute Keccak-256.
4. Display the first four hash bytes as a compact `#........` label.

This is a selector-set research signature, **not an EIP-55 address checksum**. A byte-pattern scan can include incidental constants, and two matching signatures do not prove equivalent contract behavior or safety.

## Explore the source surfaces

| Source | Purpose |
| --- | --- |
| [fetch_selectors.js](fetch_selectors.js) | Selector retrieval/inspection. |
| [compare_contracts.js](compare_contracts.js) | Bytecode and token metadata comparison. |
| [monitor.js](monitor.js) | Operational event-monitoring path. |
| [test_bytecode_checksum.js](test_bytecode_checksum.js) | Checksum investigation script. |

Use `npm ci --ignore-scripts` for declared Node dependencies, then `node --check compare_contracts.js` to check syntax without contacting an RPC. Running the comparison or monitor can make provider requests. Python helpers are separate research scripts; the `test` filenames do not establish a hermetic regression suite or validated detection accuracy.

**Technology:** JavaScript · ethers · axios · Python research helpers · Docker

Project-authored source: [MIT](LICENSE). Third-party components retain their own notices and terms.
