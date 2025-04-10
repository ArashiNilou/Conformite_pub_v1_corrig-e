import base64
from typing import Dict, Any
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core.schema import Document, MediaResource
from llama_index.core.llms import ChatMessage, ImageBlock, TextBlock, MessageRole
from llama_index.core.tools import BaseTool, FunctionTool
from prompts.prompts import description_prompt, legal_prompt, clarifications_prompt, consistency_prompt, raw_text_extraction_prompt
from raptor.raptor_setup import RaptorSetup
from datetime import datetime
from utils.output_saver import OutputSaver
from utils.text_extractor import TextExtractor
import os
from pathlib import Path

class Tools:
    """Collection des outils disponibles pour l'analyse de publicité"""
    def __init__(self, llm: AzureOpenAI, raptor: RaptorSetup):
        self.llm = llm
        self.raptor = raptor
        self._tools = self._create_tools()
        self.vision_result = None
        self.legislation = None
        self.raw_text = None
        self.output_saver = OutputSaver()
        self.text_extractor = TextExtractor()
        self.extracted_text = None
    
    def _create_tools(self) -> list[BaseTool]:
        """Crée la liste des outils disponibles pour l'agent"""
        return [
            FunctionTool.from_defaults(
                fn=self.extract_raw_text_for_agent,
                name="extract_raw_text",
                description="Extrait le texte brut d'une image publicitaire sans aucune modification ou correction. À utiliser en PREMIER, avant toute autre analyse.",
            ),
            FunctionTool.from_defaults(
                fn=self.analyze_vision,
                name="analyze_vision",
                description="Analyse une image publicitaire et fournit une description détaillée structurée. Utilisez cet outil APRÈS l'extraction du texte brut.",
            ),
            FunctionTool.from_defaults(
                fn=self.verify_consistency,
                name="verify_consistency",
                description="Vérifie la cohérence des informations (orthographe, adresse, téléphone, email, url) après l'analyse visuelle.",
            ),
            FunctionTool.from_defaults(
                fn=self.verify_dates,
                name="verify_dates",
                description="Vérifie la cohérence des dates et des jours de la semaine mentionnés dans la publicité. Vérifie également si les dates sont futures ou passées.",
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
        
        # Vérifier si l'analyse a déjà été initialisée (par l'extraction de texte brut)
        if not self.output_saver.is_analysis_in_progress():
            self.output_saver.start_new_analysis(image_path)
        
        with open(image_path, "rb") as image_file:
            img_data = base64.b64encode(image_file.read())
        
        self._last_image_data = img_data  # Garder l'image en mémoire
        image_document = Document(image_resource=MediaResource(data=img_data))
        
        # Préparer un prompt qui inclut le texte brut déjà extrait
        enhanced_prompt = description_prompt
        if hasattr(self, 'raw_text') and self.raw_text:
            enhanced_prompt = f"""Le texte brut suivant a déjà été extrait de l'image. Utilisez-le comme référence pour votre analyse mais NE LE RECOPIEZ PAS intégralement:

TEXTE BRUT DÉJÀ EXTRAIT:
----------
{self.raw_text}
----------

{description_prompt}"""
        
        msg = ChatMessage(
            role=MessageRole.USER,
            blocks=[
                TextBlock(text=enhanced_prompt),
                ImageBlock(image=image_document.image_resource.data),
            ],
        )

        response = self.llm.chat(messages=[msg])
        result = str(response)
        
        # Supprimer le préfixe "assistant:" s'il est présent
        if result.startswith("assistant:"):
            result = result[len("assistant:"):].strip()
            
        self.vision_result = result
        
        self.output_saver.save_vision_result(self.vision_result)
        
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
        
        # Préparer un prompt qui inclut le texte brut déjà extrait
        enhanced_prompt = consistency_prompt.format(
            vision_result=vision_result,
            current_date=current_date
        )
        
        if hasattr(self, 'raw_text') and self.raw_text:
            enhanced_prompt = f"""Le texte brut suivant a déjà été extrait de l'image. Utilisez-le comme référence pour votre vérification de cohérence:

TEXTE BRUT DÉJÀ EXTRAIT:
----------
{self.raw_text}
----------

{consistency_prompt.format(vision_result=vision_result, current_date=current_date)}"""
        
        msg = ChatMessage(
            role=MessageRole.USER,
            blocks=[
                TextBlock(text=enhanced_prompt),
                ImageBlock(image=self._last_image_data),
            ],
        )
        
        response = self.llm.chat(messages=[msg])
        result = str(response)
        
        # Supprimer le préfixe "assistant:" s'il est présent
        if result.startswith("assistant:"):
            result = result[len("assistant:"):].strip()
        
        self.output_saver.save_consistency_check(result)
        
        return result

    def verify_dates(self, vision_result: str = None) -> str:
        """
        Vérifie la cohérence des dates mentionnées dans la publicité
        
        Args:
            vision_result: Résultat de l'analyse visuelle (optionnel)
            
        Returns:
            str: Rapport de vérification des dates
        """
        print("\n📅 Vérification de la cohérence des dates...")
        
        if not vision_result and not self.vision_result:
            raise ValueError("L'analyse visuelle doit être effectuée d'abord")
            
        vision_content = vision_result if vision_result else self.vision_result
        
        # Obtenir la date actuelle au format français
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        prompt = f"""VÉRIFICATION DE LA COHÉRENCE DES DATES

Date actuelle : {current_date}

CONTENU À ANALYSER :
{vision_content}

INSTRUCTIONS :
1. Extraire toutes les dates et jours de la semaine mentionnés dans la publicité
2. Pour chaque date au format JJ/MM/AAAA ou similaire :
   - Vérifier si elle correspond bien au jour de la semaine mentionné (ex: "vendredi 08/03/2025")
   - Vérifier si la date est future ou passée par rapport à aujourd'hui ({current_date})
   - Vérifier la cohérence entre les périodes (dates de début et de fin)
   - Vérifier si les jours fériés sont correctement mentionnés
3. Pour chaque jour de la semaine mentionné sans date précise :
   - Indiquer les dates possibles dans un futur proche (prochaines occurrences)

TEXTE BRUT (pour référence) :
{self.raw_text if hasattr(self, 'raw_text') and self.raw_text else "Non disponible"}

FORMAT DE RÉPONSE :
DATES IDENTIFIÉES :
- Date 1 : [format original] => [JJ/MM/AAAA] [jour de la semaine] [future/passée] [cohérente/non cohérente avec le jour mentionné]
- Date 2 : [format original] => [JJ/MM/AAAA] [jour de la semaine] [future/passée] [cohérente/non cohérente avec le jour mentionné]

PÉRIODES IDENTIFIÉES :
- Période 1 : Du [date début] au [date fin] => [durée en jours] [cohérente/non cohérente]
- Période 2 : Du [date début] au [date fin] => [durée en jours] [cohérente/non cohérente]

JOURS DE LA SEMAINE SANS DATE PRÉCISE :
- [Jour mentionné] => Prochaines occurrences : [dates]

INCOHÉRENCES DÉTECTÉES :
- [Description précise de chaque incohérence]

RECOMMANDATIONS :
- [Suggestions pour corriger les incohérences]

VERDICT DE COHÉRENCE TEMPORELLE : [COHÉRENT/NON COHÉRENT/PARTIELLEMENT COHÉRENT]
"""
        
        # Utiliser le LLM pour analyser les dates
        response = self.llm.complete(prompt)
        result = str(response)
        
        # Supprimer le préfixe "assistant:" s'il est présent
        if result.startswith("assistant:"):
            result = result[len("assistant:"):].strip()
        
        # Sauvegarder le résultat
        # La méthode save_dates_verification n'existe pas encore, nous devons l'ajouter à OutputSaver
        if hasattr(self.output_saver, 'save_dates_verification'):
            self.output_saver.save_dates_verification(result)
        else:
            # Si la méthode n'existe pas, on utilise save_custom_data ou on affiche un avertissement
            print("⚠️ La méthode save_dates_verification n'existe pas dans OutputSaver")
        
        return result

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
            
            self.output_saver.save_legislation(synthesis)
            
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
        
        # Initialiser l'historique des clarifications si nécessaire
        if not hasattr(self, '_clarifications_history'):
            self._clarifications_history = set()
        
        # Vérifier si la question a déjà été posée
        if questions_text in self._clarifications_history:
            print("⚠️ Cette clarification a déjà été demandée")
            return "Cette question a déjà été posée. Veuillez demander des clarifications sur d'autres aspects ou passer à l'analyse de conformité."
        
        # Ajouter la question à l'historique
        self._clarifications_history.add(questions_text)
        
        # Créer le message multimodal avec l'image
        msg = ChatMessage(
            role=MessageRole.USER,
            blocks=[
                TextBlock(text=clarifications_prompt.format(questions_text=questions_text)),
                ImageBlock(image=self._last_image_data),
            ],
        )
        
        print("\nEnvoi de l'image et des questions au LLM...")
        response = self.llm.chat(messages=[msg])
        result = str(response)
        
        # Supprimer le préfixe "assistant:" s'il est présent
        if result.startswith("assistant:"):
            result = result[len("assistant:"):].strip()
        
        self.output_saver.save_clarifications(result)
        
        return result

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
        result = str(response)
        
        # Supprimer le préfixe "assistant:" s'il est présent
        if result.startswith("assistant:"):
            result = result[len("assistant:"):].strip()
        
        self.output_saver.save_compliance_analysis(result)
        
        return result

    def extract_text_from_image(self, image_path: str, mode: str = "docling", ocr_engine: str = "tesseract") -> str:
        """
        Extrait le texte visible dans une image publicitaire
        
        Args:
            image_path: Chemin vers l'image à analyser
            mode: Mode d'extraction ('docling', 'pytesseract', 'easyocr')
            ocr_engine: Moteur OCR à utiliser avec Docling ('tesseract', 'easyocr', 'rapidocr')
            
        Returns:
            str: Texte extrait de l'image
        """
        print(f"\n🔤 Extraction du texte de l'image avec {mode}: {image_path}")
        
        # Configurer les options d'extraction selon le mode
        options = {}
        if mode == "docling":
            try:
                # Options avancées pour l'extraction Docling
                extracted_text = self.text_extractor.extract_text_with_docling(
                    image_path, 
                    ocr_engine=ocr_engine,
                    custom_options=options
                )
            except Exception as e:
                print(f"⚠️ Erreur avec Docling: {str(e)}. Essai d'une méthode alternative...")
                # Fallback vers une autre méthode
                extracted_text = self.text_extractor.extract_text(image_path, fallback=True)
        elif mode == "pytesseract":
            extracted_text = self.text_extractor.extract_text_with_pytesseract(image_path)
        elif mode == "easyocr":
            extracted_text = self.text_extractor.extract_text_with_easyocr_direct(image_path)
        else:
            print(f"⚠️ Mode {mode} non supporté, utilisation de la méthode générique")
            extracted_text = self.text_extractor.extract_text(image_path, fallback=True)
        
        # Si le texte est vide, afficher un avertissement
        if not extracted_text or len(extracted_text.strip()) < 5:
            print("⚠️ Attention: Très peu ou pas de texte extrait de l'image.")
        else:
            print(f"✅ Texte extrait ({len(extracted_text)} caractères)")
            
        # Sauvegarder des métadonnées supplémentaires pour l'analyse
        metadata = {
            "mode": mode,
            "ocr_engine": ocr_engine if mode == "docling" else "N/A",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "char_count": len(extracted_text),
            "success": bool(extracted_text and len(extracted_text.strip()) > 5)
        }
        
        # Sauvegarder le résultat dans les sorties
        self.output_saver.save_text_extraction(extracted_text, mode)
        self.extracted_text = extracted_text
        
        return extracted_text 

    def extract_raw_text_with_vision(self, image_path: str) -> str:
        """
        Utilise GPT Vision pour extraire le texte brut d'une image sans aucune correction orthographique
        
        Args:
            image_path: Chemin vers l'image à analyser
            
        Returns:
            str: Texte brut extrait
        """
        print(f"\n🔍 Extraction de texte brut avec GPT Vision: {image_path}")
        
        # Vérifier que l'image existe
        if not os.path.exists(image_path):
            print(f"❌ Image non trouvée: {image_path}")
            return ""
        
        # Charger l'image en base64
        with open(image_path, "rb") as image_file:
            img_data = base64.b64encode(image_file.read())
        
        # Créer le document d'image
        image_document = Document(image_resource=MediaResource(data=img_data))
        
        # Créer un message multimodal avec l'image et la demande d'extraction de texte brut
        msg = ChatMessage(
            role=MessageRole.USER,
            blocks=[
                TextBlock(text=raw_text_extraction_prompt),
                ImageBlock(image=image_document.image_resource.data),
            ],
        )
        
        # Envoyer la demande à GPT Vision
        try:
            response = self.llm.chat(messages=[msg])
            extracted_text = str(response)
            
            # Supprimer le préfixe "assistant:" s'il est présent
            if extracted_text.startswith("assistant:"):
                extracted_text = extracted_text[len("assistant:"):].strip()
            
            # Sauvegarder le résultat
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("outputs") / "raw_text"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{Path(image_path).stem}_gpt_vision_{timestamp}.txt"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            
            print(f"💾 Texte brut sauvegardé: {output_file}")
            
            return extracted_text
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction de texte avec GPT Vision: {str(e)}")
            return f"ERREUR: {str(e)}"

    def extract_raw_text_for_agent(self, image_path: str) -> str:
        """
        Extrait le texte brut d'une image publicitaire pour l'agent ReACT
        
        Args:
            image_path: Chemin vers l'image à analyser
            
        Returns:
            str: Texte brut extrait
        """
        print(f"\n📝 Extraction du texte brut pour l'agent: {image_path}")
        
        try:
            # Vérifier que l'image existe
            if not os.path.exists(image_path):
                error_msg = f"❌ Image non trouvée: {image_path}"
                print(error_msg)
                return error_msg
            
            # Initialiser une nouvelle analyse - Important: doit être fait AVANT d'essayer de sauvegarder des résultats
            self.output_saver.start_new_analysis(image_path)
            
            # Utiliser GPT Vision pour l'extraction
            result = self.extract_raw_text_with_vision(image_path)
            
            # Vérifier que le résultat n'est pas vide
            if not result or len(result.strip()) < 10:
                print("⚠️ Texte extrait trop court ou vide, mais continuons l'analyse")
            
            # Sauvegarder dans les données de l'analyse
            self.raw_text = result
            
            # Sauvegarder dans l'output_saver
            self.output_saver.save_raw_text(result)
            
            print("✅ Extraction de texte brut réussie")
            return result
            
        except Exception as e:
            error_msg = f"❌ Erreur lors de l'extraction du texte brut: {str(e)}"
            print(error_msg)
            # Même en cas d'erreur, on continue l'analyse
            print("⚠️ Continuez avec l'analyse visuelle malgré l'erreur d'extraction")
            return error_msg 