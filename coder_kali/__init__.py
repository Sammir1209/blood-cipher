"""
Blood-Cipher - Agente de Inteligencia Artificial para Ciberseguridad, Hacking Ético y Auditorías en Linux.
"""

__version__ = "1.5.0"
__author__ = "Blood-Cipher Team"

from coder_kali.agent import KaliAgent
from coder_kali.config import ConfigManager
from coder_kali.system_executor import SystemExecutor
from coder_kali.tools_database import KaliToolsDatabase
from coder_kali.session_manager import SessionManager, ChatSession

__all__ = ["KaliAgent", "ConfigManager", "SystemExecutor", "KaliToolsDatabase", "SessionManager", "ChatSession", "__version__"]
