from typing import Optional, List, Dict, Any
from llama_index.core.agent import ReActAgent
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.callbacks import CallbackManager, CBEventType
from llama_index.core.callbacks.base_handler import BaseCallbackHandler
from tools.tools import Tools
from models.ai_models import AIModels
from prompts.prompts import ReACT_prompt

class ReActCallbackHandler(BaseCallbackHandler):
    """Handler personnalisé pour logger les événements du ReAct agent"""
    
    def __init__(self) -> None:
        super().__init__([], [])
        
    def on_event_start(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        if event_type == CBEventType.AGENT_STEP:
            print(f"\n🤖 Étape de l'agent - Début")
            if payload and "thought" in payload:
                print(f"💭 Réflexion: {payload['thought']}")
            if payload and "action" in payload:
                print(f"🎯 Action: {payload['action']}")
            if payload and "action_input" in payload:
                print(f"📥 Entrée: {payload['action_input']}")
        return event_id

    def on_event_end(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        if event_type == CBEventType.AGENT_STEP:
            if payload and "observation" in payload:
                print(f"👁️ Observation: {payload['observation']}")
            print("🤖 Étape de l'agent - Fin\n")

    def start_trace(self, trace_id: Optional[str] = None) -> None:
        print(f"\n📝 Début de la trace: {trace_id}")

    def end_trace(
        self,
        trace_id: Optional[str] = None,
        trace_map: Optional[Dict[str, Any]] = None,
    ) -> None:
        print(f"📝 Fin de la trace: {trace_id}\n")

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
    
    # Création du callback manager par défaut si non fourni
    if callback_manager is None:
        callback_manager = CallbackManager([ReActCallbackHandler()])
    
    return ReActAgent.from_tools(
        tools=tools.tools,
        llm=ai_models.llm,
        memory=memory,
        callback_manager=callback_manager,
        verbose=verbose,
        system_message=system_message
    ) 