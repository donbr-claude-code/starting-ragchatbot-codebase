# 🚀 Quickstart: Playwright MCP on WSL + Claude Code

This guide shows how to set up the [Playwright MCP
server](https://github.com/microsoft/playwright-mcp) in **WSL** for use
with **Claude Code**.

------------------------------------------------------------------------

## 1. Add the MCP server

Run in your WSL shell:

``` bash
claude mcp add playwright npx @playwright/mcp@latest
```

This updates `~/.claude.json` with a new `playwright` entry.

------------------------------------------------------------------------

## 2. Create a config file

Save as `~/playwright-mcp.config.json`:

``` json
{
  "browser": {
    "browserName": "chromium",
    "launchOptions": {
      "headless": true,
      "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage"
      ]
    }
  }
}
```

-   `chromium` works in WSL without needing a full Chrome install.\
-   `--no-sandbox` + `--disable-dev-shm-usage` fix common WSL/Docker
    issues.

------------------------------------------------------------------------

## 3. Update `~/.claude.json`

Point Claude Code to your config:

``` json
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--browser", "chromium",
        "--headless",
        "--config", "/home/USER/playwright-mcp.config.json"
      ],
      "env": {},
      "cwd": "${workspaceFolder}"
    }
  }
}
```

------------------------------------------------------------------------

## 4. Verify in Claude Code

1.  Run `/mcp` → confirm `playwright` is listed.\

2.  Test navigation:

        playwright - browser_navigate (url: "http://127.0.0.1:8000")

3.  Use tools:

    -   `browser_snapshot` → structured page tree\
    -   `browser_take_screenshot` → PNG/JPEG

------------------------------------------------------------------------

## 5. Troubleshooting

-   **Error: Browser not installed**\
    Run in Claude Code chat:

        playwright - browser_install (MCP)()

-   **Connection refused**\
    Ensure your app is running in WSL
    (`uv run uvicorn app:app --reload --port 8000`).\

-   **Need fresh sessions**\
    Add `"--isolated"` to args or `isolated: true` in config.

------------------------------------------------------------------------

✅ With this setup, Claude Code can drive your local app in WSL through
Playwright MCP, returning snapshots and screenshots for fully
interactive automation.
