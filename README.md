# Token Pattern Monitor

A contract-pattern research toolkit that compares selectors/checksums and monitors new BSC token events.

## Features

- Selector and bytecode helpers compare contract patterns.
- A WebSocket monitor inspects new factory events.
- Optional Telegram output reports configured matches.

## Stack

JavaScript · ethers · axios · Python research helpers · Docker

Local contract templates and analysis output are file-based. No application database is declared.

## Getting started

Install declared Node dependencies without lifecycle scripts. Set WS_RPC, TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID locally only when deliberately running the monitor; syntax checks do not require them.

## How it works

```text
Factory event → contract/selector inspection → pattern comparison → optional alert
```

## Current limitations

A pattern match is not a safety or behavior guarantee. Hardcoded bot/chat/RPC configuration was replaced by environment lookups in the preparation copy. No WebSocket session or Telegram message was started.

## License

Project-authored source code is licensed under the [MIT License](LICENSE). Third-party components and datasets retain their respective rights and licenses.
