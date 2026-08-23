import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('Extensión Blood-Cipher activada.');

    // 1. Comando: Abrir Chat Interactivo en Terminal Integrada
    let disposableChat = vscode.commands.registerCommand('blood-cipher.openChat', () => {
        const terminalName = 'Blood-Cipher Agent';
        let terminal = vscode.window.terminals.find(t => t.name === terminalName);
        
        if (!terminal) {
            terminal = vscode.window.createTerminal({
                name: terminalName,
                shellPath: 'blood-cipher',
                shellArgs: ['chat']
            });
        }
        
        terminal.show();
    });

    // 2. Comando: Auditar Archivo Actual con IA
    let disposableAudit = vscode.commands.registerCommand('blood-cipher.auditFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No hay ningún archivo abierto para auditar.');
            return;
        }

        const filePath = editor.document.fileName;
        const terminal = vscode.window.createTerminal('Blood-Cipher Audit');
        terminal.show();
        terminal.sendText(`blood-cipher run "Realiza una auditoría de seguridad y calidad técnica al archivo '${filePath}' y sugiere mejoras o correcciones."`);
    });

    // 3. Comando: Abrir Asistente de Configuración
    let disposableConfig = vscode.commands.registerCommand('blood-cipher.openConfig', () => {
        const terminal = vscode.window.createTerminal('Blood-Cipher Config');
        terminal.show();
        terminal.sendText('blood-cipher config');
    });

    context.subscriptions.push(disposableChat, disposableAudit, disposableConfig);
}

export function deactivate() {}
