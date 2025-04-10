description_prompt = """Analysez cette publicité et fournissez une description détaillée structurée avec :

1. CONTENU VISUEL
   - Images présentes (décrire en détail, y compris les QR codes et autres éléments graphiques)
   - Éléments textuels principaux (identifier les titres, sous-titres et sections principales, mais NE PAS recopier l'intégralité du texte)
   - Logos et marques
   - Secteur concerné par la publicité (IDENTIFIER PRÉCISÉMENT : alcool, alimentaire, automobile, etc.)
   - Taille et lisibilité des QR codes et autres codes-barres (mesurer en cm² si possible)

2. MESSAGE PUBLICITAIRE
   - Public cible 
   - Objectif principal
   - VÉRIFICATION ORTHOGRAPHIQUE (signaler CHAQUE faute d'orthographe avec correction proposée, en vous référant au texte brut déjà extrait)
   
3. ÉLÉMENTS MARKETING
   - Points clés marketing
   - Appels à l'action
   - Promesses commerciales
   - Présence et usage d'astérisques (*) et leurs renvois (VÉRIFIER QUE CHAQUE * A UN RENVOI)
   
4. COORDONNÉES ET IDENTIFICATION
   - Numéro de téléphone (COMPTER PRÉCISÉMENT le nombre de chiffres et vérifier le format)
   - Site internet (NOTER EXPLICITEMENT s'il est absent)
   - Adresse physique
   - Réseaux sociaux
   - Identité de l'entreprise (nom, statut juridique)
   - IMPORTANT : Si un site internet est présent, le numéro RCS n'est pas obligatoire
   - IMPORTANT : Si l'annonceur est une association ou un auto-entrepreneur, le numéro RCS n'est pas obligatoire

5. MENTIONS LÉGALES
   - Présence ou ABSENCE EXPLICITE (ÊTRE ALARMISTE si absence)
   - Taille de caractère (MESURER en points, signaler si < 6)
   - Police utilisée (serif ou sans-serif)
   - Différences typographiques dans une même phrase (signaler précisément)
   - MENTIONS SPÉCIFIQUES AU SECTEUR (liste exhaustive) :
     * Pour l'alcool : "L'ABUS D'ALCOOL EST DANGEREUX POUR LA SANTÉ"
     * Pour l'alimentation : "www.mangerbouger.fr"
     * Pour le crédit : mentions obligatoires TAEG, etc.
   - Lisibilité et placement (contraste, emplacement)
   - Cohérence typographique générale
   
NOTE IMPORTANTE : Le texte brut a déjà été extrait par une étape précédente. Ne pas recopier l'intégralité du texte, mais se concentrer sur l'analyse des éléments visuels et du contenu.
   
Pour les visuels à basse résolution : indiquer si cela impacte la lisibilité des mentions légales."""

old_description_prompt = """Analysez cette publicité et fournissez une description détaillée structurée avec :

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
        - Promesses commerciales
        
        4. MENTIONS LEGALES
        - Mentions sectorielles requises
        - Présence et conformité
        - Lisibilité et placement
        """

