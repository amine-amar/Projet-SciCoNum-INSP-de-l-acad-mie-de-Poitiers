import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import folium
from folium.plugins import MarkerCluster, Fullscreen
from folium.features import DivIcon
from streamlit_folium import st_folium
import unicodedata
import requests
import json
import re
import os
import numpy as np
from PIL import Image

# ==========================================
# 1. CONFIGURATION ET DONNÉES STATIQUES
# ==========================================
st.set_page_config(page_title="Analyse Production Écrite", page_icon="📊", layout="wide")

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
<style>
    /* Style des Onglets */
    .stTabs [data-baseweb="tab"] { 
        font-size: 1.1rem; 
        font-weight: 600; 
        padding: 1rem;
        border-radius: 5px;
    }
    .stTabs [data-baseweb="tab"]:hover { 
        color: #FF4B4B; 
        background-color: #f0f2f6;
    }
    .stTabs [aria-selected="true"] { 
        color: #FF4B4B; 
        border-bottom-color: #FF4B4B; 
    }

    /* Style de la Navigation Latérale */
    [data-testid="stSidebar"] .stRadio label {
        padding-top: 15px !important;
        padding-bottom: 15px !important;
        font-size: 1.05rem !important;
        color: #262730;
        border-bottom: 1px solid #f0f2f6;
    }
    [data-testid="stSidebar"] h1 {
        font-size: 1.5rem !important;
        padding-bottom: 20px;
        border-bottom: 2px solid #FF4B4B;
    }
    
    /* Style des Metrics (KPI) */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #0e1117;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        font-weight: bold;
        color: #555;
    }
    
    /* Style encadrés infos */
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- CHEMIN D'ACCÈS SPÉCIFIQUE ---
DOSSIER_CIBLE = r"C:\Users\mammar03\Desktop\Questionnaire LimeSurvey_Apprentissage et enseignement de la production écrite à l'école... testez vos connaissances\Analyse_347_questionnaire"
NOM_FICHIER_BASE = "471"

# MAPPING DES PARTIES
PARTIES_INFO = {
    "total_partie_2": {"titre": "Fonctionnement et développement de la production écrite chez les élèves", "short": "P2. Fonctionnement", "max_points": 32},
    "total_partie_3": {"titre": "Interventions pour améliorer la production écrite (inclus élèves en difficulté)", "short": "P3. Interventions", "max_points": 28},
    "total_partie_4": {"titre": "Des outils numériques pour enseigner et apprendre la production écrite", "short": "P4. Outils Num.", "max_points": 24},
    "total _partie_5": {"titre": "Évaluation de la production écrite", "short": "P5. Évaluation", "max_points": 16}
}

# --- DÉFINITION DES GROUPES DE FUSION ---
LISTE_FI = [
    "Étudiant ou étudiante au sein du master MEEF1 mention 1er degré, en M1",
    "Étudiant ou étudiante au sein du master MEEF1 mention 1er degré, en M2",
    "Fonctionnaire stagiaire mi-temps (PEES mi-temps), 1er degré",
    "Fonctionnaire stagiaire temps-complet (PEES temps complet) 1er degré,"
]

LISTE_FC = [
    "Enseignant Titulaire (fonctionnaire),",
    "Enseignant Remplaçant,",
    "Enseignant Contractuel,"
]

NAME_FI = "🟦(FI) FORMATION INITIALE (Fusion)"
NAME_FC = "🟦(FC) FORMATION CONTINUE (Fusion)"

# Coordonnées des Rectorats
INFO_RECTORATS = {
    "poitiers": {"nom": "Académie de Poitiers", "addr": "22 Rue Guillaume VII, 86000 Poitiers", "coord": [46.5818, 0.3374]},
    "paris": {"nom": "Académie de Paris", "addr": "12 boulevard d'Indochine, 75019 Paris", "coord": [48.8872, 2.3952]},
    "versailles": {"nom": "Académie de Versailles", "addr": "3 boulevard de Lesseps, 78017 Versailles", "coord": [48.8053, 2.1350]},
    "creteil": {"nom": "Académie de Créteil", "addr": "4 rue Georges Enesco, 94000 Créteil", "coord": [48.7973, 2.4469]},
    "bordeaux": {"nom": "Académie de Bordeaux", "addr": "5 rue Joseph de Carayon-Latour, 33060 Bordeaux", "coord": [44.8378, -0.5792]},
    "nancy-metz": {"nom": "Académie de Nancy-Metz", "addr": "2 rue Philippe de Gueldres, 54035 Nancy", "coord": [48.6921, 6.1833]},
    "normandie": {"nom": "Académie de Normandie", "addr": "25 rue de Fontenelle, 76037 Rouen", "coord": [49.4432, 1.0993]},
    "lille": {"nom": "Académie de Lille", "addr": "144 rue de Bavay, 59033 Lille", "coord": [50.6292, 3.0573]},
    "montpellier": {"nom": "Académie de Montpellier", "addr": "31 rue de l'Université, 34064 Montpellier", "coord": [43.6111, 3.8767]},
    "toulouse": {"nom": "Académie de Toulouse", "addr": "75 rue Saint-Roch, 31400 Toulouse", "coord": [43.6045, 1.4442]},
    "orleans-tours": {"nom": "Académie d'Orléans-Tours", "addr": "21 rue Saint-Étienne, 45069 Orléans", "coord": [47.9030, 1.9093]},
    "amiens": {"nom": "Académie d'Amiens", "addr": "20 boulevard d'Alsace-Lorraine, 80063 Amiens", "coord": [49.8942, 2.2957]},
    "guadeloupe": {"nom": "Académie de la Guadeloupe", "coord": [16.2625, -61.5036], "addr": "97139 Les Abymes"},
    "martinique": {"nom": "Académie de la Martinique", "coord": [14.6295, -61.0850], "addr": "97200 Schoelcher"},
    "guyane": {"nom": "Académie de la Guyane", "coord": [4.9224, -52.3135], "addr": "97300 Cayenne"},
    "reunion": {"nom": "Académie de la Réunion", "coord": [-20.9015, 55.4807], "addr": "97400 Saint-Denis"},
    "mayotte": {"nom": "Académie de Mayotte", "coord": [-12.7806, 45.2315], "addr": "97600 Mamoudzou"}
}

# ==========================================
# 2. CHARGEMENT ET PRÉPARATION
# ==========================================
@st.cache_data
def load_data():
    df = None
    loaded_path = None
    
    chemins_possibles = [
        os.path.join(DOSSIER_CIBLE, NOM_FICHIER_BASE + ".xlsx"),
        os.path.join(DOSSIER_CIBLE, NOM_FICHIER_BASE + ".csv"),
        NOM_FICHIER_BASE + ".xlsx",
        "Questionnaire_347_réponses.xlsx - Apprentissage de la Production.csv"
    ]
    
    for chemin in chemins_possibles:
        if os.path.exists(chemin):
            try:
                if chemin.endswith('.xlsx'):
                    df = pd.read_excel(chemin)
                else:
                    df = pd.read_csv(chemin)
                    if len(df.columns) < 2: df = pd.read_csv(chemin, sep=';')
                loaded_path = chemin
                break
            except Exception as e:
                continue
                
    return df, loaded_path

@st.cache_data
def fetch_geojson(url):
    try:
        r = requests.get(url)
        return json.loads(r.content.decode('utf-8-sig'))
    except: return None

def normalize_text(text):
    return "".join(c for c in unicodedata.normalize('NFD', str(text)) if unicodedata.category(c) != 'Mn').lower()

def get_acad_key(name):
    n = normalize_text(name)
    for k in INFO_RECTORATS:
        if k in n: return k
    return None

def get_centroid(feature):
    try:
        if feature['geometry']['type'] == 'Polygon':
            coords = feature['geometry']['coordinates'][0]
        elif feature['geometry']['type'] == 'MultiPolygon':
            polys = feature['geometry']['coordinates']
            coords = max(polys, key=lambda x: len(x[0]))[0]
        else: return None
        lons = [p[0] for p in coords]
        lats = [p[1] for p in coords]
        return [sum(lats)/len(lats), sum(lons)/len(lons)]
    except: return None

# Chargement
df_raw, path_loaded = load_data()

if df_raw is None:
    pass 

