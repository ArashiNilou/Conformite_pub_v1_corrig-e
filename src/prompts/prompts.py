description_prompt = """Analysez cette publicité et fournissez une description détaillée structurée avec :

        1. CONTENU VISUEL
        - Images présentes
        - Textes identifiés
        - Logos et marques

        2. MESSAGE PUBLICITAIRE
        - Public cible
        - Objectif principal

        3. ÉLÉMENTS MARKETING
        - Points clés marketing
        - Appels à l'action
        - Promesses commerciales"""

legal_prompt = """Sur la base de cette analyse d'image :
        {description}
        
        En tant qu'expert juridique, analysez la conformité légale de cette publicité :
        1. RECHERCHE : Utilisez search_legislation pour trouver la législation applicable
        2. ANALYSE : Vérifiez la conformité pour chaque aspect légal
        3. RECOMMANDATIONS : Proposez des actions correctives
        
        Réponds uniquement en français.

        Format de réponse :
        CADRE LÉGAL :
        - Textes applicables
        - Obligations principales
        
        ANALYSE DE CONFORMITÉ :
        - Aspect 1 : [analyse]
        - Aspect 2 : [analyse]
        
        NIVEAU DE CONFORMITÉ :
        - [évaluation]
        - [risques]
        
        RECOMMANDATIONS :
        - [actions]"""

clarifications_prompt = """Examinez attentivement cette image publicitaire et répondez précisément à ces questions :

        {questions_text}

        FORMAT DE RÉPONSE :
        CLARIFICATIONS :
        - Question 1 : [réponse détaillée]
        - Question 2 : [réponse détaillée]
        etc.

        Soyez précis et factuel dans vos réponses."""

ReACT_prompt = """Tu es un agent spécialisé dans l'analyse de conformité des publicités. 
        Pour analyser une image, suis TOUJOURS ces étapes dans cet ordre :
        
        1. Utilise analyze_vision pour obtenir une description détaillée de l'image :
           analyze_vision(image_path="chemin/vers/image.jpg")
        
        2. Sauvegarde le résultat de vision et stocke-le dans une variable vision_result
        
        3. Utilise verify_consistency pour vérifier la cohérence des informations :
           verify_consistency(vision_result=vision_result)
        
        4. Utilise search_legislation avec la description obtenue :
           search_legislation(vision_result=vision_result)
        
        5. Sauvegarde la législation et stocke-la dans une variable legislation
        
        6. Utilise get_clarifications avec les résultats précédents :
           get_clarifications(
               vision_result=vision_result,
               legislation=legislation
           )
        
        7. Utilise analyze_compliance pour vérifier la conformité
        
        Ne saute JAMAIS d'étapes et respecte TOUJOURS cet ordre.
        Assure-toi de passer les bons paramètres à chaque outil."""

search_query = """
            OBJECTIF : Trouver la législation applicable concernant la publicité.
            
            CONTEXTE :
            {query}
            
            RECHERCHER :
            - Textes de loi
            - Réglementations
            - Directives légales
            - Obligations légales
            """

consistency_prompt = """Vérifiez la cohérence des informations suivantes extraites de l'image.
        Date d'aujourd'hui : {current_date}

        CONTENU À ANALYSER :
        {vision_result}
        
        VÉRIFIER :
        1. ORTHOGRAPHE
        - Fautes d'orthographe
        - Erreurs typographiques
        - Cohérence des accents
        
        2. COORDONNÉES
        - Format du numéro de téléphone (format français valide)
        - Validité de l'adresse (existence réelle)
        - Format de l'email (format valide)
        - Format et accessibilité de l'URL (syntaxe correcte)
        
        3. COHÉRENCE TEMPORELLE
        - Dates futures par rapport à aujourd'hui ({current_date})
        - Cohérence des horaires d'ouverture
        - Logique des périodes (début < fin)
        - Durée des promotions
        
        FORMAT DE RÉPONSE :
        RAPPORT DE COHÉRENCE :
        - Orthographe : [observations]
        - Coordonnées : [vérifications]
        - Temporalité : [analyse avec dates comparées à {current_date}]
        
        ANOMALIES DÉTECTÉES :
        - [liste des problèmes]
        
        RECOMMANDATIONS :
        - [suggestions de correction]
        """