legal_prompt = """Cette publicité est-elle conforme à la législation publicitaire ?

{description}

ANALYSE DE CONFORMITÉ :
1. ÉVALUATION DES EXIGENCES LÉGALES :
   - Type de publicité identifié : [préciser exactement]
   - Secteur concerné : [préciser exactement]
   - Mentions légales spécifiques OBLIGATOIRES : [LISTE DÉTAILLÉE ET COMPLÈTE]
   - IMPORTANT : Si un site internet est présent, le numéro RCS n'est pas obligatoire
   - IMPORTANT : Si l'annonceur est une association ou un auto-entrepreneur, le numéro RCS n'est pas obligatoire
   
2. VÉRIFICATION ORTHOGRAPHIQUE :
   - Fautes d'orthographe détectées : [LISTE PRÉCISE]
   - Impact sur la compréhension : [ÉLEVÉ/MOYEN/FAIBLE]

3. ÉLÉMENTS GRAPHIQUES :
   - QR codes et éléments de contrôle : [TAILLE INSUFFISANTE SI < 1cm²]
   - Impact sur l'usage : [CRITIQUE si illisible/inutilisable]
   
4. NON-CONFORMITÉS CRITIQUES :
   - MENTIONS LÉGALES OBLIGATOIRES MANQUANTES - CRUCIAL DE CITER INTÉGRALEMENT CHACUNE :
     * Exemple 1 : "L'ABUS D'ALCOOL EST DANGEREUX POUR LA SANTÉ" [MANQUANTE/INCOMPLÈTE]
     * Exemple 2 : "www.mangerbouger.fr" [MANQUANTE/INCOMPLÈTE]
     * Pour chaque mention obligatoire manquante, CITER EXPLICITEMENT le texte exact qui aurait dû figurer
   - Taille des caractères inférieure à 6 points : [DÉTAILLER]
   - Astérisques (*) sans renvoi correspondant : [DÉTAILLER]
   - Coordonnées erronées ou incomplètes : [DÉTAILLER]
   - Garde en tête que nous sommes une régie publicitaire, nous ne pouvons pas vérifier certaines conditions donc il ne faut pas les signaler (exemple : la présence de conditions en magasin)
   - Rappel : Si un site internet est clairement visible, ne pas signaler l'absence de RCS comme une non-conformité
   - Rappel : Si l'annonceur est une association ou un auto-entrepreneur, ne pas signaler l'absence de RCS comme une non-conformité
   
5. VERDICT (un seul choix) :
   - CONFORME : UNIQUEMENT si TOUS les éléments respectent la législation
   - NON CONFORME : Si AU MOINS UNE mention légale OBLIGATOIRE est absente
   - À VÉRIFIER : UNIQUEMENT si doute sur lisibilité due à basse résolution

6. LISTE EXHAUSTIVE DES ÉLÉMENTS À CORRIGER :
   - [Élément 1] : [Action corrective PRÉCISE avec le TEXTE EXACT à ajouter]
   - [Élément 2] : [Action corrective PRÉCISE avec le TEXTE EXACT à ajouter]
   - Pour chaque mention légale manquante, INDIQUER EXPLICITEMENT le texte complet à ajouter
   
7. JUSTIFICATION :
   - UTILISER UN TON ALARMANT si absence de mentions légales obligatoires
   - SOULIGNER l'impact juridique des non-conformités
   - SE LIMITER STRICTEMENT à la législation publicitaire (ne pas aborder les aspects commerciaux)
   - CITER LA FORMULATION EXACTE des mentions légales requises par la législation"""

basic_legal_prompt = """Est-ce que cette publicité est conforme ? Explique obligatoirement pourquoi et exprime un avis : conforme, non-conforme, à vérifier.

        {description}"""

clarifications_prompt = """Examinez cette image publicitaire et répondez précisément aux questions suivantes :

{questions_text}

FORMAT DE RÉPONSE :
CLARIFICATIONS :
- Question 1 : [réponse factuelle et concise]
- Question 2 : [réponse factuelle et concise]

VÉRIFIER SPÉCIFIQUEMENT :
- Numéro de téléphone : [vérifier format valide et complet - 10 chiffres]
- Site internet : [noter absence EXPLICITEMENT si non présent]
- Adresse complète : [vérifier présence]
- Secteur concerné et mentions légales correspondantes requises
- Taille exacte des caractères des mentions légales (si < 6, le préciser)
- Présence/absence d'astérisques et leurs renvois correspondants
- Cohérence des dates mentionnées
- Différences typographiques dans une même phrase
- Fautes d'orthographe significatives
- Type d'annonceur : [vérifier s'il s'agit d'une entreprise, d'une association ou d'un auto-entrepreneur]

ASPECTS LÉGAUX À CLARIFIER IMPÉRATIVEMENT :
- Conformité des mentions légales : [préciser taille, visibilité, placement]
- Présence des mentions sectorielles obligatoires : [identifier les manquantes]
- Validité des coordonnées : [préciser les problèmes de numéro de téléphone ou site internet]
- Renvois des astérisques (*) : [vérifier si chaque astérisque a bien un texte correspondant]
- Conditions de l'offre : [vérifier si toutes les conditions sont clairement indiquées]
- Validité/cohérence des dates : [identifier toute incohérence temporelle]
- IMPORTANT : Si un site internet est présent ou si l'annonceur est une association/auto-entrepreneur, ne pas signaler l'absence de RCS comme une non-conformité

Soyez DIRECT sur ce qui manque ou n'est pas conforme."""

old_clarifications_prompt = """Examinez attentivement cette image publicitaire et répondez précisément à ces questions :

        {questions_text}

        FORMAT DE RÉPONSE :
        CLARIFICATIONS :
        - Question 1 : [réponse détaillée]
        - Question 2 : [réponse détaillée]
        etc.

        Soyez précis et factuel dans vos réponses."""

