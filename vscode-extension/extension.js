const vscode = require('vscode');
const { spawn } = require('child_process');

let statusBarItem;

function activate(context) {
  // 1. Create and display Status Bar Item
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.command = 'tzero.openDashboard';
  statusBarItem.text = '$(zap) T-Zero: 95% Saved';
  statusBarItem.tooltip = 'Click to open T-Zero JARVIS Control Center Dashboard';
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  // 2. Register Commands
  const openDashboard = vscode.commands.registerCommand('tzero.openDashboard', () => {
    vscode.env.openExternal(vscode.Uri.parse('http://localhost:8421'));
    vscode.window.showInformationMessage('⚡ Opening T-Zero Control Center at http://localhost:8421');
  });

  const scanWorkspace = vscode.commands.registerCommand('tzero.scanWorkspace', () => {
    const term = vscode.window.createTerminal('T-Zero Scanner');
    term.show();
    term.sendText('tzero --scan .');
  });

  const auditSecurity = vscode.commands.registerCommand('tzero.auditSecurity', () => {
    const term = vscode.window.createTerminal('T-Zero Security');
    term.show();
    term.sendText('tzero --audit .');
  });

  const exportRules = vscode.commands.registerCommand('tzero.exportRules', () => {
    const term = vscode.window.createTerminal('T-Zero Rules');
    term.show();
    term.sendText('tzero --export-agent-rules');
  });

  context.subscriptions.push(openDashboard, scanWorkspace, auditSecurity, exportRules);
}

function deactivate() {
  if (statusBarItem) {
    statusBarItem.dispose();
  }
}

module.exports = {
  activate,
  deactivate
};
