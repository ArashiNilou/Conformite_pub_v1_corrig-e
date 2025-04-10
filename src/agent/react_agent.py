from typing import Optional, List, Dict, Any
from llama_index.core.agent import ReActAgent
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.callbacks import CallbackManager, CBEventType
from llama_index.core.callbacks.base_handler import BaseCallbackHandler
from tools.tools import Tools
from models.ai_models import AIModels
from prompts.prompts import ReACT_prompt
from utils.token_counter import TokenCounter, create_token_counter

class ReActCallbackHandler(BaseCallbackHandler):
    """Handler personnalisé pour logger les événements du ReAct agent"""
    
    def __init__(self) -> None:
        super().__init__([], [])
        self.token_counter = None
        
    def set_token_counter(self, token_counter: TokenCounter) -> None:
        """Définir le compteur de tokens pour ce handler."""
        self.token_counter = token_counter
        
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
                if self.token_counter:
                    self.token_counter.set_current_step("agent_thinking")
            if payload and "action" in payload:
                print(f"🎯 Action: {payload['action']}")
                if self.token_counter:
                    action = payload["action"]
                    if action == "analyze_vision":
                        self.token_counter.set_current_step("vision_analysis")
                    elif action == "verify_consistency":
                        self.token_counter.set_current_step("consistency_check")
                    elif action == "verify_dates":
                        self.token_counter.set_current_step("dates_verification")
                    elif action == "search_legislation":
                        self.token_counter.set_current_step("legislation_search")
                    elif action == "get_clarifications":
                        self.token_counter.set_current_step("clarifications")
                    elif action == "analyze_compliance":
                        self.token_counter.set_current_step("compliance_analysis")
                    elif action == "extract_raw_text":
                        self.token_counter.set_current_step("raw_text_extraction")
                    else:
                        self.token_counter.set_current_step("other")
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
        
        # Afficher les statistiques de tokens à la fin
        if trace_id == "root" and self.token_counter:
            print("\n📊 Statistiques finales de tokens:")
            self.token_counter.print_step_stats()
            self.token_counter.save_stats()

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
        react_handler = ReActCallbackHandler()
        token_counter = create_token_counter(verbose=True, save_dir="stats/tokens")
        callback_manager = CallbackManager([react_handler, token_counter])
        
        # Connecter le compteur de tokens au handler ReAct
        react_handler.set_token_counter(token_counter)
    else:
        # Chercher s'il y a un compteur de tokens dans le callback_manager
        for handler in callback_manager.handlers:
            if isinstance(handler, TokenCounter):
                # Chercher s'il y a un ReActCallbackHandler et lui connecter le compteur de tokens
                for other_handler in callback_manager.handlers:
                    if isinstance(other_handler, ReActCallbackHandler):
                        other_handler.set_token_counter(handler)
                        break
                break
    
    return ReActAgent.from_tools(
        tools=tools.tools,
        llm=ai_models.llm,
        memory=memory,
        callback_manager=callback_manager,
        verbose=verbose,
        system_message=system_message,
        max_iterations=30
    ) 