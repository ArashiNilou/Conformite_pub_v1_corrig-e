description_prompt = """Analysez cette publicité et fournissez une description détaillée structurée avec :

1. CONTENU VISUEL
   - Images présentes (décrire en détail, y compris les QR codes et autres éléments graphiques)
   - Textes identifiés (COPIER EXACTEMENT les textes, attention à l'orthographe)
   - Logos et marques
   - Secteur concerné par la publicité
   - Taille et lisibilité des QR codes et autres codes-barres (évaluer si facilement lisibles)

2. MESSAGE PUBLICITAIRE
   - Public cible
   - Objectif principal
   - VÉRIFICATION ORTHOGRAPHIQUE (signaler TOUTE faute d'orthographe, même mineure)

3. ÉLÉMENTS MARKETING
   - Points clés marketing
   - Appels à l'action
   - Promesses commerciales
   - Présence et usage d'astérisques (*) et leurs renvois
   
4. COORDONNÉES ET IDENTIFICATION
   - Numéro de téléphone (COMPTER PRÉCISÉMENT le nombre de chiffres)
   - Site internet (NOTER EXPLICITEMENT s'il est absent)
   - Adresse physique
   - Réseaux sociaux
   - Identité de l'entreprise (nom, statut juridique, numéro RCS/SIRET si présents)

5. MENTIONS LÉGALES
   - Présence ou ABSENCE EXPLICITE
   - Type de publicité (vérifier si des mentions légales sont requises pour ce type spécifique)
   - MENTIONS SPÉCIFIQUES aux produits présentés (alcool, tabac, alimentaire, etc.)
   - Taille de caractère (estimer si inférieure à 6)
   - Lisibilité et placement
   - Cohérence typographique
   - Présence du message sanitaire www.mangerbouger.fr (si applicable)
   - Présence d'avertissements sur la consommation d'alcool (si applicable)"""

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
   - Type de publicité identifié : [type]
   - Secteur concerné : [secteur]
   - Mentions légales spécifiques requises : [LISTE DÉTAILLÉE]
   
2. VÉRIFICATION ORTHOGRAPHIQUE ET TYPOGRAPHIQUE :
   - Fautes d'orthographe détectées : [OUI/NON] - SI OUI, LISTER PRÉCISÉMENT
   - Impact sur la compréhension : [ÉLEVÉ/MOYEN/FAIBLE]

3. ÉLÉMENTS GRAPHIQUES ET VISUELS :
   - QR codes et éléments de contrôle : [TAILLE SUFFISANTE/INSUFFISANTE]
   - Impact sur l'usage : [CRITIQUE/MODÉRÉ/FAIBLE]
   
4. NON-CONFORMITÉS CRITIQUES (lister CHACUNE) :
   - Fautes d'orthographe impactantes : [DÉTAILLER]
   - Absence de mentions légales requises : [DÉTAILLER]
   - Taille des caractères inférieure au minimum légal : [DÉTAILLER]
   - Mentions sectorielles manquantes (alcool, alimentation) : [DÉTAILLER]
   - QR code ou éléments fonctionnels trop petits : [DÉTAILLER]
   - Coordonnées erronées ou incomplètes : [DÉTAILLER]

5. VERDICT (un seul choix) :
   - CONFORME : UNIQUEMENT si tous les éléments respectent la législation applicable
   - NON CONFORME : Si AU MOINS UN élément critique manque ou est incorrect
   - À VÉRIFIER : Si doutes sur certains éléments

6. LISTE EXHAUSTIVE DES ÉLÉMENTS NON CONFORMES :
   - [Élément 1] : [Précisez exactement ce qui manque ou est incorrect]
   - [Élément 2] : [Précisez exactement ce qui manque ou est incorrect]
   
