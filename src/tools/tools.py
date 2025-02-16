import base64
from typing import Dict, Any
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core.schema import Document, MediaResource
from llama_index.core.llms import ChatMessage, ImageBlock, TextBlock, MessageRole
from llama_index.core.tools import BaseTool, FunctionTool
from prompts.prompts import description_prompt, legal_prompt, clarifications_prompt, consistency_prompt
from raptor.raptor_setup import RaptorSetup
from datetime import datetime

class Tools:
    """Collection des outils disponibles pour l'analyse de publicité"""
    def __init__(self, llm: AzureOpenAI, raptor: RaptorSetup):
        self.llm = llm
        self.raptor = raptor
        self._tools = self._create_tools()
        self.vision_result = None
        self.legislation = None
    
    def _create_tools(self) -> list[BaseTool]:
        """Crée la liste des outils disponibles pour l'agent"""
        return [
            FunctionTool.from_defaults(
                fn=self.analyze_vision,
                name="analyze_vision",
                description="Analyse une image publicitaire et fournit une description détaillée structurée. Utilisez cet outil en premier pour obtenir une description de l'image.",
            ),
            FunctionTool.from_defaults(
                fn=self.verify_consistency,
                name="verify_consistency",
                description="Vérifie la cohérence des informations (orthographe, adresse, téléphone, email, url) après l'analyse visuelle.",
            ),
            FunctionTool.from_defaults(
                fn=self.search_legislation,
                name="search_legislation",
                description="Recherche la législation applicable en fonction de la description de l'image. À utiliser après analyze_vision.",
            ),
            FunctionTool.from_defaults(
                fn=self.get_clarifications,
                name="get_clarifications",
                description="Obtient des clarifications spécifiques sur des aspects de la publicité en se basant sur la vision et la législation.",
            ),
            FunctionTool.from_defaults(
                fn=self.analyze_compliance,
                name="analyze_compliance",
                description="Analyse finale de la conformité de la publicité en combinant tous les résultats précédents.",
            ),
        ]
    
    @property
    def tools(self) -> list[BaseTool]:
        """Retourne la liste des outils disponibles"""
        return self._tools

    def analyze_vision(self, image_path: str) -> str:
        """
        Analyse une image publicitaire avec GPT-4V
        Args:
            image_path: Chemin vers l'image à analyser
        Returns:
            str: Description détaillée structurée de l'image
        """
        print(f"\n🖼️ Analyse de l'image: {image_path}")
        
        with open(image_path, "rb") as image_file:
            img_data = base64.b64encode(image_file.read())
        
        self._last_image_data = img_data  # Garder l'image en mémoire
        image_document = Document(image_resource=MediaResource(data=img_data))
        
        msg = ChatMessage(
            role=MessageRole.USER,
            blocks=[
                TextBlock(text=description_prompt),
                ImageBlock(image=image_document.image_resource.data),
            ],
        )

        response = self.llm.chat(messages=[msg])
        self.vision_result = str(response)
        return self.vision_result

    def verify_consistency(self, vision_result: str) -> str:
        """
        Vérifie la cohérence des informations extraites de l'image
        
        Args:
            vision_result: Résultat de l'analyse visuelle
            
        Returns:
            str: Rapport de vérification de cohérence
        """
        print("\n🔍 Vérification de la cohérence des informations...")
        
        if not self.vision_result:
            raise ValueError("L'analyse visuelle doit être effectuée d'abord")
        
        # Obtenir la date actuelle au format français
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        msg = ChatMessage(
            role=MessageRole.USER,
            blocks=[
                TextBlock(text=consistency_prompt.format(
                    vision_result=vision_result,
                    current_date=current_date
                )),
                ImageBlock(image=self._last_image_data),
            ],
        )
        
        response = self.llm.chat(messages=[msg])
        return str(response)

    def search_legislation(self, vision_result: str) -> str:
        """
        Recherche la législation applicable
        Args:
            vision_result: Résultat de l'analyse visuelle
        Returns:
            str: Législation applicable
        """
        print("\n🔍 Recherche de législation...")
        print(f"Vision result utilisé pour la recherche: {vision_result[:200]}...")
        
        try:
            # Rechercher dans la base de connaissances
            raw_legislation = self.raptor.search(vision_result)
            print(f"\nLégislation brute trouvée: {raw_legislation[:200]}...")
            
            # Stocker la législation brute
            self.legislation = raw_legislation
            
            # Utiliser le query engine pour synthétiser la réponse
            query = f"""Analyser et synthétiser la législation suivante dans le contexte de cette publicité :
            
            CONTEXTE PUBLICITAIRE :
            {vision_result}
            
            LÉGISLATION TROUVÉE :
            {raw_legislation}
            """
            
            synthesis = self.raptor.query(query)
            print(f"\nSynthèse de la législation: {synthesis[:200]}...")
            
            return synthesis
            
        except Exception as e:
            print(f"\n❌ Erreur lors de la recherche de législation: {str(e)}")
            # En cas d'erreur, utiliser la législation brute si disponible
            if raw_legislation:
                return raw_legislation
            raise

    def get_clarifications(self, questions_text: str) -> str:
        """
        Obtient des clarifications spécifiques en analysant l'image
        Args:
            questions_text: Questions spécifiques nécessitant des clarifications
        Returns:
            str: Réponses aux questions de clarification
        """
        print("\n❓ Obtention des clarifications...")
        
        if not self.vision_result or not self.legislation:
            raise ValueError("L'analyse visuelle et la recherche de législation doivent être effectuées d'abord")
        
        # Créer le message multimodal avec l'image
        msg = ChatMessage(
            role=MessageRole.USER,
            blocks=[
                TextBlock(text=clarifications_prompt.format(questions_text=questions_text)),
                ImageBlock(image=self._last_image_data),  # On garde l'image en mémoire
            ],
        )
        
        print("\nEnvoi de l'image et des questions au LLM...")
        response = self.llm.chat(messages=[msg])
        return str(response)

    def analyze_compliance(self) -> str:
        """
        Analyse finale de la conformité
        Returns:
            str: Analyse complète de la conformité
        """
        if not self.vision_result or not self.legislation:
            raise ValueError("Toutes les étapes précédentes doivent être complétées")
            
        prompt = legal_prompt.format(description=self.vision_result)
        response = self.llm.complete(prompt)
        return str(response) 