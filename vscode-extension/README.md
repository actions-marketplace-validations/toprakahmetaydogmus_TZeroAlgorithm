# T-Zero Context Architect — VS Code & Cursor Extension

Official Visual Studio Code and Cursor extension for **T-Zero Context Architect**.

## Features
- **Live Status Bar Counter**: Shows token reduction stats right inside your IDE (`⚡ T-Zero: 95% Saved`).
- **One-Click Control Center**: Direct launch to the cyberpunk local dashboard (`localhost:8421`).
- **One-Click AI Rules**: Generate `.cursorrules`, `.cursor/rules/*.mdc`, and Copilot rules with a single command.
- **Zero-Leak Security**: Real-time secret and API credential audit.

## Packaging
To build the `.vsix` package:
```bash
npx -y @vscode/vsce package
```
Then install in Cursor or VS Code:
```bash
code --install-extension tzero-context-architect-6.0.0.vsix
```