7. JUSTIFICATION :
   - Expliquer PRÉCISÉMENT pourquoi le verdict a été rendu
   - Si NON CONFORME : détailler l'impact de chaque élément non conforme
   - Utiliser un TON ALARMANT si des mentions obligatoires liées à la santé sont absentes"""

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
- Adresse complète : [vérifier présence et complétude]
- Secteur concerné et mentions légales correspondantes requises
- Taille exacte des caractères des mentions légales (si < 6, le préciser)
- Présence/absence d'astérisques et leurs renvois correspondants
- Cohérence des dates mentionnées
- Différences typographiques dans une même phrase
- Fautes d'orthographe significatives

ASPECTS LÉGAUX À CLARIFIER IMPÉRATIVEMENT :
- Conformité des mentions légales : [préciser taille, visibilité, placement]
- Présence des mentions sectorielles obligatoires : [identifier les manquantes]
- Validité des coordonnées : [préciser les problèmes de numéro de téléphone ou site internet]
- Renvois des astérisques (*) : [vérifier si chaque astérisque a bien un texte correspondant]
- Conditions de l'offre : [vérifier si toutes les conditions sont clairement indiquées]
- Validité/cohérence des dates : [identifier toute incohérence temporelle]

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

1. Utiliser analyze_vision pour obtenir une description détaillée
   - IDENTIFIE D'ABORD le secteur/domaine de la publicité
   - DÉTECTE IMPÉRATIVEMENT :
     * Taille des caractères des mentions légales (signaler si < 6)
     * Mentions sectorielles requises selon le domaine identifié
     * Astérisques (*) et leurs renvois
     * Différences typographiques dans une même phrase
     * Fautes d'orthographe
     * VALIDITÉ DES COORDONNÉES (vérifier numéro de téléphone complet à 10 chiffres)
     * ABSENCE de site internet (le signaler EXPLICITEMENT)

2. Utiliser verify_consistency pour vérifier :
   - Coordonnées incomplètes ou erronées (téléphone, site internet, adresse)
   - Cohérence et validité des dates
   - Correspondance des astérisques et leurs renvois

3. Utiliser search_legislation pour la législation applicable
   - Adapte la recherche au secteur spécifique identifié
   - Inclure les obligations légales sur les coordonnées de contact

4. Utiliser get_clarifications UNIQUEMENT si critique pour la conformité légale :
   - Éléments illisibles (basse résolution)
   - Doutes sur présence/absence de mentions obligatoires
   - Format inhabituel ou suspect des coordonnées

5. Utiliser analyze_compliance pour le verdict final :
   - LISTER EXHAUSTIVEMENT tous les éléments non conformes
   - Être DIRECT sur la présence/absence de mentions légales
   - ALARMANT si mentions légales ou coordonnées essentielles absentes/erronées
   - Limité STRICTEMENT à la législation publicitaire

IMPORTANT:
- Pour les visuels basse résolution, indiquer clairement l'impact sur la conformité
- Aller à l'essentiel
- TOUJOURS vérifier la validité et complétude des coordonnées de contact

Commence toujours par analyze_vision."""

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
- OBLIGATIONS LÉGALES concernant les coordonnées de contact
- EXIGENCES concernant l'affichage des numéros de téléphone et sites internet

FORMAT ATTENDU :
- Articles précis avec numéros de textes
- Exigences quantifiables (ex: taille minimale 6)
- Formulations exactes des mentions obligatoires pour le secteur concerné
- Règles précises sur les coordonnées de contact"""

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
   - VÉRIFIER L'ORTHOGRAPHE DE CHAQUE MOT avec une attention particulière
   - Comparer les textes similaires pour détecter les incohérences (ex: "RETROUVER" vs "RETROUVEZ")
   - Signaler TOUTE faute d'orthographe, même mineure
   - VÉRIFIER l'orthographe des mots courants (personnes, invitation, etc.)

2. ÉLÉMENTS GRAPHIQUES ET VISUELS
   - QR code: taille et lisibilité (signaler explicitement si trop petit pour être scanné)
   - Lisibilité des petits caractères et mentions légales

3. COORDONNÉES ET IDENTIFICATION
   - Numéro de téléphone : COMPTER PRÉCISÉMENT le nombre de chiffres
   - Site internet : NOTER EXPLICITEMENT s'il est ABSENT
   - Adresse physique : vérifier complétude (rue, code postal, ville)
   - SIRET/RCS : vérifier présence si applicable

4. CONFORMITÉ LÉGALE
   - MENTIONS SPÉCIFIQUES AU SECTEUR (produits alimentaires, boissons alcoolisées)
   - Présence/absence du message "L'ABUS D'ALCOOL EST DANGEREUX POUR LA SANTÉ"
   - Présence/absence de www.mangerbouger.fr
   - Taille des caractères des mentions légales (< 6 ?)
   - Astérisques et leurs renvois (chaque * doit avoir un renvoi)

5. COHÉRENCE TEMPORELLE
   - Erreurs de dates (incohérentes, impossibles)
   - Périodes promotionnelles (début < fin)

FORMAT DE RÉPONSE :
ANOMALIES CRITIQUES DE CONFORMITÉ :
- Orthographe et typographie : [LISTE PRÉCISE des fautes d'orthographe]
- Éléments graphiques : [QR code trop petit/illisible]
- Coordonnées : [TÉLÉPHONE INCOMPLET, SITE INTERNET ABSENT, etc.]
- Mentions légales : [ABSENCE/présence, LISTE des mentions manquantes]
- Mentions sectorielles requises : [LISTE DÉTAILLÉE selon le secteur identifié]

RECOMMANDATIONS LÉGALES :
- [corrections STRICTEMENT nécessaires pour la conformité]"""

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