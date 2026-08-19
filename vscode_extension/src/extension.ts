import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('Extensión Coder-Kali activada.');

    // 1. Comando: Abrir Chat Interactivo en Terminal Integrada
    let disposableChat = vscode.commands.registerCommand('coder-kali.openChat', () => {
        const terminalName = 'Coder-Kali Agent';
        let terminal = vscode.window.terminals.find(t => t.name === terminalName);
        
        if (!terminal) {
            terminal = vscode.window.createTerminal({
                name: terminalName,
                shellPath: 'coder-kali',
                shellArgs: ['chat']
            });
        }
        
        terminal.show();
    });

    // 2. Comando: Auditar Archivo Actual con IA
    let disposableAudit = vscode.commands.registerCommand('coder-kali.auditFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No hay ningún archivo abierto para auditar.');
            return;
        }

        const filePath = editor.document.fileName;
        const terminal = vscode.window.createTerminal('Coder-Kali Audit');
        terminal.show();
        terminal.sendText(`coder-kali run "Realiza una auditoría de seguridad y calidad técnica al archivo '${filePath}' y sugiere mejoras o correcciones."`);
    });

    // 3. Comando: Abrir Asistente de Configuración
    let disposableConfig = vscode.commands.registerCommand('coder-kali.openConfig', () => {
        const terminal = vscode.window.createTerminal('Coder-Kali Config');
        terminal.show();
        terminal.sendText('coder-kali config');
    });

    context.subscriptions.push(disposableChat, disposableAudit, disposableConfig);
}

export function deactivate() {}