if df_raw is not None:
    df = df_raw.copy()
    
    # Nettoyage scores
    total_cols = [c for c in df.columns if "total" in c.lower() and "repondeur" in c.lower()]
    cols_to_clean = total_cols + list(PARTIES_INFO.keys())
    for col in cols_to_clean:
        if col in df.columns:
             df[col] = pd.to_numeric(df[col].astype(str).str.extract(r'(\d+)', expand=False), errors='coerce').fillna(0)

    # Identification Colonnes
    cols_statut = [c for c in df.columns if "statut" in c.lower() and "autre" not in c.lower()]
    col_statut = cols_statut[0] if cols_statut else df.columns[2]
    
    cols_statut_autre = [c for c in df.columns if "statut" in c.lower() and "autre" in c.lower()]
    col_statut_autre = cols_statut_autre[0] if cols_statut_autre else None

    # Correction Académie
    col_academie_list = [c for c in df.columns if "académie" in c.lower()]
    col_academie = col_academie_list[0] if col_academie_list else df.columns[10] 

    if col_academie:
        df[col_academie] = df[col_academie].astype(str).str.strip()
        mask_poitiers = df[col_academie].str.contains("Poitiers", case=False, na=False)
        df.loc[mask_poitiers, col_academie] = "Académie de Poitiers"

    col_coords = [c for c in df.columns if "ville vous exercez" in c.lower()]
    col_coords = col_coords[0] if col_coords else None
    col_plan = [c for c in df.columns if "plan français" in str(c).lower()]

    # Calcul Match
    if 'total_partie_2' in df.columns and 'total_partie_3' in df.columns:
        df['Pct_Theorie'] = (df['total_partie_2'] / 32) * 100
        df['Pct_Pratique'] = (df['total_partie_3'] / 28) * 100
        df['Profil_Match'] = df.apply(lambda row: "Pragmatiques" if (row['Pct_Pratique'] - row['Pct_Theorie']) > 5 else ("Théoriciens" if (row['Pct_Pratique'] - row['Pct_Theorie']) < -5 else "Équilibrés"), axis=1)
    else:
        df['Profil_Match'] = "Inconnu"

    if col_coords:
        df[col_coords] = df[col_coords].replace("1;1", "46.58261;0.34348")
    
    df['acad_key'] = df[col_academie].apply(get_acad_key)

    # --- FONCTION HELPER GLOBALE ---
    def get_mask_for_status(status_name, dataframe):
        if status_name == NAME_FI:
            m_l = dataframe[col_statut].isin(LISTE_FI)
            m_a = dataframe[col_statut_autre].astype(str).str.contains("FI", case=False, na=False) if col_statut_autre else False
            return m_l | m_a
        elif status_name == NAME_FC:
            m_l = dataframe[col_statut].isin(LISTE_FC)
            m_a = dataframe[col_statut_autre].astype(str).str.contains("FC", case=False, na=False) if col_statut_autre else False
            return m_l | m_a
        else:
            return dataframe[col_statut] == status_name

    # ==========================================
    # 4. INTERFACE
    # ==========================================
    
    # --- LOGO EN HAUT A GAUCHE (SIDEBAR) ---
    logo_url = "https://github.com/amine-amar/Photo_inspe/blob/main/UP%20+%20INSPE%20HD.png?raw=true"
    try:
        st.sidebar.image(logo_url, use_container_width=True)
    except:
        pass

    # --- NAVIGATION ---
    st.sidebar.title("📌 Menu Principal")
    
    page = st.sidebar.radio("Aller vers :", [
        "🏠 Accueil & Contexte",
        "📊 Analyse Descriptive", 
        "🌍 Carte Géographique",
        "🏆 Top/Flop 5Q",
        "📖 Plan Français",
        "💻 Outils Numériques",
        "⏳ Ancienneté",
        "⚡ Théorie vs Pratique"
    ])

    # Footer Sidebar
    st.sidebar.markdown("---")
    st.sidebar.caption("""
    **Note :** Les réponses collectées sont strictement anonymes. Ce questionnaire est un outil de formation et de recherche visant à nourrir la réflexion didactique.
    
    🔗 [En savoir plus sur le projet SciCoNum](https://inspe.univ-poitiers.fr/projet-sciconum/)
    """)
    
    # --- PRÉ-CALCUL ---
    mask_fi_list = df[col_statut].isin(LISTE_FI)
    mask_fc_list = df[col_statut].isin(LISTE_FC)
    mask_fi_autre = pd.Series(False, index=df.index)
    mask_fc_autre = pd.Series(False, index=df.index)

    if col_statut_autre:
        mask_fi_autre = df[col_statut_autre].astype(str).str.contains("FI", case=False, na=False)
        mask_fc_autre = df[col_statut_autre].astype(str).str.contains("FC", case=False, na=False)

    nb_fi = (mask_fi_list | mask_fi_autre).sum()
    nb_fc = (mask_fc_list | mask_fc_autre).sum()
    nb_total = nb_fi + nb_fc
    
    # --- LOGIQUE D'AFFICHAGE DES PAGES ---

    # >>> PAGE ACCUEIL (PAGE SÉPARÉE - MISE EN PAGE SOBRE)
    if page == "🏠 Accueil & Contexte":
        
        # 2. TITRE & SOUS-TITRE EN DESSOUS (Avec Emoji)
        st.markdown("<h1 style='text-align: center;'>📊 Apprentissage et enseignement de la production écrite à l'école</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #555;'>Projet SciCoNum – INSPÉ de l'académie de Poitiers</h3>", unsafe_allow_html=True)
        st.divider()
        
        # --- BLOC CONTEXTE ---
        st.markdown("### 📌 Contexte du Projet")
        st.info("""
        Le présent tableau de bord propose une analyse approfondie des données recueillies via le questionnaire intitulé *"Testez vos connaissances sur l'apprentissage et l'enseignement de la production écrite"*. Cet outil d'évaluation a été conçu et déployé dans le cadre du projet **SciCoNum** (Sciences Cognitives pour le Numérique), afin de mesurer l'appropriation des concepts cognitifs liés à l'écriture.
        """)
        
        st.markdown("<br>", unsafe_allow_html=True) 

        # --- BLOC OBJECTIFS & RESPONSABLES (2 colonnes) ---
        col_obj, col_resp = st.columns(2, gap="large")
        
        with col_obj:
            st.markdown("#### 🎯 Objectifs de cet outil")
            # Liste propre sans émojis
            st.markdown("""
            * Diagnostiquer les forces et les axes d'amélioration spécifiques à chacune des 4 thématiques du questionnaire.
            * Comparer les trajectoires entre la Formation Initiale et la Formation Continue.
            * Explorer les interdépendances entre les 4 parties du questionnaire (via l'analyse des corrélations ou factorielle) pour comprendre la structure des connaissances.
            * Cartographier la répartition territoriale des répondants.
            """)
            
        with col_resp:
            st.markdown("#### 👥 Responsables scientifiques")
            # Liste propre sans émojis
            st.markdown("""
            * **Denis ALAMARGOT**, professeur des universités en psychologie du développement.
            * **Victor MILLOGO**, maître de conférences en psychologie du développement.
            """)
            
            st.markdown("#### 👤 Ingénieur d’études")
            st.markdown("""
            * **Amine AMMAR**, IGE production, traitement, analyse de données et enquêtes.
            """)
            
        st.markdown("---")
        st.success("👈 **Utilisez le menu latéral pour naviguer dans les différentes analyses.**")

    # >>> AUTRES PAGES (AVEC FILTRES)
    else:
        # --- CENTRE DE PILOTAGE (FILTRES) - Présent sur toutes les pages sauf l'accueil ---
        st.title("📊 Tableau de Bord : Production Écrite")
        
        with st.expander("🎯 CENTRE DE PILOTAGE (Filtres)", expanded=True):
            # Indicateurs
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.metric("Ensemble des réponses", nb_total, help="Total FI + FC")
            with kpi2:
                st.metric("Formation Initiale (FI)", nb_fi, help="M1, M2, Stagiaires")
            with kpi3:
                st.metric("Formation Continue (FC)", nb_fc, help="Titulaires, Contractuels")
            
            st.divider()
            
            # Explication des filtres
            st.info("""
            **Guide d'utilisation des filtres :**
            * 🟦 **(FI) & (FC) Fusions :** Utilisez ces options pour comparer les deux grands blocs (Formation initiale vs Formation continue).
            * 🟩 **Statuts Détaillés :** Cochez ces options pour affiner l'analyse sur un public précis (ex: M2 uniquement, Contractuels, etc.).
            """)

            # Sélecteur
            st.markdown("#### 🔍 Sélectionner les populations à analyser :")
            standard_options = sorted([str(x) for x in df[col_statut].unique() if pd.notna(x)])
            display_standards = [f"🟩 {x}" for x in standard_options]
            
            all_options = [NAME_FI, NAME_FC] + display_standards
            
            statuts_sel = st.multiselect(
                "Choisissez un ou plusieurs statuts :", 
                options=all_options, 
                default=all_options,
                label_visibility="collapsed"
            )
        
        # --- MOTEUR DE FILTRAGE ---
        final_mask = pd.Series(False, index=df.index)
        
        if NAME_FI in statuts_sel:
            final_mask = final_mask | mask_fi_list | mask_fi_autre
        if NAME_FC in statuts_sel:
            final_mask = final_mask | mask_fc_list | mask_fc_autre

        selected_standards_display = [s for s in statuts_sel if s not in [NAME_FI, NAME_FC]]
        selected_standards_raw = [s.replace("🟩 ", "") for s in selected_standards_display]

        if selected_standards_raw:
            final_mask = final_mask | df[col_statut].isin(selected_standards_raw)

        df_filtered = df[final_mask]
        
        if len(df_filtered) == 0:
            st.warning("⚠️ Aucune donnée ne correspond aux filtres sélectionnés.")
        else:
            
            # >>> PAGE 2 : DESCRIPTIF
            if page == "📊 Analyse Descriptive":
                st.markdown("### 📊 Analyse Descriptive")
                # TEXTE MIS À JOUR AVEC BOITE VERTE
                st.success("""
                Cette section vise à analyser de manière approfondie les trajectoires de formation, les quotités de travail et les contextes d’exercice (zone géographique, classes multi-niveaux), afin de caractériser les acteurs de terrain. Elle s’appuie sur un score global, une analyse par parties et une analyse comparative pour mettre en évidence les principales disparités observées.
                """)
                st.markdown("<br>", unsafe_allow_html=True)
                st.divider()

                col_quotite = next((c for c in df.columns if "quotité" in c.lower()), None)
                
                # DÉTECTION ROBUSTE COLONNE MULTI-NIVEAUX
                col_multi = None
                keywords_multi = ["multi-niveaux", "multiniveaux", "plusieurs niveaux", "cours double", "double niveau"]
                for c in df.columns:
                    if any(kw in c.lower() for kw in keywords_multi):
                        col_multi = c
                        break
                
                # MISE À JOUR : Ajout de l'onglet Écart Type après Vue d'ensemble
                tab1, tab_std, tab2, tab_quotite, tab_zone, tab_multi, tab3, tab4, tab5 = st.tabs([
                    "Vue d'ensemble", 
                    "Écart Type & Coefficient de Variation", 
                    "Démographie", 
                    "Quotité de travail", 
                    "Zone géographique", 
                    "Classes Multi-niveaux",
                    "Score Global", 
                    "Analyse par Parties", 
                    "Analyse Comparative"
                ])
                
                with tab1:
                    # 1. CHIFFRES CLÉS
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Nombre de répondants", len(df_filtered))
                    if total_cols:
                        c2.metric("Score Moyen", f"{df_filtered[total_cols[0]].mean():.2f}")
                        c3.metric("Score Max", f"{df_filtered[total_cols[0]].max():.0f}")
                        c4.metric("Score Min", f"{df_filtered[total_cols[0]].min():.0f}")
                    
                    st.divider()
                    
                    # 2. RÉPARTITION PAR STATUT (AFFICHAGE JOLI)
                    st.markdown("### 👥 Répartition par Statut")
                    status_counts = df_filtered[col_statut].value_counts()
                    
                    # Création de colonnes dynamiques pour afficher les statuts proprement
                    if len(status_counts) > 0:
                        cols = st.columns(len(status_counts)) if len(status_counts) <= 4 else st.columns(4)
                        for i, (statut_name, count) in enumerate(status_counts.items()):
                            col_idx = i % 4
                            with cols[col_idx]:
                                st.metric(label=statut_name, value=count)
                                st.markdown("---")
                    
                    st.markdown("<br>", unsafe_allow_html=True)

                    # 3. INFORMATIONS PERTINENTES (INSIGHTS)
                    st.markdown("### 💡 Informations Clés de la Sélection")
                    col_i1, col_i2 = st.columns(2)
                    
                    # Académies Dominantes (Top 3)
                    if not df_filtered.empty and col_academie:
                        top_acads = df_filtered[col_academie].value_counts().head(3)
                        acad_list_text = "📍 **Top 3 Académies :**"
                        for i, (name, count) in enumerate(top_acads.items(), 1):
                            acad_list_text += f"\n{i}. {name} ({count})"
                    else:
                        acad_list_text = "📍 **Académies :** N/A"
                    
                    # Partie la mieux réussie
                    best_part = "N/A"
                    best_score = 0
                    if total_cols:
                        scores_parts = {k: (df_filtered[k].mean()/v['max_points']*100) for k, v in PARTIES_INFO.items() if k in df_filtered.columns}
                        if scores_parts:
                            best_part_key = max(scores_parts, key=scores_parts.get)
                            best_part = PARTIES_INFO[best_part_key]['short']
                            best_score = scores_parts[best_part_key]

                    with col_i1:
                        st.info(acad_list_text)
                    with col_i2:
                        st.success(f"🏆 **Point Fort du groupe :** {best_part} ({best_score:.1f}% de réussite)")

                # --- CONTENU : ONGLET ÉCART TYPE & CV ---
                with tab_std:
                    st.header("📏 Analyse de la Dispersion (Écart Type)")
                    
                    # 1. FORMULE MATHÉMATIQUE
                    st.latex(r"\sigma = \sqrt{\frac{\sum(x - \bar{x})^2}{N}}")
                    
                    # 2. INFO BULLE BLEUE (DÉFINITION)
                    st.info("""
                    🟢 **Faible écart type :** Les scores sont proches de la moyenne (groupe homogène).
                    
                    🔴 **Fort écart type :** Les scores sont très dispersés (groupe hétérogène).
                    """)
                    
                    if total_cols:
                        col_score = total_cols[0]
                        mean_val = df_filtered[col_score].mean()
                        std_val = df_filtered[col_score].std()
                        
                        # 3. Indicateurs clés (Interprétation classique)
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Moyenne du groupe", f"{mean_val:.2f} / 100")
                        c2.metric("Écart Type (Dispersion)", f"{std_val:.2f}")
                        
                        interpretation = "Homogène" if std_val < 15 else ("Moyennement dispersé" if std_val < 20 else "Très Hétérogène")
                        c3.metric("Interprétation", interpretation)

                        st.divider()

                        # 4. Visualisation de la distribution (Boîte à moustaches avec Ecart Type)
                        st.subheader("1. Visualisation de la dispersion des scores")
                        
                        clean_data = df_filtered[col_score].dropna()
                        
                        if len(clean_data) > 1:
                            fig_box = go.Figure()
                            
                            fig_box.add_trace(go.Box(
                                x=clean_data,
                                name="Global",
                                boxmean='sd', # C'est l'option magique : affiche moyenne et écart type
                                orientation='h',
                                marker_color='#9b59b6',
                                boxpoints='all', # Affiche tous les points pour voir la dispersion réelle
                                jitter=0.3,
                                pointpos=-1.8
                            ))

                            fig_box.update_layout(
                                title="Distribution des scores (Boîte à moustaches avec Moyenne ± Ecart Type)",
                                xaxis_title="Score Total (/100)",
                                yaxis_title="",
                                showlegend=False,
                                xaxis_range=[0, 100]
                            )
                            
                            st.plotly_chart(fig_box, use_container_width=True)
                            
                            # --- BLOC DE DÉTAILS STATISTIQUES ---
                            st.markdown("### 📊 Détails statistiques de la distribution")
                            
                            # Calculs
                            q1 = clean_data.quantile(0.25)
                            median = clean_data.median()
                            q3 = clean_data.quantile(0.75)
                            iqr = q3 - q1
                            min_score = clean_data.min()
                            max_score = clean_data.max()
                            
                            # Calcul Outliers (Règle 1.5 IQR)
                            lower_fence = q1 - (1.5 * iqr)
                            upper_fence = q3 + (1.5 * iqr)
                            
                            # On récupère les lignes entières pour les outliers (pour savoir QUI c'est)
                            mask_outliers = (df_filtered[col_score] < lower_fence) | (df_filtered[col_score] > upper_fence)
                            df_outliers = df_filtered[mask_outliers]
                            
                            nb_outliers = len(df_outliers)
                            pct_outliers = (nb_outliers / len(clean_data)) * 100

                            # Affichage en colonnes
                            col_s1, col_s2, col_s3 = st.columns(3)
                            
                            with col_s1:
                                st.markdown("**Les Quartiles (La Boîte)**")
                                st.write(f"🔹 **25% (Q1) :** {q1:.1f}")
                                st.write(f"🔹 **Médiane (50%) :** {median:.1f}")
                                st.write(f"🔹 **75% (Q3) :** {q3:.1f}")
                            
                            with col_s2:
                                st.markdown("**Les Extrêmes**")
                                st.write(f"🔻 **Minimum :** {min_score:.0f}")
                                st.write(f"🔺 **Maximum :** {max_score:.0f}")
                                st.write(f"📏 **Écart Interquartile :** {iqr:.1f}")

                            with col_s3:
                                st.markdown("**Valeurs Atypiques (Outliers)**")
                                st.metric("Nombre de cas", f"{nb_outliers}")
                                st.caption(f"Soit {pct_outliers:.1f}% des répondants sont considérés comme hors-norme.")
                                
                                # --- LE PETIT MENU DÉROULANT ---
                                with st.expander("👁️ Voir le détail par Statut"):
                                    if not df_outliers.empty:
                                        # Compter par statut
                                        counts_outliers = df_outliers[col_statut].value_counts().reset_index()
                                        counts_outliers.columns = ['Statut', 'Nombre']
                                        st.dataframe(counts_outliers, hide_index=True, use_container_width=True)
                                    else:
                                        st.write("Aucun outlier détecté.")

                        else:
                            st.info("Pas assez de données pour tracer la distribution.")

                        st.divider()

                        # 5. Comparatif : Qui est le plus hétérogène ?
                        st.subheader("2. Comparaison de l'hétérogénéité par Statut")
                        # Calcul de l'écart type par statut
                        df_std_by_status = df_filtered.groupby(col_statut)[col_score].std().reset_index()
                        df_std_by_status.columns = [col_statut, 'Ecart_Type']
                        
                        # --- LOGIQUE DE COULEURS ET LABELS ---
                        colors_list = []
                        for val in df_std_by_status['Ecart_Type']:
                            if val < 15:
                                colors_list.append("#2ecc71") # Vert
                            elif val < 20:
                                colors_list.append("#f1c40f") # Jaune
                            else:
                                colors_list.append("#e74c3c") # Rouge
                        
                        df_std_by_status['Color'] = colors_list
                        
                        df_std_by_status = df_std_by_status.sort_values('Ecart_Type', ascending=True)

                        fig_std_bar = px.bar(
                            df_std_by_status,
                            x='Ecart_Type',
                            y=col_statut,
                            orientation='h',
                            title="Classement : Du groupe le plus homogène (haut) au plus hétérogène (bas)",
                            text_auto='.2f',
                        )
                        # On applique les couleurs ligne par ligne
                        fig_std_bar.update_traces(marker_color=df_std_by_status['Color'])
                        
                        # Ajout des lignes de seuil
                        fig_std_bar.add_vline(x=15, line_width=1, line_dash="dash", line_color="green", annotation_text="Seuil 15")
                        fig_std_bar.add_vline(x=20, line_width=1, line_dash="dash", line_color="red", annotation_text="Seuil 20")
                        
                        fig_std_bar.update_layout(xaxis_title="Écart Type (Plus c'est grand, plus c'est hétérogène)")
                        st.plotly_chart(fig_std_bar, use_container_width=True)
                        
                        # Légende explicite sous le graphique (Texte mis à jour selon demande)
                        st.caption("🟢 Vert : Écart type < 15 (Homogène) | 🟡 Jaune : Entre 15 et 20 (Hétérogène) | 🔴 Rouge : Écart type > 20 (Très Hétérogène)")

                    else:
                        st.warning("Impossible de calculer l'écart type (colonne score total introuvable).")
                
                with tab2:
                    c1, c2 = st.columns(2)
                    with c1: st.plotly_chart(px.pie(df_filtered, names=col_statut, title="Statut", hole=0.4), use_container_width=True)
                    with c2: st.plotly_chart(px.bar(df_filtered[col_academie].value_counts(), title="Académies"), use_container_width=True)
                
                # --- ONGLET QUOTITÉ (MODIFIÉ) ---
                with tab_quotite:
                    st.header("⏳ Quotité de Travail")
                    if col_quotite:
                        df_q = df_filtered.copy()
                        df_q[col_quotite] = df_q[col_quotite].astype(str)
                        mask_nc = df_q[col_quotite].str.contains("non enseignant", case=False, na=False) | df_q[col_quotite].isin(['nan', 'None', '', 'NaN'])
                        df_q.loc[mask_nc, col_quotite] = "Non concerné"
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            # MODIFICATION COULEURS ICI
                            color_map_quotite = {
                                "Non concerné": "#e74c3c",  # Rouge
                                "Temps partiel": "#56CCF2", # Bleu ciel
                                "Temps complet": "#000080"  # Bleu marine
                            }
                            
                            fig_q = px.pie(
                                df_q, 
                                names=col_quotite, 
                                title="Répartition Globale", 
                                hole=0.4,
                                color=col_quotite,
                                color_discrete_map=color_map_quotite
                            )
                            st.plotly_chart(fig_q, use_container_width=True)
                        with c2:
                            # Ajout de la map couleur ici aussi
                            fig_q_bar = px.histogram(
                                df_q, 
                                y=col_statut, 
                                color=col_quotite, 
                                barmode='stack', 
                                title="Détail par Statut", 
                                orientation='h',
                                color_discrete_map=color_map_quotite
                            )
                            st.plotly_chart(fig_q_bar, use_container_width=True)
                    else:
                        st.warning("Colonne 'Quotité' introuvable.")

                # --- ONGLET ZONE GÉOGRAPHIQUE ---
                with tab_zone:
                    st.header("📍 Zone Géographique d'exercice")
                    
                    cols_zones = [c for c in df.columns if "zone géographique" in str(c).lower() and "[" in str(c)]
                    
                    if cols_zones:
                        zone_data = []
                        for col in cols_zones:
                            match = re.search(r'\[(.*?)\]', col)
                            if match:
                                zone_name = match.group(1).replace(',', '').strip()
                                count = df_filtered[col].apply(lambda x: 1 if pd.notna(x) and str(x).strip() != "" and str(x).lower() not in ["non", "0", "false"] else 0).sum()
                                if count > 0:
                                    zone_data.append({"Zone": zone_name, "Nombre": count})
                        
                        if zone_data:
                            df_zones = pd.DataFrame(zone_data).sort_values("Nombre", ascending=True)
                            
                            # --- MODIFICATION COULEURS ICI ---
                            fig_z = px.bar(
                                df_zones, 
                                x='Nombre', 
                                y='Zone', 
                                text='Nombre',
                                title="Fréquence des types de zones",
                                orientation='h',
                                color='Zone', 
                                color_discrete_map={
                                    "Zone rurale": "#2ecc71",  # Vert
                                    "Zone urbaine": "#3498db"  # Bleu
                                }
                            )
                            fig_z.update_traces(textposition='outside')
                            st.plotly_chart(fig_z, use_container_width=True)
                        else:
                            st.warning("Aucune donnée cochée trouvée.")
                    else:
                        st.warning("Colonnes 'Zone géographique' (format [Option]) introuvables.")

                # --- ONGLET CLASSES MULTI-NIVEAUX (MODIFIÉ) ---
                with tab_multi:
                    st.header("🏫 Classes Multi-niveaux")
                    if col_multi:
                        df_m = df_filtered.copy()
                        df_m[col_multi] = df_m[col_multi].fillna("Non concerné")
                        
                        # DÉFINITION DE L'ORDRE ET DES COULEURS
                        multi_order = ["Oui, double niveaux,", "Oui, triple niveaux,", "Non", "Non concerné"]
                        multi_colors = {
                            "Oui, double niveaux,": "#2980b9", # Bleu Roi
                            "Oui, triple niveaux,": "#56CCF2", # Bleu Ciel
                            "Non": "#e74c3c",                  # Rouge
                            "Non concerné": "#95a5a6"          # Gris
                        }
                        
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            fig_m_pie = px.pie(
                                df_m, 
                                names=col_multi, 
                                title="Répartition Globale", 
                                hole=0.4, 
                                color=col_multi, # Important pour mapper la couleur
                                color_discrete_map=multi_colors,
                                category_orders={col_multi: multi_order}
                            )
                            st.plotly_chart(fig_m_pie, use_container_width=True)
                        with c2:
                            df_m_gb = df_m.groupby([col_statut, col_multi]).size().reset_index(name='Nombre')
                            
                            fig_m_bar = px.bar(
                                df_m_gb, 
                                y=col_statut, 
                                x='Nombre',
                                color=col_multi, 
                                title="Répartition par Statut (Empilé)", 
                                orientation='h',
                                text='Nombre',
                                barmode='stack',
                                color_discrete_map=multi_colors,
                                category_orders={col_multi: multi_order}
                            )
                            fig_m_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig_m_bar, use_container_width=True)
                    else:
                        st.warning("Colonne 'Classes Multi-niveaux' introuvable. Vérifiez les noms de colonnes dans le fichier Excel.")

                with tab3:
                    st.header("📈 Analyse du Score Global")
                    if total_cols:
                        c1, c2 = st.columns(2)
                        
                        with c1: 
                            fig_hist = px.histogram(
                                df_filtered, 
                                x=total_cols[0], 
                                nbins=25, 
                                title="Distribution des Scores (0-100)",
                                color_discrete_sequence=['#3498db'], 
                                marginal="box"
                            )
                            fig_hist.update_layout(
                                xaxis_title="Score Total (/100)",
                                yaxis_title="Nombre de répondants",
                                bargap=0.1
                            )
                            st.plotly_chart(fig_hist, use_container_width=True)
                        
                        with c2: 
                            df_stat_mean = df_filtered.groupby(col_statut)[total_cols[0]].agg(['mean', 'count']).reset_index()
                            df_stat_mean.columns = [col_statut, 'Score_Moyen', 'Effectif']
                            
                            df_stat_mean['Label'] = df_stat_mean.apply(lambda row: f"{row['Score_Moyen']:.1f} (N={int(row['Effectif'])})", axis=1)
                            df_stat_mean = df_stat_mean.sort_values(by='Score_Moyen', ascending=True)
                            
                            fig_bar_mean = px.bar(
                                df_stat_mean, 
                                x='Score_Moyen', 
                                y=col_statut, 
                                title="Score Moyen par Statut (avec effectif N)",
                                text='Label',
                                orientation='h',
                                color='Score_Moyen',
                                color_continuous_scale='Blues'
                            )
                            fig_bar_mean.update_layout(
                                xaxis_title="Score Moyen",
                                yaxis_title="",
                                xaxis_range=[0, 100]
                            )
                            st.plotly_chart(fig_bar_mean, use_container_width=True)

                with tab4:
                    st.header("Détail des scores par thématique")
                    for col_partie, info in PARTIES_INFO.items():
                        if col_partie in df_filtered.columns:
                            with st.container():
                                st.subheader(f"📘 {info['titre']}")
                                st.caption(f"Barème : sur **{info['max_points']} points**")
                                
                                mean_val = df_filtered[col_partie].mean()
                                max_val = df_filtered[col_partie].max()
                                min_val = df_filtered[col_partie].min()
                                pct_mean = (mean_val / info['max_points']) * 100 if info['max_points'] > 0 else 0
                                
                                m1, m2, m3, m4 = st.columns(4)
                                m1.metric("Moyenne", f"{mean_val:.2f} / {info['max_points']}")
                                m2.metric("Moyenne (%)", f"{pct_mean:.1f} %")
                                m3.metric("Maximum", f"{max_val:.0f}")
                                m4.metric("Minimum", f"{min_val:.0f}")
                                
                                g1, g2 = st.columns(2)
                                
                                score_counts = df_filtered[col_partie].value_counts().reset_index()
                                score_counts.columns = ['Score', 'Count']
                                
                                fig_dist = px.bar(
                                    score_counts, x='Score', y='Count', text='Count',
                                    title=f"Distribution : {info['titre']}",
                                    labels={'Score': f"Score obtenu sur {info['max_points']}", 'Count': 'Nombre de répondants'},
                                    color_discrete_sequence=['#3498db']
                                )
                                fig_dist.update_traces(textposition='outside')
                                fig_dist.update_layout(xaxis=dict(dtick=1, range=[0, info['max_points']+1]), yaxis_title="Nombre de répondants")
                                g1.plotly_chart(fig_dist, use_container_width=True, key=f"dist_{col_partie}")
                                
                                df_p_mean = df_filtered.groupby(col_statut)[col_partie].mean().reset_index()
                                df_p_mean['Pourcentage'] = (df_p_mean[col_partie] / info['max_points']) * 100
                                df_p_mean = df_p_mean.sort_values(by='Pourcentage', ascending=False)
                                fig_bar = px.bar(df_p_mean, x=col_statut, y='Pourcentage', title="Moyenne par Statut (%)", text_auto='.1f', color='Pourcentage', color_continuous_scale='Viridis', range_y=[0, 100])
                                g2.plotly_chart(fig_bar, use_container_width=True, key=f"bar_{col_partie}")
                                st.divider()

                with tab5:
                    st.header("⚖️ Analyse Comparative Approfondie")
                    defaults = [NAME_FI, NAME_FC] if (NAME_FI in all_options and NAME_FC in all_options) else all_options[:2]
                    comp_statuts = st.multiselect("Choix des groupes à comparer :", options=all_options, default=defaults)
                    
                    if comp_statuts:
                        radar_data = []
                        for statut in comp_statuts:
                            # Gestion propre pour les groupes comparatifs : retirer le vert s'il est présent
                            clean_statut = statut.replace("🟩 ", "")
                            mask = get_mask_for_status(clean_statut, df)
                            sub_df = df[mask]
                            if len(sub_df) > 0:
                                for col_part, info in PARTIES_INFO.items():
                                    if col_part in sub_df.columns:
                                        avg_score = sub_df[col_part].mean()
                                        pct_score = (avg_score / info['max_points']) * 100
                                        radar_data.append({"Statut": statut, "Partie": info['short'], "Score Moyen": avg_score, "Pourcentage": pct_score, "Max": info['max_points']})
                        
                        if radar_data:
                            df_radar = pd.DataFrame(radar_data)
                            col_g1, col_g2 = st.columns([1, 1])
                            with col_g1:
                                st.subheader("🕸️ Profil de compétences (Radar)")
                                fig_radar = px.line_polar(df_radar, r='Pourcentage', theta='Partie', color='Statut', line_close=True, title="Comparaison (en %)", markers=True)
                                fig_radar.update_traces(fill='toself')
                                st.plotly_chart(fig_radar, use_container_width=True)
                            with col_g2:
                                st.subheader("📊 Comparaison par Axe")
                                fig_bar_comp = px.bar(df_radar, x='Partie', y='Pourcentage', color='Statut', barmode='group', text_auto='.1f', title="Détail des scores moyens (normalisés en %)", labels={'Pourcentage': 'Score Moyen (%)'})
                                fig_bar_comp.update_layout(yaxis_range=[0, 100])
                                st.plotly_chart(fig_bar_comp, use_container_width=True)
                            
                            st.subheader("📋 Tableau de données détaillées")
                            df_pivot = df_radar.pivot(index='Partie', columns='Statut', values='Score Moyen')
                            df_pivot["Sur (Points)"] = df_pivot.index.map({v['short']: v['max_points'] for k, v in PARTIES_INFO.items()})
                            st.dataframe(df_pivot.style.format("{:.2f}"), use_container_width=True)
                        else:
                            st.warning("Pas assez de données pour les statuts sélectionnés.")
                    else:
                        st.info("Veuillez sélectionner au moins un statut.")

            # >>> PAGE 3 : TOP / FLOP 5Q
            elif page == "🏆 Top/Flop 5Q":
                st.markdown("### 🏆 Hit-Parade des Questions")
                # TEXTE MIS À JOUR AVEC BOITE VERTE
                st.success("""
                Sur les 54 questions de contenu du QCM, quelles sont celles qui font consensus et celles qui posent problème ? Cette analyse identifie les notions de sciences cognitives les mieux maîtrisées et les idées reçues persistantes.
                """)
                st.markdown("<br>", unsafe_allow_html=True)
                st.divider()
                
                cols = df.columns.tolist()
                
                def get_top_flop_stats(dataframe, label="Global"):
                    items_stats = []
                    for i, col in enumerate(cols):
                        if str(col).strip().startswith('{if') or "if(" in str(col):
                            match = re.search(r',\s*(\d+(\.\d+)?)\s*,\s*0', str(col))
                            if match:
                                max_points = float(match.group(1))
                                if max_points > 0:
                                    question_text = str(cols[i-1])
                                    q_num_match = re.search(r'^(\d+(\.\d+)*)', question_text)
                                    q_num = q_num_match.group(1) if q_num_match else "?"
                                    question_clean = re.sub(r'^\d+(\.\d+)*\s*', '', question_text).split('?')[0] + "?"
                                    if len(question_clean) > 70: question_clean = question_clean[:70] + "..."
                                    full_label = f"[{q_num}] {question_clean}"

                                    scores = pd.to_numeric(dataframe[col], errors='coerce').fillna(0)
                                    avg_score = scores.mean()
                                    success_rate = (avg_score / max_points) * 100
                                    
                                    items_stats.append({
                                        'Question': full_label,
                                        'Réussite (%)': success_rate,
                                        'Score Moyen': avg_score,
                                        'Max Points': max_points,
                                        'Groupe': label
                                    })
                    return items_stats

                st.subheader("1. Analyse Globale (Selon filtre latéral)")
                global_stats = get_top_flop_stats(df_filtered, "Sélection Actuelle")
                
                if global_stats:
                    df_items = pd.DataFrame(global_stats)
                    top_5 = df_items.sort_values('Réussite (%)', ascending=False).head(5)
                    bottom_5 = df_items.sort_values('Réussite (%)', ascending=True).head(5)
                    top_5['Type'] = 'Top 5 (Acquis)'
                    bottom_5['Type'] = 'Flop 5 (À renforcer)'
                    df_plot = pd.concat([top_5, bottom_5]).sort_values('Réussite (%)', ascending=False)
                    
                    fig = px.bar(
                        df_plot, x='Réussite (%)', y='Question', color='Type', text_auto='.1f', orientation='h',
                        color_discrete_map={'Top 5 (Acquis)': '#2ecc71', 'Flop 5 (À renforcer)': '#e74c3c'},
                        title="Les concepts les mieux maîtrisés vs les plus difficiles"
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Taux de Réussite Moyen (%)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Impossible de détecter les questions.")

                st.divider()

                st.subheader("2. Comparaison Top/Flop entre Statuts")
                c1, c2 = st.columns(2)
                with c1:
                    statut_A = st.selectbox("Groupe A :", options=all_options, index=0)
                with c2:
                    default_idx_B = 1 if len(all_options) > 1 else 0
                    statut_B = st.selectbox("Groupe B :", options=all_options, index=default_idx_B)

                if statut_A and statut_B:
                    # Nettoyage des préfixes verts pour le filtrage
                    clean_A = statut_A.replace("🟩 ", "")
                    clean_B = statut_B.replace("🟩 ", "")
                    
                    mask_A = get_mask_for_status(clean_A, df)
                    stats_A = get_top_flop_stats(df[mask_A], statut_A)
                    mask_B = get_mask_for_status(clean_B, df)
                    stats_B = get_top_flop_stats(df[mask_B], statut_B)

                    if stats_A and stats_B:
                        df_A = pd.DataFrame(stats_A)
                        df_B = pd.DataFrame(stats_B)

                        col_left, col_right = st.columns(2)
                        with col_left:
                            st.markdown(f"**Top 5 & Flop 5 : {statut_A}**")
                            t5_A = df_A.sort_values('Réussite (%)', ascending=False).head(5)
                            b5_A = df_A.sort_values('Réussite (%)', ascending=True).head(5)
                            t5_A['Type'] = 'Top'; b5_A['Type'] = 'Flop'
                            plot_A = pd.concat([t5_A, b5_A]).sort_values('Réussite (%)', ascending=True)
                            fig_A = px.bar(plot_A, x='Réussite (%)', y='Question', color='Type', text_auto='.0f', orientation='h', color_discrete_map={'Top': '#27ae60', 'Flop': '#c0392b'}, height=500)
                            fig_A.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
                            st.plotly_chart(fig_A, use_container_width=True, key="fig_comp_A")

                        with col_right:
                            st.markdown(f"**Top 5 & Flop 5 : {statut_B}**")
                            t5_B = df_B.sort_values('Réussite (%)', ascending=False).head(5)
                            b5_B = df_B.sort_values('Réussite (%)', ascending=True).head(5)
                            t5_B['Type'] = 'Top'; b5_B['Type'] = 'Flop'
                            plot_B = pd.concat([t5_B, b5_B]).sort_values('Réussite (%)', ascending=True)
                            fig_B = px.bar(plot_B, x='Réussite (%)', y='Question', color='Type', text_auto='.0f', orientation='h', color_discrete_map={'Top': '#27ae60', 'Flop': '#c0392b'}, height=500)
                            fig_B.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
                            st.plotly_chart(fig_B, use_container_width=True, key="fig_comp_B")

            # >>> PAGE 4 : CARTE
            elif page == "🌍 Carte Géographique":
                st.header("🌍 Carte des Répondants")
                
                # --- LÉGENDE MISE À JOUR (NOUVEAU TEXTE) ---
                st.success("""
                **Légende de la carte :**
                * 🎓 **Icônes Bleues :** Sièges des Académies. Cliquez pour voir les statistiques détaillées par académie.
                * 🔴 **Points Rouges :** Lieux d’exercice mentionnés par les répondants.
                * 🔢 **Cercles Colorés (Clusters) :** Regroupements de plusieurs répondants. Cliquez dessus pour zoomer et voir le détail.
                """)
                st.markdown("<br>", unsafe_allow_html=True)
                
                with st.spinner("Chargement de la carte..."):
                    # 1. Création de la carte avec OpenStreetMap PAR DÉFAUT (Vitesse optimisée avec prefer_canvas)
                    m = folium.Map(location=[46.5, 2.0], zoom_start=6, tiles="OpenStreetMap", prefer_canvas=True)
                    
                    # 2. Ajout du masque monde (Pays en noir pour focus France)
                    world_geo = fetch_geojson("https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json")
                    if world_geo:
                        folium.GeoJson(
                            world_geo,
                            name="Masque Monde",
                            style_function=lambda x: {
                                'fillColor': '#000000',
                                'color': '#000000',
                                'weight': 0,
                                'fillOpacity': 0.75
                            } if x['properties']['name'] not in ['France', 'Andorra'] else {
                                'fillOpacity': 0,
                                'weight': 0
                            }
                        ).add_to(m)

                    # 3. Ajout des régions de France
                    france_geo = fetch_geojson("https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions.geojson")
                    if france_geo:
                        folium.GeoJson(
                            france_geo, 
                            name="Régions",
                            style_function=lambda x: {'fillColor': 'transparent', 'color': '#3388ff', 'weight': 1, 'opacity': 0.6}
                        ).add_to(m)
                        
                        # Labels légers pour les régions
                        for f in france_geo['features']:
                            c = get_centroid(f)
                            if c: folium.map.Marker(
                                c, 
                                icon=DivIcon(
                                    icon_size=(150,36), 
                                    icon_anchor=(75,18), 
                                    html=f"<div style='font-family:Arial;font-size:9px;font-weight:bold;color:#555;text-align:center;background:rgba(255,255,255,0.5);border-radius:4px;'>{f['properties']['nom']}</div>"
                                )
                            ).add_to(m)
                    
                    # 4. Cluster des répondants
                    cluster = MarkerCluster(name="Répondants").add_to(m)
                    
                    if col_coords:
                        points_to_add = []
                        for _, row in df_filtered.iterrows():
                            try:
                                if ';' in str(row[col_coords]):
                                    lat, lon = map(float, str(row[col_coords]).replace('(', '').replace(')', '').split(';'))
                                    popup_text = f"<b>{row[col_statut]}</b><br>{row.get(col_academie, '')}"
                                    folium.CircleMarker(
                                        [lat, lon], 
                                        radius=5, 
                                        color='white', 
                                        weight=1, 
                                        fill=True, 
                                        fill_color='#e74c3c', 
                                        fill_opacity=0.9, 
                                        popup=popup_text
                                    ).add_to(cluster)
                            except: pass
                    
                    # 5. Marqueurs Rectorats (Popup intelligent)
                    acad_counts = df_filtered['acad_key'].value_counts()
                    for key, info in INFO_RECTORATS.items():
                        if key in acad_counts:
                            # 1. Calcul du détail par statut pour cette académie
                            sub_df_acad = df_filtered[df_filtered['acad_key'] == key]
                            stats_acad = sub_df_acad[col_statut].value_counts()
                            
                            # 2. Construction du HTML pour le popup
                            popup_html = f"<div style='font-family:Arial; font-size:12px;'>"
                            popup_html += f"<b style='color:#2c3e50; font-size:14px;'>{info['nom']}</b><br>"
                            popup_html += f"<b>Total: {acad_counts[key]}</b><hr style='margin:5px 0;'>"
                            
                            for s_name, s_count in stats_acad.items():
                                short_name = (s_name[:30] + '..') if len(s_name) > 30 else s_name
                                popup_html += f"{short_name}: <b>{s_count}</b><br>"
                            
                            popup_html += "</div>"

                            folium.Marker(
                                info["coord"], 
                                icon=folium.Icon(color='blue', icon='graduation-cap', prefix='fa'), 
                                popup=folium.Popup(popup_html, max_width=300)
                            ).add_to(m)
                    
                    folium.LayerControl().add_to(m)
                    Fullscreen().add_to(m)
                    
                    # 6. AFFICHAGE OPTIMISÉ (SOLUTION 1)
                    st_folium(m, width="100%", height=600, returned_objects=[])

            # >>> PAGE 5 : PLAN FRANÇAIS
            elif page == "📖 Plan Français":
                st.markdown("### 📖 Participation au Plan Français")
                # TEXTE MIS À JOUR AVEC BOITE VERTE
                st.success("""
                Analyse d'impact du plan de formation national 'Français'. Observons si la participation à ce dispositif influence significativement les scores de compétence et les pratiques déclarées.
                """)
                st.markdown("<br>", unsafe_allow_html=True)
                st.divider()
                
                if col_plan and len(col_plan) > 0:
                    col_p = col_plan[0]
                    
                    st.subheader("📋 Résumé des réponses par Statut")
                    summary_data = []
                    for s in statuts_sel:
                        clean_s = s.replace("🟩 ", "")
                        mask = get_mask_for_status(clean_s, df) 
                        sub = df[mask]
                        nb_oui = len(sub[sub[col_p] == 'Oui'])
                        nb_non = len(sub[sub[col_p] == 'Non'])
                        summary_data.append({"Statut / Groupe": s, "✅ Oui": nb_oui, "❌ Non": nb_non, "Total": nb_oui + nb_non})
                    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)
                    st.divider()

                    st.subheader("📊 Visualisation graphique")
                    df_grouped = df_filtered.groupby([col_statut, col_p]).size().reset_index(name='Nb')
                    fig_bar = px.bar(df_grouped, x='Nb', y=col_statut, color=col_p, orientation='h', text='Nb', 
                                     color_discrete_map={"Oui": "#3498db", "Non": "#e74c3c"}, 
                                     category_orders={col_p: ["Oui", "Non"]})
                    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_bar, use_container_width=True)
                    st.divider()
                    
                    if total_cols:
                        col_score = total_cols[0]
                        st.subheader("📈 Impact sur la Note Globale")
                        df_compar = df_filtered[df_filtered[col_p].isin(['Oui', 'Non'])]
                        if not df_compar.empty:
                            c1, c2 = st.columns(2)
                            mean_oui = df_compar[df_compar[col_p] == 'Oui'][col_score].mean()
                            mean_non = df_compar[df_compar[col_p] == 'Non'][col_score].mean()
                            with c1:
                                st.metric("Moyenne (Oui)", f"{mean_oui:.2f}" if pd.notna(mean_oui) else "N/A")
                                st.metric("Moyenne (Non)", f"{mean_non:.2f}" if pd.notna(mean_non) else "N/A")
                            with c2:
                                # REMPLACEMENT BOÎTE A MOUSTACHE PAR HISTOGRAMME COMPARATIF (CODE MIS À JOUR)
                                avg_data = df_compar.groupby(col_p)[col_score].mean().reset_index()
                                avg_data.columns = [col_p, 'Score Moyen']
                                
                                fig_new = px.bar(
                                    avg_data, 
                                    x=col_p, 
                                    y='Score Moyen', 
                                    color=col_p, 
                                    title="Comparaison des Scores Moyens", 
                                    text_auto='.1f',
                                    range_y=[0, 100], 
                                    color_discrete_map={"Oui": "#3498db", "Non": "#e74c3c"},
                                    category_orders={col_p: ["Oui", "Non"]}
                                )
                                st.plotly_chart(fig_new, use_container_width=True)
                    
                    st.divider()
                    st.subheader("🔄 Comparaison directe entre Statuts (Détail Oui/Non)")
                    comp_selection = st.multiselect("Choisissez les statuts à comparer :", options=all_options, default=[NAME_FI, NAME_FC] if NAME_FI in all_options and NAME_FC in all_options else all_options[:2])

                    if comp_selection:
                        comp_data = []
                        for s in comp_selection:
                            clean_s = s.replace("🟩 ", "")
                            mask = get_mask_for_status(clean_s, df) 
                            sub_df = df[mask].copy()
                            sub_df['Groupe_Comparaison'] = s
                            comp_data.append(sub_df)
                        
                        if comp_data:
                            df_comp = pd.concat(comp_data)
                            df_comp_viz = df_comp[df_comp[col_p].isin(['Oui', 'Non'])]
                            if not df_comp_viz.empty:
                                df_stats = df_comp_viz.groupby(['Groupe_Comparaison', col_p]).agg(Score_Moyen=(total_cols[0], 'mean'), Nombre=('ID de la réponse', 'count')).reset_index()
                                df_stats['Label'] = df_stats.apply(lambda x: f"{x['Score_Moyen']:.2f} (n={x['Nombre']})", axis=1)
                                
                                fig_comp = px.bar(
                                    df_stats, x='Groupe_Comparaison', y='Score_Moyen', color=col_p, barmode='group',
                                    text='Label', title="Score Global Moyen par Statut et Participation",
                                    labels={'Groupe_Comparaison': 'Statut', 'Score_Moyen': 'Score Moyen (/100)', col_p: 'Plan Français'},
                                    color_discrete_map={"Oui": "#3498db", "Non": "#e74c3c"}, 
                                    category_orders={col_p: ["Oui", "Non"]}
                                )
                                fig_comp.update_traces(textposition='outside')
                                fig_comp.update_layout(yaxis_title="Score Moyen / 100", uniformtext_minsize=8, uniformtext_mode='hide')
                                st.plotly_chart(fig_comp, use_container_width=True)

                                st.markdown("---")
                                st.subheader("🏛️ Détail des 4 Piliers par Statut (Oui vs Non)")
                                
                                for col_partie, info in PARTIES_INFO.items():
                                    if col_partie in df_comp_viz.columns:
                                        stats_pilier = df_comp_viz.groupby(['Groupe_Comparaison', col_p]).agg(
                                            Score_Moyen=(col_partie, 'mean'),
                                            Nombre=('ID de la réponse', 'count')
                                        ).reset_index()
                                        stats_pilier['Label'] = stats_pilier.apply(lambda x: f"{x['Score_Moyen']:.2f} (n={x['Nombre']})", axis=1)
                                        
                                        fig_part = px.bar(
                                            stats_pilier, x='Groupe_Comparaison', y='Score_Moyen', color=col_p, barmode='group',
                                            text='Label', title=f"🔹 {info['titre']} (Max: {info['max_points']} pts)",
                                            labels={'Groupe_Comparaison': 'Statut', 'Score_Moyen': 'Note Moyenne', col_p: 'Plan Français'},
                                            color_discrete_map={"Oui": "#2ecc71", "Non": "#f1c40f"}, # Vert et Jaune
                                            category_orders={col_p: ["Oui", "Non"]}
                                        )
                                        fig_part.update_traces(textposition='outside')
                                        fig_part.update_layout(yaxis=dict(range=[0, info['max_points'] + 5]), yaxis_title="Note Moyenne")
                                        st.plotly_chart(fig_part, use_container_width=True, key=f"pilier_{col_partie}_comp")
                            else:
                                st.warning("Aucune donnée 'Oui' ou 'Non' trouvée.")
                    else:
                        st.info("Sélectionnez des statuts ci-dessus.")
                else:
                    st.warning("Colonne 'Plan Français' introuvable.")

            # >>> PAGE 6 : OUTILS NUMÉRIQUES
            elif page == "💻 Outils Numériques":
                st.markdown("### 💻 Usage des Outils Numériques")
                # TEXTE MIS À JOUR AVEC BOITE VERTE
                st.success("""
                Dans le cadre du projet SciCoNum, cette section évalue la maturité numérique des enseignants. Le numérique est-il utilisé comme un simple support ou comme un levier cognitif pour l'apprentissage de l'écriture ?
                """)
                st.markdown("<br>", unsafe_allow_html=True)
                st.divider()
                
                st.subheader("1. Usage général des outils (Ordinateur, Tablette...)")
                cols_tools = [c for c in df.columns if "Pour enseigner la production écrite à vos élèves, avez-vous déjà eu recours à des outils numériques comme" in c]
                
                if cols_tools:
                    tool_stats = []
                    for col in cols_tools:
                        tool_name = re.search(r'\[(.*?)\]', col)
                        tool_name = tool_name.group(1) if tool_name else col
                        
                        if "[Autre]" in col:
                            subset = df_filtered[col].dropna()
                            count = subset[subset.astype(str).str.strip() != ""].shape[0]
                        else:
                            count = df_filtered[df_filtered[col] == 'Oui'].shape[0]
                        
                        total = df_filtered.shape[0]
                        pct = (count / total * 100) if total > 0 else 0
                        tool_stats.append({"Outil": tool_name, "Utilisateurs": count, "Pourcentage": pct})
                    
                    df_tools = pd.DataFrame(tool_stats).sort_values("Utilisateurs", ascending=False)
                    
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.dataframe(df_tools.style.format({"Pourcentage": "{:.1f}%"}), use_container_width=True, hide_index=True)
                    with c2:
                        fig_global = px.bar(df_tools, x="Utilisateurs", y="Outil", orientation='h', text="Utilisateurs", title="Nombre d'utilisateurs par outil", color="Utilisateurs")
                        st.plotly_chart(fig_global, use_container_width=True)

                    st.subheader("Détail par Statut")
                    breakdown_data = []
                    for s in statuts_sel:
                        clean_s = s.replace("🟩 ", "")
                        mask = get_mask_for_status(clean_s, df)
                        sub = df[mask]
                        if len(sub) > 0:
                            for col in cols_tools:
                                tool_name = re.search(r'\[(.*?)\]', col).group(1)
                                if "[Autre]" in col:
                                    subset_sub = sub[col].dropna()
                                    nb_oui = subset_sub[subset_sub.astype(str).str.strip() != ""].shape[0]
                                else:
                                    nb_oui = len(sub[sub[col] == 'Oui'])
                                pct = (nb_oui / len(sub)) * 100
                                breakdown_data.append({"Statut": s, "Outil": tool_name, "Nombre": nb_oui, "Pourcentage": pct})
                    
                    if breakdown_data:
                        df_breakdown = pd.DataFrame(breakdown_data)
                        viz_type = st.radio("Type de visualisation :", ["Valeurs Absolues (Nombre)", "Pourcentage (%)"], horizontal=True)
                        y_val = "Nombre" if "Nombre" in viz_type else "Pourcentage"
                        fig_breakdown = px.bar(df_breakdown, x="Statut", y=y_val, color="Outil", barmode="group", title=f"Utilisation par Statut ({y_val})", text_auto='.1f' if "Pourcentage" in viz_type else True)
                        st.plotly_chart(fig_breakdown, use_container_width=True)
                else:
                    st.warning("Colonnes 'Outils numériques' (4.1) non trouvées.")

                st.divider()

                st.subheader("2. L'utilisation des logiciels et applications numériques")
                col_4_2 = None
                for c in df.columns:
                    if "4.2." in c and "Utilisez-vous actuellement des logiciels" in c:
                        col_4_2 = c
                        break
                
                if col_4_2:
                    vals = df_filtered[col_4_2].value_counts()
                    c1, c2 = st.columns(2)
                    with c1:
                        fig_pie = px.pie(values=vals.values, names=vals.index, title="Répartition Globale (Oui / Non)", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with c2:
                        breakdown_42 = []
                        for s in statuts_sel:
                            clean_s = s.replace("🟩 ", "")
                            mask = get_mask_for_status(clean_s, df)
                            sub = df[mask]
                            if len(sub) > 0 and col_4_2 in sub.columns:
                                total = len(sub)
                                nb_oui = len(sub[sub[col_4_2] == 'Oui'])
                                nb_non = len(sub[sub[col_4_2] == 'Non'])
                                
                                pct_oui = (nb_oui / total) * 100 if total > 0 else 0
                                pct_non = (nb_non / total) * 100 if total > 0 else 0
                                
                                breakdown_42.append({"Statut": s, "Réponse": "Oui", "Nombre": nb_oui, "Pourcentage": pct_oui})
                                breakdown_42.append({"Statut": s, "Réponse": "Non", "Nombre": nb_non, "Pourcentage": pct_non})
                        
                        if breakdown_42:
                            df_b42 = pd.DataFrame(breakdown_42)
                            fig_bar_42 = px.bar(
                                df_b42, 
                                x="Statut", 
                                y="Pourcentage", 
                                color="Réponse",
                                title="Répartition de l'utilisation par Statut (% Oui / % Non)", 
                                text_auto='.1f', 
                                barmode='stack',
                                color_discrete_map={"Oui": "#2ecc71", "Non": "#e74c3c"},
                                custom_data=["Nombre"]
                            )
                            fig_bar_42.update_traces(
                                hovertemplate="<br>".join([
                                    "<b>Réponse:</b> %{color}", 
                                    "<b>Statut:</b> %{x}", 
                                    "<b>Pourcentage:</b> %{y:.1f}%",
                                    "<b>Value:</b> %{customdata[0]}", 
                                    "<extra></extra>"
                                ])
                            )
                            fig_bar_42.update_layout(yaxis_title="Pourcentage (%)", legend_title_text="Utilisation")
                            st.plotly_chart(fig_bar_42, use_container_width=True)
                else:
                    st.warning("Colonne 4.2 introuvable dans le fichier.")

                st.divider()
                
                st.subheader('3. 📈 Corrélation : "Le numérique améliore-t-il la compétence enseignante ?"')
                if col_4_2 and total_cols:
                    df_impact = df_filtered[df_filtered[col_4_2].isin(['Oui', 'Non'])].copy()
                    metric_choice = st.radio("Choisir la compétence à analyser :", ["Score Global (Maîtrise générale)", "P3. Interventions & Difficultés", "P4. Outils Numériques"], horizontal=True)
                    
                    if "Global" in metric_choice:
                        y_col = total_cols[0]
                        max_val = 100 
                        title_graph = "Distribution du Score Global selon l'usage numérique"
                    elif "P3" in metric_choice:
                        y_col = "total_partie_3"
                        max_val = 28
                        title_graph = "Distribution du Score 'Interventions' selon l'usage numérique"
                    elif "P4" in metric_choice:
                        y_col = "total_partie_4"
                        max_val = 24
                        title_graph = "Distribution du Score 'Outils Numériques' selon l'usage numérique"

                    # --- MODIFICATION ICI : Remplacement du Boxplot par un Barplot comparatif ---
                    
                    # 1. Calcul des moyennes et des effectifs
                    df_avg = df_impact.groupby(col_4_2)[y_col].mean().reset_index()
                    df_avg.columns = [col_4_2, 'Score Moyen']
                    
                    df_counts = df_impact[col_4_2].value_counts().reset_index()
                    df_counts.columns = [col_4_2, 'Nombre']
                    
                    df_plot = pd.merge(df_avg, df_counts, on=col_4_2)
                    df_plot['Label'] = df_plot.apply(lambda x: f"{x['Score Moyen']:.1f} (n={x['Nombre']})", axis=1)

                    # 2. Calcul des indicateurs pour les métriques au-dessus du graphe
                    try:
                        mean_oui = df_plot[df_plot[col_4_2] == 'Oui']['Score Moyen'].values[0]
                    except IndexError: mean_oui = 0
                    try:
                        mean_non = df_plot[df_plot[col_4_2] == 'Non']['Score Moyen'].values[0]
                    except IndexError: mean_non = 0
                    delta = mean_oui - mean_non

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Moyenne (Utilisateurs)", f"{mean_oui:.2f}/{max_val}")
                    c2.metric("Moyenne (Non-Utilisateurs)", f"{mean_non:.2f}/{max_val}")
                    c3.metric("Écart (Impact)", f"{delta:+.2f}", delta_color="normal")

                    # 3. Création du Barplot
                    fig_impact = px.bar(
                        df_plot,
                        x=col_4_2,
                        y='Score Moyen',
                        color=col_4_2,
                        title=title_graph,
                        text='Label',
                        range_y=[0, max_val + (max_val*0.1)], # Marge de 10% au-dessus
                        color_discrete_map={"Oui": "#2ecc71", "Non": "#e74c3c"},
                        category_orders={col_4_2: ["Oui", "Non"]}
                    )
                    fig_impact.update_traces(textposition='outside')
                    fig_impact.update_layout(yaxis_title=f"Score Moyen (/{max_val})", uniformtext_minsize=8, uniformtext_mode='hide')
                    st.plotly_chart(fig_impact, use_container_width=True)

                st.divider()
                st.subheader('4. 🔥 La "Heatmap" (Carte de Chaleur) des Usages vs Statuts')
                heatmap_data = []
                if cols_tools:
                    for s in statuts_sel:
                        clean_s = s.replace("🟩 ", "")
                        mask = get_mask_for_status(clean_s, df)
                        sub = df[mask]
                        if len(sub) > 0:
                            for col in cols_tools:
                                tool_name = re.search(r'\[(.*?)\]', col)
                                tool_name = tool_name.group(1) if tool_name else "Autre"
                                
                                if "[Autre]" in col:
                                    nb_users = sub[col].dropna().apply(lambda x: 1 if str(x).strip() != "" else 0).sum()
                                else:
                                    nb_users = len(sub[sub[col] == 'Oui'])
                                
                                usage_pct = (nb_users / len(sub) * 100) if len(sub) > 0 else 0
                                heatmap_data.append({'Statut': s, 'Outil': tool_name, 'Taux (%)': usage_pct})

                    if heatmap_data:
                        df_heatmap = pd.DataFrame(heatmap_data)
                        fig_heat = px.density_heatmap(
                            df_heatmap, x="Outil", y="Statut", z="Taux (%)", text_auto='.1f',
                            color_continuous_scale="Viridis", title="Intensité d'usage par Statut (%)"
                        )
                        fig_heat.update_layout(xaxis_title="", yaxis_title="")
                        st.plotly_chart(fig_heat, use_container_width=True)

            # >>> PAGE 7 : NOUVEAU - ANALYSE PAR ANCIENNETÉ
            elif page == "⏳ Ancienneté":
                st.markdown("### ⏳ Analyse par Ancienneté (Cycle de Vie)")
                # TEXTE MIS À JOUR AVEC BOITE VERTE
                st.success("""
                Cette section permet de vérifier l'évolution des compétences et des pratiques en fonction de l'expérience professionnelle.
                """)
                st.markdown("<br>", unsafe_allow_html=True)
                st.divider()

                # 1. DÉTECTION COLONNE ANCIENNETÉ (FIX)
                col_anciennete = None
                for c in df.columns:
                    if "combien" in c.lower() and "années" in c.lower() and "enseignez" in c.lower():
                        col_anciennete = c
                        break
                
                if col_anciennete:
                    # 2. NETTOYAGE ET CRÉATION DES TRANCHES (LOGIQUE MISE À JOUR)
                    def categoriser_anciennete(val):
                        val_str = str(val).lower().strip()
                        
                        # Cas spécifique vide (Non concerné)
                        if pd.isna(val) or val_str == "" or val_str == "nan":
                            return "4. Non concernés"
                        
                        # Cas spécifique texte "+10 ans" ou "plus de 10 ans"
                        if "+10" in val_str or "plus de 10" in val_str:
                            return "3. Seniors (+10 ans)"
                            
                        try:
                            nums = re.findall(r'\d+', val_str)
                            if nums:
                                years = int(nums[0])
                                if years <= 3: return "1. Néo-titulaires (0-3 ans)"
                                elif years <= 10: return "2. Juniors (4-10 ans)"
                                else: return "3. Seniors (+10 ans)"
                        except:
                            pass
                        return "4. Non concernés" # Fallback si pas de chiffre

                    df_exp = df_filtered.copy()
                    df_exp['Tranche_Exp'] = df_exp[col_anciennete].apply(categoriser_anciennete)
                    
                    if not df_exp.empty:
                        # Calcul des effectifs (Tout le monde pour l'affichage en haut)
                        nb_neo = len(df_exp[df_exp['Tranche_Exp'] == "1. Néo-titulaires (0-3 ans)"])
                        nb_jun = len(df_exp[df_exp['Tranche_Exp'] == "2. Juniors (4-10 ans)"])
                        nb_sen = len(df_exp[df_exp['Tranche_Exp'] == "3. Seniors (+10 ans)"])
                        
                        df_nc = df_exp[df_exp['Tranche_Exp'] == "4. Non concernés"]
                        nb_nc = len(df_nc)
                        
                        nb_fc_detail = 0
                        if col_statut_autre:
                            nb_fc_detail = df_nc[col_statut_autre].astype(str).str.contains("FC", case=False, na=False).sum()

                        # Affichage "Joli" en haut (4 colonnes)
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("🌱 Néo-titulaires", f"{nb_neo}", "0-3 ans")
                        m2.metric("🚀 Juniors", f"{nb_jun}", "4-10 ans")
                        m3.metric("👑 Seniors", f"{nb_sen}", "+10 ans")
                        
                        m4.metric("🎓 Non concernés", f"{nb_nc}", f"Dont {nb_fc_detail} FC (Autre)")
                        with m4:
                            st.caption("Étudiants/Stagiaires dont la FC n’a pas répondu")

                        st.divider()

                        # --- FILTRE ACTIFS UNIQUEMENT POUR GRAPHIQUES 1 À 4 ---
                        df_active = df_exp[df_exp['Tranche_Exp'] != "4. Non concernés"]

                        # A. RÉPARTITION
                        st.subheader("1. Répartition de l'échantillon")
                        c1, c2 = st.columns(2)
                        # Utilisation de df_active ici
                        counts = df_active['Tranche_Exp'].value_counts().sort_index()
                        with c1:
                            fig_pie = px.pie(values=counts.values, names=counts.index, title="Distribution par Ancienneté (Actifs)", 
                                             color_discrete_sequence=px.colors.qualitative.Pastel)
                            st.plotly_chart(fig_pie, use_container_width=True)
                        
                        with c2:
                            pass

                        st.divider()

                        # B. COMPÉTENCE THÉORIQUE
                        st.subheader("2. Évolution des Compétences Didactiques")
                        if total_cols:
                            # Utilisation de df_active ici
                            df_scores = df_active.groupby('Tranche_Exp')[[total_cols[0], 'total_partie_2', 'total_partie_3']].mean().reset_index()
                            
                            fig_scores = go.Figure()
                            fig_scores.add_trace(go.Bar(x=df_scores['Tranche_Exp'], y=df_scores[total_cols[0]], name='Score Global (/100)', marker_color='#3498db'))
                            fig_scores.add_trace(go.Bar(x=df_scores['Tranche_Exp'], y=df_scores['total_partie_2'], name='Partie 2: Théorie (/32)', marker_color='#e74c3c'))
                            fig_scores.add_trace(go.Bar(x=df_scores['Tranche_Exp'], y=df_scores['total_partie_3'], name='Partie 3: Pratique (/28)', marker_color='#2ecc71'))
                            
                            fig_scores.update_layout(barmode='group', title="Scores Moyens par Ancienneté")
                            st.plotly_chart(fig_scores, use_container_width=True)

                        st.divider()

                        # 4. SECTION DÉTAILLÉE (NEW)
                        st.subheader("3. 🧠 Analyse Détaillée par Compétence (Focus)")
                        st.info("Sélectionnez une thématique ci-dessous pour voir comment la maîtrise évolue avec l'expérience.")

                        # Dictionary for mapping: Title -> Column Name
                        options_map = {info['titre']: col for col, info in PARTIES_INFO.items() if col in df.columns}

                        # Selectbox
                        choix_partie = st.selectbox("👇 Choisir le domaine à explorer :", options=list(options_map.keys()))
                        col_target = options_map[choix_partie]
                        info_target = PARTIES_INFO[col_target]

                        # Calculation sur df_active UNIQUEMENT
                        df_focus = df_active.groupby('Tranche_Exp')[col_target].mean().reset_index()
                        df_focus.columns = ['Tranche', 'Score_Moyen']

                        # Add Percentage for Label
                        df_focus['Pourcentage'] = (df_focus['Score_Moyen'] / info_target['max_points']) * 100
                        df_focus['Label'] = df_focus.apply(lambda x: f"{x['Score_Moyen']:.1f}/{info_target['max_points']} ({x['Pourcentage']:.0f}%)", axis=1)

                        # Chart
                        fig_focus = px.bar(
                            df_focus,
                            x='Tranche',
                            y='Score_Moyen',
                            color='Tranche', 
                            text='Label',
                            title=f"Score Moyen : {info_target['short']}",
                            color_discrete_sequence=px.colors.qualitative.Bold, 
                            range_y=[0, info_target['max_points'] + (info_target['max_points']*0.1)] 
                        )
                        fig_focus.update_layout(showlegend=False, xaxis_title="", yaxis_title=f"Note sur {info_target['max_points']}")
                        st.plotly_chart(fig_focus, use_container_width=True)
                        
                        st.divider()
                        
                        # 5. NOUVELLE SECTION : COMPARAISON FI VS TERRAIN (Ici on garde tout le monde)
                        st.subheader("4. 🎓 Trajectoire : De la Formation Initiale à l'Expertise")
                        st.markdown("Comparaison directe entre les **futurs enseignants (FI / Sans expérience)** et les **enseignants en poste** (Néos, Juniors, Seniors).")
                        
                        # Préparation des données pour le graphique 5 (On utilise df_exp complet ici)
                        df_traj = df_exp.copy()
                        df_traj['Tranche_Exp'] = df_traj['Tranche_Exp'].replace("4. Non concernés", "0. Formation Initiale (Sans exp.)")
                        
                        # On regroupe par tranche
                        cols_to_agg = [total_cols[0]] + list(PARTIES_INFO.keys())
                        cols_to_agg = [c for c in cols_to_agg if c in df_traj.columns] # Sécurité
                        
                        traj_stats = df_traj.groupby('Tranche_Exp')[cols_to_agg].mean().reset_index()
                        
                        # Graphique 1 : Score Global
                        fig_traj_global = px.bar(
                            traj_stats,
                            x='Tranche_Exp',
                            y=total_cols[0],
                            color='Tranche_Exp',
                            title="Évolution du Score Global (/100)",
                            text_auto='.1f',
                            color_discrete_sequence=px.colors.qualitative.Prism
                        )
                        fig_traj_global.update_layout(showlegend=False, xaxis_title="", yaxis_title="Score Global")
                        st.plotly_chart(fig_traj_global, use_container_width=True)
                        
                        # Graphique 2 : Détail par partie (Pourcentages) pour comparer les forces
                        st.markdown("#### 🔎 Forces et Faiblesses relatives")
                        st.caption("Les scores sont ramenés en pourcentage (%) pour comparer les domaines entre eux.")
                        
                        # Transformation des données pour affichage groupé
                        radar_data = []
                        for idx, row in traj_stats.iterrows():
                            tranche = row['Tranche_Exp']
                            for col_part, info in PARTIES_INFO.items():
                                if col_part in traj_stats.columns:
                                    score = row[col_part]
                                    pct = (score / info['max_points']) * 100
                                    radar_data.append({"Tranche": tranche, "Domaine": info['short'], "Pourcentage": pct})
                        
                        if radar_data:
                            df_radar_traj = pd.DataFrame(radar_data)
                            fig_grouped = px.bar(
                                df_radar_traj,
                                x="Domaine",
                                y="Pourcentage",
                                color="Tranche",
                                barmode="group",
                                title="Comparaison détaillée par domaine de compétence",
                                text_auto='.0f'
                            )
                            fig_grouped.update_layout(yaxis_title="Réussite (%)", yaxis_range=[0, 100])
                            st.plotly_chart(fig_grouped, use_container_width=True)


                    else:
                        st.warning("Aucune donnée valide trouvée pour la colonne ancienneté.")
                else:
                    st.error("Colonne 'Ancienneté' introuvable.")

            # >>> PAGE 8 : LE MATCH
            elif page == "⚡ Théorie vs Pratique":
                st.markdown("### ⚡ Théorie vs Pratique")
                
                # --- DÉBUT DU BLOC D'INTRODUCTION (BOITE VERTE MISE À JOUR) ---
                st.success("""
                **🎯 L'objectif de cette analyse :**
                Il n'est pas toujours facile d'aligner ce que l'on **sait** (les mécanismes cognitifs de l'élève) avec ce que l'on **fait** en classe (les gestes pédagogiques). Cette section visualise cet équilibre.
                
                **🧮 La méthode de calcul :**
                Comme les parties n'ont pas le même barème (la Théorie est sur 32 points, la Pratique sur 28), nous avons converti tous les scores en **pourcentages (%)** pour pouvoir les comparer équitablement.
                
                **🔍 Comment lire votre profil ?**
                Le logiciel compare vos deux pourcentages et définit votre profil selon l'écart constaté :
                * 📘 **Théoriciens :** Votre score théorique est supérieur à votre score pratique de plus de **5%**. Vous maîtrisez bien les concepts scientifiques.
                * 🛠️ **Pragmatiques :** Votre score pratique est supérieur à votre score théorique de plus de **5%**. Vous êtes avant tout un expert du terrain.
                * ⚖️ **Équilibrés :** L'écart entre vos connaissances et vos pratiques est minime (**moins de 5%**). Vous mobilisez vos savoirs théoriques directement dans l'action.
                """)
                st.markdown("<br>", unsafe_allow_html=True)
                # --- FIN DU BLOC ---

                st.divider()
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    color_map = {"Théoriciens": "#e74c3c", "Pragmatiques": "#3498db", "Équilibrés": "#2ecc71"}
                    fig = px.scatter(df_filtered, x='Pct_Theorie', y='Pct_Pratique', color='Profil_Match', color_discrete_map=color_map, hover_data=[col_statut], title="Nuage de points")
                    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(color="Gray", width=2, dash="dash"))
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.dataframe(df_filtered['Profil_Match'].value_counts(), use_container_width=True)
                
                st.divider()
                st.subheader("🕵️‍♂️ Analyse croisée : Qui sont les participants au Plan Français ?")
                c1, c2 = st.columns(2)
                
                local_options = [NAME_FI, NAME_FC] + sorted([str(x) for x in df[col_statut].unique() if pd.notna(x)])
                sel_statut_match = c1.multiselect("Restreindre par Statut :", options=local_options, default=local_options[:2])
                
                if col_plan:
                    options_plan = df_filtered[col_plan[0]].dropna().unique()
                    sel_plan_match = c2.multiselect("Filtrer par réponse au Plan Français :", options=options_plan, default=options_plan)
                    
                    mask_statut_cross = pd.Series(False, index=df.index)
                    for s in sel_statut_match:
                        clean_s = s.replace("🟩 ", "")
                        mask_statut_cross = mask_statut_cross | get_mask_for_status(clean_s, df)
                    
                    df_cross = df[mask_statut_cross & df[col_plan[0]].isin(sel_plan_match)]
                    
                    fig_cross = px.histogram(
                        df_cross, x=col_plan[0], color="Profil_Match", barmode="group",
                        title="Répartition des Profils (Pragmatique/Théoricien) selon la participation", text_auto=True,
                        color_discrete_map={"Théoriciens": "#e74c3c", "Pragmatiques": "#3498db", "Équilibrés": "#2ecc71"}
                    )
                    st.plotly_chart(fig_cross, use_container_width=True)

else:
    # Page vide si pas de fichier
    st.info("En attente de fichier...")