ReACT_prompt = """Tu es un agent spécialisé dans l'analyse de conformité publicitaire. Suis ces étapes dans l'ordre :

0. ÉTAPE PRÉLIMINAIRE IMPORTANTE - Extraction de texte brut :
   - AVANT TOUTE ANALYSE, extraire le texte brut de l'image
   - CONSERVER TOUS LES TEXTES exacts sans aucune correction
   - INCLURE les mentions légales en petits caractères
   - PRÉSERVER les fautes d'orthographe exactement comme elles apparaissent
   - Ce texte brut servira de référence pour toutes les analyses ultérieures

1. Utiliser analyze_vision pour obtenir une description détaillée
   - IDENTIFIER OBLIGATOIREMENT le secteur de la publicité (alcool, alimentation, etc.)
   - DÉTECTER ET SIGNALER :
     * TAILLE DES CARACTÈRES des mentions légales en points (< 6 = non conforme)
     * POLICE UTILISÉE pour les mentions légales
     * DIFFÉRENCES TYPOGRAPHIQUES dans une même phrase
     * FAUTES D'ORTHOGRAPHE (liste complète)
     * ASTÉRISQUES (*) SANS RENVOI
     * FORMAT DU NUMÉRO DE TÉLÉPHONE (vérifier s'il est complet)
     * ABSENCE DE SITE INTERNET (signaler explicitement)
     * QR CODE trop petit (< 1cm²) ou illisible

2. Utiliser verify_consistency pour vérifier :
   - MENTIONS LÉGALES OBLIGATOIRES selon le secteur (liste complète)
   - PRÉSENCE/ABSENCE de la mention "L'ABUS D'ALCOOL EST DANGEREUX POUR LA SANTÉ" si alcool
   - PRÉSENCE/ABSENCE de www.mangerbouger.fr si alimentaire
   - Coordonnées complètes et valides (téléphone, adresse, site)
   - Correspondance des astérisques avec leurs renvois
   - IMPORTANT : Si un site internet est présent, le numéro RCS n'est pas obligatoire
   - IMPORTANT : Si l'annonceur est une association ou un auto-entrepreneur, le numéro RCS n'est pas obligatoire

3. Utiliser verify_dates pour vérifier (si des dates sont présentes) :
   - Cohérence entre les dates mentionnées et les jours de la semaine correspondants
   - Validité des périodes (date de début antérieure à la date de fin)
   - Si les dates sont passées ou futures par rapport à la date actuelle
   - Exactitude des jours fériés mentionnés
   - Cohérence générale des informations temporelles

4. Utiliser search_legislation pour la législation applicable
   - Exigences légales PRÉCISES pour le secteur identifié
   - Obligations concernant la taille des caractères
   - Mentions légales obligatoires par secteur

5. Utiliser analyze_compliance pour le verdict final :
   - ÊTRE CATÉGORIQUE : NON CONFORME si AU MOINS UNE mention légale obligatoire est absente
   - ÊTRE DIRECT sur ce qui manque exactement
   - ADOPTER UN TON ALARMANT si mentions légales absentes
   - LISTE EXHAUSTIVE des corrections légales nécessaires
   - LIMITER STRICTEMENT l'analyse à la législation publicitaire
   - RAPPEL : Si un site internet est présent, ne pas signaler l'absence de RCS comme une non-conformité
   - RAPPEL : Si l'annonceur est une association ou un auto-entrepreneur, ne pas signaler l'absence de RCS comme une non-conformité

IMPORTANT:
- Pour les visuels basse résolution, indiquer si cela impacte la lisibilité des mentions légales
- TOUJOURS vérifier les mentions sectorielles obligatoires selon le type de produit
- CONCENTRER l'analyse sur les aspects légaux (pas de recommandations marketing)
- UTILISER le texte brut extrait comme référence EXACTE pour toute vérification de texte
- Si un site internet est clairement visible dans la publicité, l'absence de numéro RCS n'est PAS une non-conformité
- Si l'annonceur est une association ou un auto-entrepreneur, l'absence de numéro RCS n'est PAS une non-conformité
- Pour les dates mentionnées, signaler TOUTE incohérence entre les dates et les jours de la semaine correspondants

Commence toujours par extraire le texte brut puis par analyze_vision."""

