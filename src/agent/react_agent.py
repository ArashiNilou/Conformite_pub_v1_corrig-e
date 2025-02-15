from typing import Optional, List
from llama_index.core.agent import ReActAgent
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.callbacks import CallbackManager
from tools.tools import Tools
from models.ai_models import AIModels
from prompts.prompts import ReACT_prompt

def create_react_agent(
    ai_models: AIModels,
    tools: Tools,
    chat_history: Optional[List[ChatMessage]] = None,
    callback_manager: Optional[CallbackManager] = None,
    verbose: bool = False,
) -> ReActAgent:
    """
    Crée un agent ReAct configuré pour l'analyse de publicité
    
    Args:
        ai_models: Instance de AIModels contenant les modèles configurés
        tools: Instance de Tools contenant les outils disponibles
        chat_history: Historique optionnel des conversations
        callback_manager: Gestionnaire de callbacks optionnel
        verbose: Active le mode verbeux pour le débogage
    
    Returns:
        ReActAgent: Agent configuré avec les outils et le prompt système
    """
    memory = ChatMemoryBuffer.from_defaults(
        chat_history=chat_history or [],
        llm=ai_models.llm
    )
    
    system_message = ChatMessage(
        role=MessageRole.SYSTEM,
        content=ReACT_prompt
    )
    
    return ReActAgent.from_tools(
        tools=tools.tools,
        llm=ai_models.llm,
        memory=memory,
        callback_manager=callback_manager,
        verbose=verbose,
        system_message=system_message
    ) 