from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from pathlib import Path
from llama_index.core.callbacks import TokenCountingHandler as LlamaIndexTokenCounter
from llama_index.core.callbacks import CallbackManager, CBEventType
from llama_index.core.callbacks.base_handler import BaseCallbackHandler
import tiktoken
import os
import logging

class TokenCounter(LlamaIndexTokenCounter):
    """Un compteur de tokens amélioré qui suit l'utilisation des tokens par étape."""
    
    def __init__(
        self,
        tokenizer=None,
        verbose: bool = False,
        save_filepath: Optional[str] = None
    ):
        """
        Initialiser le compteur de tokens amélioré.
        
        Args:
            tokenizer: Tokenizer à utiliser (par défaut: None, utilise celui de LlamaIndex)
            verbose: Afficher les informations de comptage en temps réel
            save_filepath: Chemin où sauvegarder les statistiques (optionnel)
        """
        if tokenizer is None:
            try:
                tokenizer = tiktoken.encoding_for_model("gpt-4o").encode
                print(f"✅ Tokenizer 'gpt-4o' chargé avec succès")
            except Exception as e:
                print(f"⚠️ Impossible de charger le tokenizer: {str(e)}")
                # Fallback sur cl100k_base qui est généralement disponible
                try:
                    tokenizer = tiktoken.get_encoding("cl100k_base").encode
                    print(f"✅ Tokenizer 'cl100k_base' chargé avec succès (fallback)")
                except Exception as e:
                    print(f"❌ Impossible de charger le tokenizer de fallback: {str(e)}")
        
        # Initialiser le compteur de tokens de base
        super().__init__(tokenizer=tokenizer)
        
        # Modification: assurer que nous surveillons les bons événements
        self._event_starts_to_watch = []
        self._event_ends_to_watch = [CBEventType.LLM, CBEventType.EMBEDDING]
        
        self.verbose = verbose
        self.save_filepath = save_filepath
        self.total_cost = 0.0
        
        # Suivi des tokens par étape
        self.steps_token_usage = {
            "raw_text_extraction": {"prompt": 0, "completion": 0, "embedding": 0, "total": 0, "cost": 0.0},
            "vision_analysis": {"prompt": 0, "completion": 0, "embedding": 0, "total": 0, "cost": 0.0},
            "consistency_check": {"prompt": 0, "completion": 0, "embedding": 0, "total": 0, "cost": 0.0},
            "dates_verification": {"prompt": 0, "completion": 0, "embedding": 0, "total": 0, "cost": 0.0},
            "legislation_search": {"prompt": 0, "completion": 0, "embedding": 0, "total": 0, "cost": 0.0},
            "clarifications": {"prompt": 0, "completion": 0, "embedding": 0, "total": 0, "cost": 0.0},
            "compliance_analysis": {"prompt": 0, "completion": 0, "embedding": 0, "total": 0, "cost": 0.0},
            "agent_thinking": {"prompt": 0, "completion": 0, "embedding": 0, "total": 0, "cost": 0.0},
            "other": {"prompt": 0, "completion": 0, "embedding": 0, "total": 0, "cost": 0.0}
        }
        
        # Étape courante
        self.current_step = "other"
        
        # Compteur d'embedding précédent pour calculer la différence
        self.previous_embedding_count = 0
    
    def on_event_end(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        """
        Intercepter les événements LLM et EMBEDDING pour compter les tokens par étape.
        """
        # Appeler d'abord la méthode parente pour compter les tokens globaux
        super().on_event_end(event_type, payload, event_id, **kwargs)
        
        # Traiter spécifiquement les événements LLM
        if event_type == CBEventType.LLM and payload:
            # Récupérer les tokens du dernier appel LLM depuis les compteurs globaux de la classe parente
            if hasattr(payload, 'prompt_tokens_count'):
                prompt_tokens = payload.get("prompt_tokens_count", 0)
            else:
                # Si le compteur global a augmenté, prendre la différence depuis la dernière fois
                last_step_total = sum(step["prompt"] for step in self.steps_token_usage.values())
                prompt_tokens = self.prompt_llm_token_count - last_step_total
                
            if hasattr(payload, 'completion_tokens_count'):
                completion_tokens = payload.get("completion_tokens_count", 0)
            else:
                # Si le compteur global a augmenté, prendre la différence depuis la dernière fois
                last_step_total = sum(step["completion"] for step in self.steps_token_usage.values())
                completion_tokens = self.completion_llm_token_count - last_step_total
            
            model_name = payload.get("model_name", "gpt-4o")
            
            # Utiliser les tokens reportés par LlamaIndex si disponibles dans le payload
            if "prompt_tokens" in payload and payload["prompt_tokens"] > 0:
                prompt_tokens = payload["prompt_tokens"]
            
            if "completion_tokens" in payload and payload["completion_tokens"] > 0:
                completion_tokens = payload["completion_tokens"]
            
            # Si on a toujours 0 tokens et qu'on a un tokenizer, essayer de compter directement
            if prompt_tokens == 0 and self.tokenizer and "prompt" in payload:
                prompt_str = str(payload["prompt"])
                prompt_tokens = len(self.tokenizer(prompt_str))
            
            if completion_tokens == 0 and self.tokenizer and "response" in payload:
                completion_str = str(payload["response"])
                completion_tokens = len(self.tokenizer(completion_str))
            
            # Ajouter les tokens à l'étape courante
            if self.current_step in self.steps_token_usage:
                self.steps_token_usage[self.current_step]["prompt"] += prompt_tokens
                self.steps_token_usage[self.current_step]["completion"] += completion_tokens
                self.steps_token_usage[self.current_step]["total"] += prompt_tokens + completion_tokens
                
                # Calculer le coût
                prompt_cost = self._calculate_cost(prompt_tokens, model_name, is_prompt=True)
                completion_cost = self._calculate_cost(completion_tokens, model_name, is_prompt=False)
                self.steps_token_usage[self.current_step]["cost"] += (prompt_cost + completion_cost)
                
                if self.verbose:
                    print(f"\n💰 Tokens pour l'étape {self.current_step}:")
                    print(f"   Prompt: +{prompt_tokens} tokens")
                    print(f"   Completion: +{completion_tokens} tokens")
                    print(f"   Total étape: {self.steps_token_usage[self.current_step]['total']} tokens")
                    print(f"   Coût étape: ${self.steps_token_usage[self.current_step]['cost']:.5f}")
        
        # Traiter spécifiquement les événements EMBEDDING
        elif event_type == CBEventType.EMBEDDING and payload:
            embedding_tokens = 0
            model_name = payload.get("model_name", "text-embedding-3-large")
            
            # Calculer les tokens d'embedding pour cette étape
            current_embedding_count = self.total_embedding_token_count
            embedding_tokens = current_embedding_count - self.previous_embedding_count
            self.previous_embedding_count = current_embedding_count
            
            # Si les tokens d'embedding sont dans le payload, les utiliser
            if "embedding_tokens" in payload:
                embedding_tokens = payload["embedding_tokens"]
            
            # Ajouter les tokens d'embedding à l'étape courante
            if self.current_step in self.steps_token_usage and embedding_tokens > 0:
                self.steps_token_usage[self.current_step]["embedding"] += embedding_tokens
                self.steps_token_usage[self.current_step]["total"] += embedding_tokens
                
                # Calculer le coût des embeddings
                embedding_cost = self._calculate_cost(embedding_tokens, model_name, is_embedding=True)
                self.steps_token_usage[self.current_step]["cost"] += embedding_cost
                
                if self.verbose:
                    print(f"\n💰 Tokens d'embedding pour l'étape {self.current_step}:")
                    print(f"   Embedding: +{embedding_tokens} tokens")
                    print(f"   Total étape: {self.steps_token_usage[self.current_step]['total']} tokens")
                    print(f"   Coût étape: ${self.steps_token_usage[self.current_step]['cost']:.5f}")
    
    def set_current_step(self, step_name: str) -> None:
        """
        Définir l'étape actuelle pour le suivi des tokens.
        
        Args:
            step_name: Nom de l'étape
        """
        if step_name not in self.steps_token_usage:
            self.steps_token_usage[step_name] = {"prompt": 0, "completion": 0, "embedding": 0, "total": 0, "cost": 0.0}
        
        self.current_step = step_name
        
        if self.verbose:
            print(f"🔄 Étape de suivi des tokens: {step_name}")
    
    def _calculate_cost(self, num_tokens: int, model_name: str, is_prompt: bool = True, is_embedding: bool = False) -> float:
        """
        Calculer le coût approximatif basé sur le nombre de tokens et le modèle.
        
        Args:
            num_tokens: Nombre de tokens
            model_name: Nom du modèle
            is_prompt: Si True, calcule le coût du prompt, sinon de la completion
            is_embedding: Si True, calcule le coût des embeddings
            
        Returns:
            float: Coût estimé en dollars
        """
        # Prix par 1000 tokens (convertis depuis les prix par million affichés sur la page de tarification d'OpenAI)
        # https://openai.com/api/pricing/
        pricing = {
            # GPT-4o: $2.5/M input, $10/M output -> $0.0025/K input, $0.01/K output
            "gpt-4o": {"prompt": 0.0025, "completion": 0.01},
            # GPT-4: $30/M input, $60/M output -> $0.03/K input, $0.06/K output
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            # GPT-4 Turbo: $10/M input, $30/M output -> $0.01/K input, $0.03/K output
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            # GPT-3.5 Turbo: $0.5/M input, $1.5/M output -> $0.0005/K input, $0.0015/K output
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
            # GPT-4 Vision: comme GPT-4 Turbo
            "gpt-4-vision-preview": {"prompt": 0.01, "completion": 0.03},
            # Embedding models
            # text-embedding-3-large: $0.13/M -> $0.00013/K
            "text-embedding-3-large": {"embedding": 0.00013},
            # text-embedding-3-small: $0.02/M -> $0.00002/K
            "text-embedding-3-small": {"embedding": 0.00002},
            # text-embedding-ada-002: $0.10/M -> $0.0001/K
            "text-embedding-ada-002": {"embedding": 0.0001},
        }
        
        # Chercher le modèle correspondant (modèle exact ou correspondance partielle)
        model_key = None
        for key in pricing.keys():
            if key in model_name.lower():
                model_key = key
                break
        
        if not model_key:
            # Modèle par défaut si non trouvé
            if is_embedding:
                model_key = "text-embedding-3-large"
            else:
                model_key = "gpt-4o"
            
        # Calculer le coût
        if is_embedding:
            cost_per_token = pricing[model_key].get("embedding", 0.00013)
        else:
            cost_type = "prompt" if is_prompt else "completion"
            default_cost = 0.0025 if is_prompt else 0.01  # GPT-4o par défaut
            cost_per_token = pricing[model_key].get(cost_type, default_cost)
        
        # Le prix est par 1000 tokens, donc diviser le nombre de tokens par 1000
        return (num_tokens / 1000.0) * cost_per_token
    
    def update_costs(self) -> None:
        """Mettre à jour les coûts pour toutes les étapes et le total."""
        total_cost = 0.0
        
        # Calculer le coût total des étapes
        for step_name, step_stats in self.steps_token_usage.items():
            total_cost += step_stats["cost"]
        
        self.total_cost = total_cost
    
    def get_step_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtenir les statistiques d'utilisation des tokens par étape.
        
        Returns:
            Dict: Statistiques d'utilisation des tokens par étape
        """
        # Mettre à jour les coûts avant de renvoyer les statistiques
        self.update_costs()
        return self.steps_token_usage
    
    def print_step_stats(self) -> None:
        """Afficher les statistiques d'utilisation des tokens par étape."""
        # Vérifier si tous les tokens ont été attribués à des étapes
        total_step_prompt = sum(step["prompt"] for step in self.steps_token_usage.values())
        total_step_completion = sum(step["completion"] for step in self.steps_token_usage.values())
        total_step_embedding = sum(step["embedding"] for step in self.steps_token_usage.values())
        
        # Si des tokens ne sont pas attribués, les ajouter à "other"
        if total_step_prompt < self.prompt_llm_token_count:
            missing_prompt = self.prompt_llm_token_count - total_step_prompt
            self.steps_token_usage["other"]["prompt"] += missing_prompt
            self.steps_token_usage["other"]["total"] += missing_prompt
            print(f"⚠️ {missing_prompt} tokens de prompt non attribués ont été ajoutés à 'other'")
            
        if total_step_completion < self.completion_llm_token_count:
            missing_completion = self.completion_llm_token_count - total_step_completion
            self.steps_token_usage["other"]["completion"] += missing_completion
            self.steps_token_usage["other"]["total"] += missing_completion
            print(f"⚠️ {missing_completion} tokens de completion non attribués ont été ajoutés à 'other'")
            
        if total_step_embedding < self.total_embedding_token_count:
            missing_embedding = self.total_embedding_token_count - total_step_embedding
            self.steps_token_usage["other"]["embedding"] += missing_embedding
            self.steps_token_usage["other"]["total"] += missing_embedding
            print(f"⚠️ {missing_embedding} tokens d'embedding non attribués ont été ajoutés à 'other'")
        
        self.update_costs()
        
        print("\n" + "="*60)
        print("📊 UTILISATION DES TOKENS PAR ÉTAPE")
        print("="*60)
        
        for step_name, stats in self.steps_token_usage.items():
            if stats["total"] > 0:  # N'afficher que les étapes qui ont été utilisées
                print(f"\n⚙️ {step_name.upper()}:")
                print(f"  Tokens prompt:     {stats['prompt']:,}")
                print(f"  Tokens completion: {stats['completion']:,}")
                if stats["embedding"] > 0:
                    print(f"  Tokens embedding:  {stats['embedding']:,}")
                print(f"  Tokens totaux:     {stats['total']:,}")
                print(f"  Coût estimé:       ${stats['cost']:.4f}")
        
        print("\n💰 TOTAUX:")
        print(f"  Tokens prompt:     {self.prompt_llm_token_count:,}")
        print(f"  Tokens completion: {self.completion_llm_token_count:,}")
        print(f"  Tokens embedding:  {self.total_embedding_token_count:,}")
        print(f"  Tokens totaux:     {self.total_llm_token_count + self.total_embedding_token_count:,}")
        print(f"  Coût total estimé: ${self.total_cost:.4f}")
        
        print("\n" + "="*60)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtenir les statistiques complètes d'utilisation des tokens.
        
        Returns:
            Dict: Statistiques d'utilisation des tokens
        """
        # Vérifier si tous les tokens ont été attribués à des étapes
        total_step_prompt = sum(step["prompt"] for step in self.steps_token_usage.values())
        total_step_completion = sum(step["completion"] for step in self.steps_token_usage.values())
        total_step_embedding = sum(step["embedding"] for step in self.steps_token_usage.values())
        
        # Si des tokens ne sont pas attribués, les ajouter à "other"
        if total_step_prompt < self.prompt_llm_token_count:
            missing_prompt = self.prompt_llm_token_count - total_step_prompt
            self.steps_token_usage["other"]["prompt"] += missing_prompt
            self.steps_token_usage["other"]["total"] += missing_prompt
            
        if total_step_completion < self.completion_llm_token_count:
            missing_completion = self.completion_llm_token_count - total_step_completion
            self.steps_token_usage["other"]["completion"] += missing_completion
            self.steps_token_usage["other"]["total"] += missing_completion
            
        if total_step_embedding < self.total_embedding_token_count:
            missing_embedding = self.total_embedding_token_count - total_step_embedding
            self.steps_token_usage["other"]["embedding"] += missing_embedding
            self.steps_token_usage["other"]["total"] += missing_embedding
        
        self.update_costs()
        
        return {
            "total_prompt_tokens": self.prompt_llm_token_count,
            "total_completion_tokens": self.completion_llm_token_count,
            "total_embedding_tokens": self.total_embedding_token_count,
            "total_tokens": self.total_llm_token_count + self.total_embedding_token_count,
            "estimated_cost_usd": self.total_cost,
            "steps": self.steps_token_usage,
            "timestamp": datetime.now().isoformat()
        }
    
    def save_stats(self) -> None:
        """Sauvegarder les statistiques dans un fichier JSON."""
        if not self.save_filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stats_dir = Path("stats/tokens")
            stats_dir.mkdir(parents=True, exist_ok=True)
            self.save_filepath = str(stats_dir / f"token_stats_{timestamp}.json")
        
        # Créer le répertoire parent si nécessaire
        save_path = Path(self.save_filepath)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.get_stats(), f, ensure_ascii=False, indent=2)
                
            if self.verbose:
                print(f"💾 Statistiques sauvegardées dans: {save_path}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde des statistiques: {str(e)}")
    
    def log_tokens_for_step(self, prompt_tokens: int = 0, completion_tokens: int = 0, embedding_tokens: int = 0) -> None:
        """
        Enregistrer manuellement l'utilisation des tokens pour l'étape actuelle.
        
        Args:
            prompt_tokens: Nombre de tokens du prompt
            completion_tokens: Nombre de tokens de la completion
            embedding_tokens: Nombre de tokens d'embedding
        """
        self.steps_token_usage[self.current_step]["prompt"] += prompt_tokens
        self.steps_token_usage[self.current_step]["completion"] += completion_tokens
        self.steps_token_usage[self.current_step]["embedding"] += embedding_tokens
        total_tokens = prompt_tokens + completion_tokens + embedding_tokens
        self.steps_token_usage[self.current_step]["total"] += total_tokens
        
        # Mettre à jour le coût
        prompt_cost = self._calculate_cost(prompt_tokens, "gpt-4o", True)
        completion_cost = self._calculate_cost(completion_tokens, "gpt-4o", False)
        embedding_cost = self._calculate_cost(embedding_tokens, "text-embedding-3-large", is_embedding=True)
        self.steps_token_usage[self.current_step]["cost"] += prompt_cost + completion_cost + embedding_cost
        
        if self.verbose:
            print(f"\n💰 Tokens pour l'étape {self.current_step}:")
            if prompt_tokens > 0:
                print(f"   Prompt: +{prompt_tokens} tokens")
            if completion_tokens > 0:
                print(f"   Completion: +{completion_tokens} tokens")
            if embedding_tokens > 0:
                print(f"   Embedding: +{embedding_tokens} tokens")
            print(f"   Total étape: {self.steps_token_usage[self.current_step]['total']} tokens")

def create_token_counter(verbose: bool = True, save_dir: str = "stats/tokens") -> TokenCounter:
    """
    Créer un compteur de tokens amélioré avec un chemin de sauvegarde par défaut.
    
    Args:
        verbose: Afficher les informations de comptage en temps réel
        save_dir: Répertoire où sauvegarder les statistiques
        
    Returns:
        TokenCounter: Compteur de tokens configuré
    """
    # Créer un nom de fichier avec horodatage
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = Path(save_dir) / f"token_stats_{timestamp}.json"
    
    # S'assurer que le répertoire existe
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    return TokenCounter(
        verbose=verbose,
        save_filepath=str(save_path)
    )

def add_token_counting(callback_manager: CallbackManager, verbose: bool = True) -> TokenCounter:
    """
    Ajouter un compteur de tokens amélioré à un CallbackManager existant.
    
    Args:
        callback_manager: CallbackManager auquel ajouter le compteur
        verbose: Afficher les informations de comptage en temps réel
        
    Returns:
        TokenCounter: Compteur de tokens ajouté
    """
    counter = create_token_counter(verbose=verbose)
    callback_manager.add_handler(counter)
    return counter 