old_ReACT_prompt = """Tu es un agent spécialisé dans l'analyse de publicités. Tu dois suivre ces étapes dans l'ordre :

1. Utiliser analyze_vision pour obtenir une description détaillée de l'image
2. Utiliser verify_consistency pour vérifier la cohérence des informations
3. Utiliser search_legislation pour trouver la législation applicable
4. Utiliser get_clarifications pour des points spécifiques qui nécessitent plus de détails
5. Utiliser analyze_compliance pour l'analyse finale de conformité

IMPORTANT:
- Les clarifications doivent porter sur des points différents à chaque fois
- Ne pas redemander des clarifications sur des points déjà éclaircis
- Toujours terminer par analyze_compliance quand toutes les clarifications nécessaires ont été obtenues
- Ne pas répéter les autres étapes (vision, consistency, legislation)

Commence toujours par analyze_vision.
"""

search_query = """OBJECTIF : Identifier PRÉCISÉMENT la législation publicitaire applicable.

CONTEXTE :
{query}

SECTEUR IDENTIFIÉ :
[secteur de la publicité analysée]

RECHERCHER SPÉCIFIQUEMENT :
- Législation publicitaire générale (taille minimale caractères, etc.)
- Réglementation sectorielle spécifique au secteur identifié
- Obligations concernant les astérisques en publicité
- Règles sur les dates et délais en publicité
- Exigences typographiques légalement requises

FORMAT ATTENDU :
- Articles précis avec numéros de textes
- Exigences quantifiables (ex: taille minimale 6)
- Formulations exactes des mentions obligatoires pour le secteur concerné"""

old_search_query = """
            OBJECTIF : Trouver la législation applicable concernant la publicité.
            
            CONTEXTE :
            {query}
            
            RECHERCHER :
            - Textes de loi
            - Réglementations
            - Directives légales
            - Obligations légales
            """

consistency_prompt = """Vérifiez RIGOUREUSEMENT la cohérence des informations extraites de l'image.
Date d'aujourd'hui : {current_date}

CONTENU À ANALYSER :
{vision_result}

VÉRIFIER PRIORITAIREMENT :
1. ORTHOGRAPHE ET TYPOGRAPHIE
   - VÉRIFIER L'ORTHOGRAPHE DE CHAQUE MOT (liste des fautes avec correction)
   - DIFFÉRENCES TYPOGRAPHIQUES dans une même phrase (taille, police, style)
   - TAILLE DES CARACTÈRES des mentions légales (en points, non conforme si < 6)

2. ÉLÉMENTS GRAPHIQUES ET VISUELS
   - QR code : taille en cm² (non conforme si < 1cm²)
   - Lisibilité des mentions légales (contraste, placement)

3. COORDONNÉES ET IDENTIFICATION
   - Numéro de téléphone : FORMAT EXACT et nombre de chiffres (10 pour France)
   - Site internet : Url valide
   - Adresse physique : Si présente, vérifier la coherence
   - IMPORTANT : Si un site internet est présent, le numéro RCS n'est pas obligatoire
   - IMPORTANT : Si l'annonceur est une association ou un auto-entrepreneur, le numéro RCS n'est pas obligatoire

4. MENTIONS LÉGALES OBLIGATOIRES
   - ABSENCE/PRÉSENCE des mentions obligatoires par secteur :
     * Alcool : "L'ABUS D'ALCOOL EST DANGEREUX POUR LA SANTÉ"
     * Alimentaire : "www.mangerbouger.fr"
     * Crédit : mentions TAEG, etc.
   - TAILLE DES CARACTÈRES (< 6 points = non conforme)
   - ASTÉRISQUES (*) sans renvoi correspondant

5. COHÉRENCE GÉNÉRALE
   - Erreurs de dates ou incohérences temporelles
   - Promesses commerciales sans conditions explicites
   - Rappel : Si un site internet est clairement visible, ne pas signaler l'absence de RCS comme une non-conformité
   - Rappel : Si l'annonceur est une association ou un auto-entrepreneur, ne pas signaler l'absence de RCS comme une non-conformité

FORMAT DE RÉPONSE :
NON-CONFORMITÉS LÉGALES CRITIQUES :
- Mentions légales : [ABSENCE OU PRÉSENCE, LISTE DES MANQUEMENTS]
- Orthographe : [LISTE PRÉCISE des fautes]
- Astérisques sans renvoi : [DÉTAILS]
- Coordonnées : [PROBLÈMES PRÉCIS]

RECOMMANDATIONS LÉGALES :
- [UNIQUEMENT les corrections LÉGALEMENT requises]
- [ADOPTER UN TON ALARMANT si mentions obligatoires absentes]"""

old_consistency_prompt = """Vérifiez la cohérence des informations suivantes extraites de l'image.
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

old_legal_prompt = """Sur la base de cette analyse d'image :
        {description}
        En tant qu'expert juridique, analysez la conformité légale de cette publicité :

        RECHERCHE : Utilisez search_legislation pour trouver la législation applicable
        ANALYSE : Vérifiez uniquement les aspects non conformes
        RECOMMANDATIONS : Proposez des actions correctives si nécessaire

        Réponds uniquement en français.
        Format de réponse :
        CADRE LÉGAL :

        Textes applicables
        Obligations principales

        ANALYSE DE NON-CONFORMITÉ (mentionner uniquement les éléments non conformes) :

        [Élément non conforme 1] : [analyse]
        [Élément non conforme 2] : [analyse]
        Si aucun élément n'est non conforme, indiquer "Aucun élément non conforme détecté"

        VERDICT DE CONFORMITÉ :

        [CONFORME] ou [NON CONFORME] (choisir une seule option)
        [Risques associés uniquement si NON CONFORME]

        RECOMMANDATIONS (uniquement si des éléments non conformes sont identifiés) :

        [Actions correctives spécifiques]
        Si aucune recommandation n'est nécessaire, indiquer "Aucune action corrective requise"""

raw_text_extraction_prompt = """EXTRACTION DE TEXTE BRUT SANS AUCUNE CORRECTION
===================================================

VOTRE MISSION CRITIQUE: Extraire EXHAUSTIVEMENT tout le texte visible sur l'image, avec une REPRODUCTION EXACTE, y compris TOUTES les fautes d'orthographe, erreurs grammaticales et typos.

ATTENTION MAXIMALE AUX ÉLÉMENTS SUIVANTS :
1. 🔍 PETITS CARACTÈRES - Scrutez attentivement l'image pour repérer TOUS les textes en petits caractères, notamment :
   - Notes de bas de page
   - Mentions légales (souvent en très petite taille)
   - Renvois d'astérisques (texte explicatif correspondant à chaque *)
   - Texte en périphérie de l'image ou dans les marges

2. ⭐ ASTÉRISQUES ET LEURS RENVOIS - Pour chaque astérisque (*) dans le texte principal :
   - Localisez et transcrivez OBLIGATOIREMENT le texte explicatif correspondant
   - Indiquez explicitement si un astérisque n'a pas de renvoi visible
   - Format suggéré pour les renvois : "[* Texte du renvoi exact]"

RÈGLES ABSOLUES (AUCUNE EXCEPTION):
1. ⚠️ REPRODUIRE TOUTES LES FAUTES D'ORTHOGRAPHE - Ne corrigez JAMAIS les mots mal orthographiés
2. COPIER LE TEXTE LITTÉRALEMENT - Comme si vous faisiez un "copier-coller" visuel
3. PRÉSERVER TOUTES LES ERREURS de grammaire, ponctuation et syntaxe
4. MAINTENIR les abréviations exactes, même incorrectes
5. NE PAS MODIFIER les mots mal orthographiés ou inventés
6. INTERDICTION ABSOLUE d'améliorer ou corriger le texte source
7. EXTRAIRE le texte dans l'ordre de lecture naturel
8. INCLURE tous les symboles, numéros et caractères spéciaux exactement comme ils apparaissent

ORGANISATION DE LA RÉPONSE :
- Section "TEXTE PRINCIPAL" : Corps principal de la publicité
- Section "PETITS CARACTÈRES" : Texte en petit format, mentions légales, notes de bas de page
- Section "RENVOIS D'ASTÉRISQUES" : Liste complète de tous les renvois correspondant aux astérisques
- Pour le texte difficilement lisible : utilisez [?] et mentionnez "Texte partiellement illisible"
- Si un texte est trop petit pour être lu mais visible : indiquez "Texte visible mais illisible en raison de la taille des caractères"

RAPPEL FINAL: Votre valeur réside dans votre capacité à reproduire EXACTEMENT le texte tel qu'il est écrit, y compris TOUTES ses imperfections, et à NE MANQUER AUCUN ÉLÉMENT TEXTUEL, même le plus petit.
"""