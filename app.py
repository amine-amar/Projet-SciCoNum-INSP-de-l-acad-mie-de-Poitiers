import streamlit as st
import pandas as pd
import plotly.express as px
import io
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
from streamlit_option_menu import option_menu
from PIL import Image

# --- ANALYSE STATISTIQUE & ML ---
from scipy import stats  # Indispensable pour T-test, ANOVA, Chi-2
import statsmodels.api as sm # Indispensable pour Régression & Tukey
from sklearn.preprocessing import StandardScaler # Pour normaliser les données
from sklearn.cluster import KMeans # Pour le clustering
from sklearn.decomposition import PCA # Pour l'analyse factorielle
from sklearn.metrics import roc_curve, auc

# Cette ligne permet d'éviter l'erreur "NameError: SKLEARN_AVAILABLE"
# dans les blocs de code précédents.
SKLEARN_AVAILABLE = True

# ==========================================
# 1. CONFIGURATION ET DONNÉES STATIQUES
# ==========================================
st.set_page_config(page_title="Analyse Production Écrite", page_icon="📊", layout="wide")

# --- STYLE CSS PERSONNALISÉ ---
# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
<style>
    /* ==============================================================
       NOUVEAU STYLE DES ONGLETS (Design "Boutons" Multilignes)
       ============================================================== */
    /* 1. Forcer le conteneur à passer à la ligne (Wrap) */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {
        flex-wrap: wrap !important;
        gap: 10px 6px; /* 10px d'espace vertical, 6px d'espace horizontal */
    }

    /* 2. Désactiver la grande ligne grise de base de Streamlit qui casse le multiligne */
    div[data-testid="stTabs"] > div:first-child {
        border-bottom: none !important; 
    }

    /* 3. Style des onglets inactifs */
    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        background-color: #f8f9fa !important; 
        border: 1px solid #dee2e6 !important; 
        border-radius: 8px !important; /* Arrondi sur les 4 coins */
        padding: 8px 16px !important;
        color: #495057 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        transition: all 0.2s ease-in-out;
        margin: 0 !important; /* Les marges sont gérées par le 'gap' au-dessus */
    }

    /* 4. Effet au survol (Hover) */
    div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
        background-color: #e9ecef !important;
        color: #FF4B4B !important;
        border-color: #FF4B4B !important;
    }

    /* 5. Style de l'onglet ACTIF (Celui sélectionné) */
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background-color: #FF4B4B !important; /* Fond couleur thème */
        color: white !important; /* Texte blanc */
        border: 1px solid #FF4B4B !important;
        box-shadow: 0px 4px 10px rgba(255, 75, 75, 0.3) !important; /* Petite ombre */
    }
    /* ============================================================== */

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
NOM_FICHIER_BASE = "506"

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

# ==============================================================================
# 🛠️ FONCTION MANQUANTE : CALCUL DU TOP/FLOP
# ==============================================================================
def get_top_flop_stats(dataframe, label="Global"):
    """
    Calcule les taux de réussite.
    CORRECTION : Force la conversion en nombres pour éviter l'erreur TypeError.
    """
    import pandas as pd
    import re

    items_stats = []
    
    if dataframe.empty:
        return []

    # Repérage des colonnes scores
    score_cols = [c for c in dataframe.columns if str(c).strip().lower().startswith('score_')]
    
    for col in score_cols:
        # --- ETAPE CLÉ : CALCUL DU BARÈME (MAX) ---
        try:
            # 1. On essaie de récupérer la colonne dans le DF global (variable 'df')
            # pour avoir le vrai max de tout le fichier
            if 'df' in globals():
                col_data = df[col]
            else:
                col_data = dataframe[col]
            
            # 2. CONVERSION FORCÉE EN NUMÉRIQUE (C'est ça qui corrige votre erreur)
            # 'coerce' transforme les erreurs (textes bizarres) en NaN
            col_numeric = pd.to_numeric(col_data, errors='coerce')
            
            # 3. On prend le max des valeurs numériques
            max_points = col_numeric.max()
            
        except Exception:
            max_points = 1 # Valeur par défaut si tout échoue
            
        # Sécurité : Si le max est vide (NaN) ou 0, on met 1 pour éviter la division par zéro
        if pd.isna(max_points) or max_points == 0: 
            max_points = 1
            
        # --- CALCULS STATISTIQUES ---
        # Maintenant max_points est sûr d'être un nombre (float ou int)
        if max_points > 0:
            # Conversion des données du groupe filtré
            scores_group = pd.to_numeric(dataframe[col], errors='coerce').fillna(0)
            avg_score = scores_group.mean()
            
            # Nettoyage du nom (Esthétique)
            clean_name = re.sub(r'^score_', '', str(col), flags=re.IGNORECASE).strip()
            clean_name = clean_name.split('[')[0].strip()
            
            match = re.match(r'^(\d+(\.\d+)*)', clean_name)
            if match:
                num = match.group(1)
                rest = clean_name[len(num):].strip(" .)-:")
                if len(rest) > 65: rest = rest[:65] + "..."
                clean_name = f"<b>{num}.</b> {rest}"
            else:
                if len(clean_name) > 70: clean_name = clean_name[:70] + "..."

            success_rate = (avg_score / max_points) * 100
            
            items_stats.append({
                'Question': clean_name,
                'Réussite (%)': success_rate,
                'Score Moyen': avg_score,
                'Max Points': max_points,
                'Groupe': label
            })
    
    return items_stats

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
    # --- NAVIGATION CATÉGORISÉE ULTRA-COMPACTE ---
    
    # 1. CSS MAGIQUE : Force Streamlit à enlever les espaces dans la barre latérale
    st.markdown("""
    <style>
        /* Supprime l'espace vertical entre les éléments de la barre latérale */
        [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
            gap: 0.1rem !important;
        }
        /* Réduit l'épaisseur des boutons pour qu'ils soient plus fins */
        [data-testid="stSidebar"] .stButton button {
            min-height: 30px !important;
            padding-top: 2px !important;
            padding-bottom: 2px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("📌 Menu Principal")
    
    # 2. Initialisation de la mémoire
    if 'page' not in st.session_state:
        st.session_state.page = "🏠 Accueil & Contexte"

    # 3. Fonction pour les boutons
    def menu_button(label):
        btn_type = "primary" if st.session_state.page == label else "secondary"
        if st.sidebar.button(label, type=btn_type, use_container_width=True):
            st.session_state.page = label
            st.rerun()

   # 4. Fonction pour des titres
    def menu_section(title):
        st.sidebar.markdown(
            f"""<div style="margin-top: 20px; margin-bottom: 30px; font-size: 0.75rem; font-weight: 700; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px;">
            {title}
            </div>""", 
            unsafe_allow_html=True
        )

    # 5. Fonction ligne de séparation (AVEC ESPACE AU DESSUS)
    def menu_divider():
        st.sidebar.markdown(
            '<div style="border-top: 1px solid #e6e6e6; margin-top: 20px; margin-bottom: 0px;"></div>', 
            unsafe_allow_html=True
        )

    # --- CONSTRUCTION DU MENU ---
    
    menu_section("Introduction")
    menu_button("🏠 Accueil & Contexte")

    menu_divider()
    menu_section("Vue d'ensemble")
    menu_button("📊 Analyse Descriptive")
    menu_button("🌍 Carte Géographique")
    menu_button("🏆 Top/Flop 5Q")

    menu_divider()
    menu_section("Thématiques")
    menu_button("⏳ Ancienneté")
    menu_button("💻 Outils Numériques")
    menu_button("📖 Plan Français")
    menu_button("⚡ Théorie vs Pratique")

    menu_divider()
    menu_section("Outils Avancés")
    menu_button("📈 Tests Statistiques")
    menu_button("🧠 Assistant Cognitif")

    # Mise à jour de la variable page pour le reste du code
    page = st.session_state.page

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
    # >>> AUTRES PAGES (AVEC FILTRES)
    else:
        st.title("📊 Tableau de Bord : Production Écrite")
        
        # =========================================================
        # 1. ZONE FIXE : LA POPULATION GLOBALE (100% Natif Streamlit)
        # =========================================================
        st.markdown("##### 👥 Base de données globale (Chiffres fixes)")
        
        # Utilisation d'un conteneur avec bordure (crée un joli cadre gris clair)
        with st.container(border=True):
            kpi1, kpi2, kpi3 = st.columns(3)
            # On affiche les métriques simplement
            kpi1.metric("Total des répondants", nb_total)
            kpi2.metric("Formation Initiale (FI)", nb_fi)
            kpi3.metric("Formation Continue (FC)", nb_fc)
            
        st.markdown("---") # Ligne de séparation classique
        # =========================================================
        # 2. ZONE D'INTERACTION : LA TÉLÉCOMMANDE
        # =========================================================
        st.markdown("### 🎛️ Filtrez les données des graphiques ci-dessous")
        
        # --- GÉNÉRATION DES OPTIONS DE BASE ---
        standard_options = sorted([str(x) for x in df[col_statut].unique() if pd.notna(x)])
        display_standards = [f"🟩 {x}" for x in standard_options]
        all_options = [NAME_FI, NAME_FC] + display_standards
        
        # Création de la liste pour les pilules
        pill_options = ["🌍 TOUS (Désactiver les filtres)", NAME_FI, NAME_FC] + display_standards

        # 💊 LES PILULES CLICQUABLES
        try:
            selected_pills = st.pills(
                "Cliquez sur les étiquettes pour cibler un public (Plusieurs choix possibles) :", 
                options=pill_options, 
                default=["🌍 TOUS (Désactiver les filtres)"],
                selection_mode="multi"
            )
        except Exception:
            selected_pills = st.multiselect(
                "Sélectionnez les statuts :", 
                options=pill_options, 
                default=["🌍 TOUS (Désactiver les filtres)"]
            )

        # Initialisation
        final_mask = pd.Series(False, index=df.index)
        statuts_sel = [] 
        
        # --- LOGIQUE DE FILTRAGE DES PILULES ---
        if not selected_pills or "🌍 TOUS (Désactiver les filtres)" in selected_pills:
            final_mask = pd.Series(True, index=df.index) # On prend tout le monde
            statuts_sel = [NAME_FI, NAME_FC]
        else:
            if NAME_FI in selected_pills:
                final_mask = final_mask | mask_fi_list | mask_fi_autre
                statuts_sel.append(NAME_FI)
            
            if NAME_FC in selected_pills:
                final_mask = final_mask | mask_fc_list | mask_fc_autre
                statuts_sel.append(NAME_FC)
                
            selected_standards_display = [s for s in selected_pills if s.startswith("🟩")]
            selected_standards_raw = [s.replace("🟩 ", "") for s in selected_standards_display]
            
            if selected_standards_raw:
                final_mask = final_mask | df[col_statut].isin(selected_standards_raw)
                statuts_sel.extend(selected_standards_display)
        
        # --- APPLICATION DU FILTRE FINAL ---
        df_filtered = df[final_mask]

        # =========================================================
        # 3. FEEDBACK VISUEL POUR L'UTILISATEUR (La magie opère ici)
        # =========================================================
        if len(df_filtered) == 0:
            st.warning("⚠️ Aucune donnée ne correspond aux filtres sélectionnés. Veuillez modifier votre choix.")
        elif len(df_filtered) == nb_total:
            st.info("💡 **Aperçu global :** Les graphiques ci-dessous analysent actuellement **100% de l'échantillon**.")
        else:
            pct_filtered = (len(df_filtered) / nb_total) * 100
            st.success(f"🎯 **Filtre Actif :** Les graphiques ci-dessous sont maintenant recalculés sur **{len(df_filtered)} participants** (soit {pct_filtered:.0f}% de la base globale).")

        st.markdown("<br>", unsafe_allow_html=True) # Un petit espace avant les graphiques

        # Sécurité : On n'affiche la suite que si on a des données
        if len(df_filtered) > 0:
            
      
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
                
                # MISE À JOUR : Onglet supprimé d'ici
                tab1, tab2, tab_quotite, tab_zone, tab_multi, tab3, tab4, tab5 = st.tabs([
                    "Vue d'ensemble", 
                    "Démographie", 
                    "Quotité de travail", 
                    "Zone géographique", 
                    "Classes Multi-niveaux",
                    "Score Global", 
                    "Analyse par Parties", 
                    "Analyse Comparative"
                ])
                
                with tab1:
                    # =========================================================
                    # 1. CHIFFRES CLÉS (Cartes de type "Dashboard Pro")
                    # =========================================================
                    st.markdown("### 📈 Chiffres Clés")
                    
                    if total_cols:
                        score_moyen = f"{df_filtered[total_cols[0]].mean():.1f}"
                        score_max = f"{df_filtered[total_cols[0]].max():.0f}"
                        score_min = f"{df_filtered[total_cols[0]].min():.0f}"
                    else:
                        score_moyen, score_max, score_min = "N/A", "N/A", "N/A"
                        
                    c1, c2, c3, c4 = st.columns(4)
                    
                    with c1:
                        with st.container(border=True):
                            st.markdown(f"<div style='text-align: center; padding: 10px;'><span style='font-size: 2rem;'>👥</span><br><b style='color: gray; font-size: 0.85rem; text-transform: uppercase;'>Participants</b><br><span style='font-size: 2.2rem; font-weight: 800;'>{len(df_filtered)}</span></div>", unsafe_allow_html=True)
                            
                    with c2:
                        with st.container(border=True):
                            st.markdown(f"<div style='text-align: center; padding: 10px;'><span style='font-size: 2rem;'>🎯</span><br><b style='color: gray; font-size: 0.85rem; text-transform: uppercase;'>Score Moyen</b><br><span style='font-size: 2.2rem; font-weight: 800; color: #3498db;'>{score_moyen}</span></div>", unsafe_allow_html=True)

                    with c3:
                        with st.container(border=True):
                            st.markdown(f"<div style='text-align: center; padding: 10px;'><span style='font-size: 2rem;'>🏆</span><br><b style='color: gray; font-size: 0.85rem; text-transform: uppercase;'>Score Max</b><br><span style='font-size: 2.2rem; font-weight: 800; color: #2ecc71;'>{score_max}</span></div>", unsafe_allow_html=True)

                    with c4:
                        with st.container(border=True):
                            st.markdown(f"<div style='text-align: center; padding: 10px;'><span style='font-size: 2rem;'>📉</span><br><b style='color: gray; font-size: 0.85rem; text-transform: uppercase;'>Score Min</b><br><span style='font-size: 2.2rem; font-weight: 800; color: #e74c3c;'>{score_min}</span></div>", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # =========================================================
                    # 2. RÉPARTITION PAR STATUT (Design Grille)
                    # =========================================================
                    # =========================================================
                    # 2. RÉPARTITION PAR STATUT (Design Grille)
                    # =========================================================
                    st.markdown("### 💼 Répartition détaillée par Statut")
                    status_counts = df_filtered[col_statut].value_counts()

                    if len(status_counts) > 0:
                        # On garde 4 colonnes pour l'affichage, mais on laisse le texte entier
                        cols_statut_grid = st.columns(4) 
                        for i, (statut_name, count) in enumerate(status_counts.items()):
                            with cols_statut_grid[i % 4]:
                                with st.container(border=True):
                                    # AFFICHAGE DU NOM COMPLET (statut_name brut)
                                    st.markdown(f"""
                                    <div style='text-align: center; padding: 5px;'>
                                        <div style='color: #555; font-size: 0.85rem; font-weight: 600; min-height: 80px; display: flex; align-items: center; justify-content: center;'>
                                            {statut_name}
                                        </div>
                                        <div style='font-size: 1.8rem; font-weight: 800; color: #2c3e50;'>{count}</div>
                                    </div>
                                    """, unsafe_allow_html=True)

                    # =========================================================
                    # 3. TOP 3 ACADÉMIES (Design Podium)
                    # =========================================================
                    st.markdown("### 📍 Top 3 des Académies représentées")
                    if not df_filtered.empty and col_academie:
                        top_acads = df_filtered[col_academie].value_counts().head(3)
                        
                        cols_acad = st.columns(3)
                        medals = ['🥇', '🥈', '🥉']
                        for i, (name, count) in enumerate(top_acads.items()):
                            if i < 3:
                                with cols_acad[i]:
                                    with st.container(border=True):
                                        st.markdown(f"""
                                        <div style='text-align: center; padding: 10px;'>
                                            <div style='font-size: 2rem; margin-bottom: 5px;'>{medals[i]}</div>
                                            <div style='font-size: 1rem; font-weight: 700;'>{name}</div>
                                            <div style='color: gray; font-size: 0.9rem; margin-top: 5px;'><b>{count}</b> répondants</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                    else:
                        st.info("Aucune donnée d'académie n'est disponible pour cette sélection.")
                
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

            # --- PAGE 3 : TOP / FLOP 5 QUESTIONS ---
            elif page == "🏆 Top/Flop 5Q":
                st.header("🏆 Les réussites et les difficultés (Top/Flop 5)")
                st.markdown("Quels sont les concepts les mieux maîtrisés et ceux qui posent problème ?")
                st.divider()
                
                # --- 1. ANALYSE GLOBALE ---
                st.subheader("1. Analyse Globale (Selon filtre latéral)")
                
                # Appel de la nouvelle fonction
                global_stats = get_top_flop_stats(df_filtered, "Sélection Actuelle")
                
                if global_stats:
                    df_items = pd.DataFrame(global_stats)
                    
                    # Tri des meilleurs et moins bons
                    top_5 = df_items.sort_values('Réussite (%)', ascending=False).head(5)
                    bottom_5 = df_items.sort_values('Réussite (%)', ascending=True).head(5)
                    
                    top_5['Type'] = 'Top 5 (Acquis)'
                    bottom_5['Type'] = 'Flop 5 (À renforcer)'
                    
                    # Fusion et ordre pour le graphique
                    df_plot = pd.concat([top_5, bottom_5.sort_values('Réussite (%)', ascending=False)])
                    
                    # Graphique
                    fig = px.bar(
                        df_plot, 
                        x='Réussite (%)', 
                        y='Question', 
                        color='Type', 
                        text_auto='.1f', 
                        orientation='h',
                        color_discrete_map={'Top 5 (Acquis)': '#2ecc71', 'Flop 5 (À renforcer)': '#e74c3c'},
                        title="Top 5 vs Flop 5"
                    )
                    
                    fig.update_layout(
                        yaxis={
                            'categoryorder':'total ascending',
                            'tickfont': {'size': 14} # Police lisible
                        },
                        xaxis_title="Taux de Réussite Moyen (%)",
                        margin=dict(l=10),
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Aucune colonne de score ('score_...') trouvée pour l'analyse.")

                st.divider()

                # --- 2. COMPARAISON ENTRE GROUPES ---
                st.subheader("2. Comparaison Top/Flop entre Statuts")
                
                c1, c2 = st.columns(2)
                group_A = c1.selectbox("Groupe A :", options=all_options, index=0, key="tf_A")
                group_B = c2.selectbox("Groupe B :", options=all_options, index=1 if len(all_options)>1 else 0, key="tf_B")
                
                if group_A and group_B:
                    # Filtres
                    clean_A = group_A.replace("🟩 ", "")
                    clean_B = group_B.replace("🟩 ", "")
                    mask_A = get_mask_for_status(clean_A, df)
                    mask_B = get_mask_for_status(clean_B, df)
                    
                    # Calculs pour chaque groupe
                    stats_A = get_top_flop_stats(df[mask_A], clean_A)
                    stats_B = get_top_flop_stats(df[mask_B], clean_B)
                    
                    if stats_A and stats_B:
                        # On affiche deux graphiques côte à côte
                        col_g1, col_g2 = st.columns(2)
                        
                        for col_st, stats, g_name in [(col_g1, stats_A, clean_A), (col_g2, stats_B, clean_B)]:
                            df_i = pd.DataFrame(stats)
                            # On prend le Top 5 et Flop 5 de ce groupe
                            t5 = df_i.sort_values('Réussite (%)', ascending=False).head(5)
                            b5 = df_i.sort_values('Réussite (%)', ascending=True).head(5)
                            t5['Type'] = 'Top 5'
                            b5['Type'] = 'Flop 5'
                            
                            df_p = pd.concat([t5, b5.sort_values('Réussite (%)', ascending=False)])
                            
                            with col_st:
                                st.markdown(f"**Top 5 & Flop 5 : 🟦 {g_name}**")
                                fig_g = px.bar(
                                    df_p, x='Réussite (%)', y='Question', color='Type',
                                    text_auto='.0f', orientation='h',
                                    color_discrete_map={'Top 5': '#2ecc71', 'Flop 5': '#e74c3c'}
                                )
                                fig_g.update_layout(
                                    yaxis={'categoryorder':'total ascending', 'visible': True}, # On garde les labels
                                    xaxis_title="Réussite (%)",
                                    showlegend=False,
                                    height=400,
                                    margin=dict(l=0)
                                )
                                st.plotly_chart(fig_g, use_container_width=True)

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

                # CRÉATION DES ONGLETS (MISE A JOUR : 6 Onglets)
                tab1, tab2, tab4, tab6, tab7, tab8 = st.tabs([
                    "📊 Usage & Outils", 
                    "📈 Impact sur la Compétence",
                    "👥 Typologie d'Usager",
                    "🗺️ Fracture Numérique Territoriale",
                    "✍️ L'Hypothèse Révision",
                    "🎓 Efficacité de la Formation"
                ])

                # --- ONGLET 1 : Usage général et Logiciels ---
                with tab1:
                    st.subheader("1. Usage général des outils (Ordinateur, Tablette...)")
                    cols_tools = [c for c in df.columns if "Pour enseigner la production écrite à vos élèves, avez-vous déjà eu recours à des outils numériques comme" in c]
                    
                    if cols_tools:
                        tool_stats = []
                        tool_details = []

                        for col in cols_tools:
                            match = re.search(r'\[(.*?)\]', col)
                            tool_name_short = match.group(1) if match else col
                            tool_name_full = col.split("comme :")[-1].strip() if "comme :" in col else col

                            if "[Autre]" in col:
                                subset = df_filtered[col].dropna()
                                count = subset[subset.astype(str).str.strip() != ""].shape[0]
                            else:
                                count = df_filtered[df_filtered[col] == 'Oui'].shape[0]
                            
                            total = df_filtered.shape[0]
                            pct = (count / total * 100) if total > 0 else 0
                            
                            tool_stats.append({"Outil": tool_name_short, "Utilisateurs": count, "Pourcentage": pct})
                            
                            if "Aucun outil" not in tool_name_short:
                                tool_details.append({"Nom de l'outil": tool_name_short, "Nom complet dans le questionnaire": tool_name_full})
                        
                        df_tools = pd.DataFrame(tool_stats).sort_values("Utilisateurs", ascending=False)
                        
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            st.dataframe(df_tools.style.format({"Pourcentage": "{:.1f}%"}), use_container_width=True, hide_index=True)
                        with c2:
                            fig_global = px.bar(df_tools, x="Utilisateurs", y="Outil", orientation='h', text="Utilisateurs", title="Nombre d'utilisateurs par outil", color="Utilisateurs")
                            st.plotly_chart(fig_global, use_container_width=True)

                        # Tableau des noms d'outils
                        st.markdown("#### 📋 Liste détaillée des outils recensés")
                        with st.expander("Voir les noms complets des outils", expanded=False):
                            st.table(pd.DataFrame(tool_details))

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

                # --- ONGLET 2 : Corrélation ---
                with tab2:
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

                # --- ONGLET 4 : TYPOLOGIE D'USAGER ---
                with tab4:
                    st.subheader("👥 Typologie d'Usager & Ancienneté")
                    
                    st.info("""
                    ### 🎯 Objectifs de cette analyse
                    Nous ne nous contentons pas d'une moyenne générale. Nous cherchons à créer des **"Profils Types"** d'enseignants face au numérique pour mieux comprendre les besoins de formation.
                    """)

                    with st.expander("📘 Comprendre la méthode de calcul et les profils", expanded=True):
                        st.markdown("""
                        **1. Comment avons-nous calculé ces profils ?**
                        Nous nous sommes basés sur le **score obtenu à la Partie 4** du questionnaire ("Outils numériques"), noté sur **24 points**.
                        Nous avons découpé la population en 3 tiers statistiques :
                        
                        * 🔴 **1. Déconnectés (Score < 8/24) :** Enseignants déclarant peu ou pas d'usage du numérique.
                        * 🟡 **2. Utilisateurs Basiques (Score 8 à 15/24) :** Enseignants utilisant le numérique ponctuellement.
                        * 🟢 **3. Experts Numériques (Score > 16/24) :** Enseignants intégrant le numérique comme levier d'apprentissage.

                        **2. Pourquoi croiser avec l'ancienneté ?**
                        Pour vérifier si les "Néo-titulaires" sont réellement plus experts que les "Seniors", contrairement aux idées reçues.
                        """)
                    
                    st.divider()

                    if 'total_partie_4' in df_filtered.columns:
                        df_typ = df_filtered.copy()
                        
                        def get_typology(score):
                            if score < 8: return "1. Déconnectés (Faible)"
                            elif score < 16: return "2. Utilisateurs Basiques (Moyen)"
                            else: return "3. Experts Numériques (Élevé)"
                            
                        df_typ['Profil_Num'] = df_typ['total_partie_4'].apply(get_typology)
                        
                        col_anc_local = next((c for c in df.columns if "combien" in c.lower() and "années" in c.lower() and "enseignez" in c.lower()), None)
                        
                        if col_anc_local:
                            def local_cat_anc(val):
                                val_str = str(val).lower().strip()
                                if pd.isna(val) or val_str in ["", "nan"]: return "Non concerné"
                                if "+10" in val_str or "plus de 10" in val_str: return "3. Seniors (+10 ans)"
                                import re
                                nums = re.findall(r'\d+', val_str)
                                if nums:
                                    years = int(nums[0])
                                    if years <= 3: return "1. Néo-titulaires (0-3 ans)"
                                    elif years <= 10: return "2. Juniors (4-10 ans)"
                                    else: return "3. Seniors (+10 ans)"
                                return "Non concerné"

                            df_typ['Tranche_Anc'] = df_typ[col_anc_local].apply(local_cat_anc)
                            df_typ_clean = df_typ[df_typ['Tranche_Anc'] != "Non concerné"]
                            
                            if not df_typ_clean.empty:
                                cross_tab = pd.crosstab(df_typ_clean['Tranche_Anc'], df_typ_clean['Profil_Num'], normalize='index') * 100
                                st.markdown("#### 🧩 Qui sont les experts ? (Analyse Croisée)")
                                fig_heat_typ = px.imshow(
                                    cross_tab, 
                                    text_auto=".1f", 
                                    color_continuous_scale="Blues",
                                    title="Profil Numérique selon l'Ancienneté (% par ligne)",
                                    labels=dict(x="Profil Numérique", y="Ancienneté", color="Pourcentage")
                                )
                                st.plotly_chart(fig_heat_typ, use_container_width=True)
                                st.info("💡 **Lecture de la Heatmap :** Chaque ligne totalise 100%. Regardez la colonne de droite ('3. Experts'). Si la case est bleu foncé chez les Seniors, cela signifie qu'ils sont proportionnellement très nombreux à être experts.")
                            else:
                                st.warning("Pas assez de données d'ancienneté valides pour le graphique.")
                        else:
                            st.warning("Colonne Ancienneté introuvable pour le croisement.")
                            
                        st.divider()
                        st.subheader("Répartition globale des profils")
                        counts_typ = df_typ['Profil_Num'].value_counts().sort_index()
                        color_map_typ = {
                            "1. Déconnectés (Faible)": "#e74c3c",  
                            "2. Utilisateurs Basiques (Moyen)": "#f1c40f", 
                            "3. Experts Numériques (Élevé)": "#2ecc71" 
                        }
                        fig_pie_typ = px.pie(
                            values=counts_typ.values, 
                            names=counts_typ.index, 
                            hole=0.5, 
                            title="Poids des groupes dans la population totale",
                            color=counts_typ.index,
                            color_discrete_map=color_map_typ
                        )
                        st.plotly_chart(fig_pie_typ, use_container_width=True)
                    else:
                        st.error("Colonne 'total_partie_4' manquante. Impossible de créer la typologie.")

                # --- ONGLET 6 : FRACTURE NUMÉRIQUE ---
                with tab6:
                    st.subheader("🗺️ Fracture Numérique Territoriale")
                    
                    st.info("""
                    **ℹ️ Comment interpréter ces données ?**
                    Cette analyse vise à détecter d'éventuelles inégalités territoriales dans la maîtrise du numérique.
                    
                    * **Important :** La question sur la "Zone géographique" est à **choix multiples**. Un enseignant peut exercer en "Zone rurale" ET en "REP".
                    * **L'objectif :** Vérifier si les scores de compétence numérique varient significativement selon le contexte d'exercice.
                    """)
                    
                    st.markdown("Y a-t-il une inégalité d'accès ou de compétence selon le territoire ?")
                    
                    if 'total_partie_4' in df_filtered.columns:
                        score_col = 'total_partie_4'
                        cols_zone = [c for c in df.columns if "zone géographique" in str(c).lower() and "[" in str(c)]
                        
                        if cols_zone:
                            zone_scores = []
                            for col in cols_zone:
                                zone_name = re.search(r'\[(.*?)\]', col).group(1).replace(',', '').strip()
                                sub_zone = df_filtered[df_filtered[col].notna() & (df_filtered[col] != "Non") & (df_filtered[col] != "False")]
                                if len(sub_zone) > 0:
                                    avg_score = sub_zone[score_col].mean()
                                    zone_scores.append({"Zone": zone_name, "Score Moyen (Numérique)": avg_score, "Effectif": len(sub_zone)})
                            
                            if zone_scores:
                                df_zone_res = pd.DataFrame(zone_scores).sort_values("Score Moyen (Numérique)", ascending=False)
                                st.markdown("#### 🏘️ Score Moyen par Type de Zone")
                                fig_zone = px.bar(
                                    df_zone_res, 
                                    x="Score Moyen (Numérique)", 
                                    y="Zone", 
                                    orientation='h', 
                                    text_auto=".2f",
                                    color="Score Moyen (Numérique)",
                                    title="Compétence Numérique (Partie 4) selon la zone d'exercice"
                                )
                                fig_zone.update_layout(xaxis_range=[0, 24]) 
                                st.plotly_chart(fig_zone, use_container_width=True)
                            else:
                                st.info("Aucune donnée de zone trouvée.")
                        
                        st.divider()
                        st.markdown("#### 🎓 Score Moyen par Académie")
                        st.info("""
                        **Pourquoi cartographier les résultats ?**
                        Cela permet de repérer des "Académies pilotes" où la compétence numérique est plus élevée.
                        *Cliquez sur les marqueurs pour voir le détail (Score moyen et Effectif).*
                        """)
                        
                        if col_academie:
                            acad_stats = df_filtered.groupby('acad_key')[score_col].agg(['mean', 'count']).reset_index()
                            acad_stats.columns = ['acad_key', 'Score_Moyen', 'Nombre_Personnes']
                            
                            m_num = folium.Map(location=[46.5, 2.0], zoom_start=6, tiles="cartodbpositron")
                            
                            for _, row in acad_stats.iterrows():
                                acad_key = row['acad_key']
                                score = row['Score_Moyen']
                                count = int(row['Nombre_Personnes'])
                                
                                if acad_key in INFO_RECTORATS:
                                    info = INFO_RECTORATS[acad_key]
                                    color = "green" if score > 16 else ("orange" if score > 12 else "red")
                                    
                                    folium.Marker(
                                        location=info["coord"],
                                        popup=f"<b>{info['nom']}</b><br>Score Moyen: {score:.2f}/24<br>Effectif: {count} personnes",
                                        icon=folium.Icon(color=color, icon="laptop", prefix="fa")
                                    ).add_to(m_num)
                            
                            st_folium(m_num, width="100%", height=500)
                            st.caption("🟢 Vert : Score > 16/24 | 🟠 Orange : Score > 12/24 | 🔴 Rouge : Score < 12/24")
                    else:
                        st.error("Score numérique (Partie 4) introuvable pour l'analyse territoriale.")

                # --- ONGLET 7 (NOUVEAU) : HYPOTHÈSE RÉVISION ---
                with tab7:
                    st.subheader("✍️ L'Hypothèse 'Révision'")
                    
                    # --- EXPLICATIONS PÉDAGOGIQUES ---
                    st.info("""
                    ### 🧐 De quoi s'agit-il ?
                    La recherche en sciences cognitives montre que le numérique est particulièrement efficace pour **alléger le coût cognitif** de la révision de texte.
                    
                    **L'hypothèse testée :**
                    Les enseignants qui utilisent beaucoup d'outils numériques (profil "Fort Usage") devraient avoir une meilleure compréhension théorique des processus de **Révision** (relecture, correction) que des processus de **Planification**.
                    
                    **Comment lire le graphique ?**
                    Si la barre des "Gros utilisateurs" est significativement plus haute pour la "Révision", cela valide l'hypothèse que l'outil façonne la compétence.
                    """)
                    # ---------------------------------
                    
                    cols_revision = [c for c in df.columns if "score" in c.lower() and ("2.8" in c or "2.9" in c)]
                    cols_planif = [c for c in df.columns if "score" in c.lower() and ("2.4" in c or "2.5" in c)]
                    
                    if cols_revision and cols_planif:
                        df_rev = df_filtered.copy()
                        
                        def get_div_score(row):
                            cnt = 0
                            if cols_tools:
                                for c in cols_tools:
                                    if "Aucun outil" in c: continue
                                    v = row[c]
                                    if "[Autre]" in c:
                                        if pd.notna(v) and str(v).strip()!="": cnt+=1
                                    elif v=="Oui": cnt+=1
                            return cnt
                        
                        df_rev['Indice_Div'] = df_rev.apply(get_div_score, axis=1)
                        df_rev['Profil_Usage'] = df_rev['Indice_Div'].apply(lambda x: "Fort Usage (>2 outils)" if x > 2 else "Faible Usage (0-2 outils)")
                        
                        df_rev['Score_Revision_Moyen'] = df_rev[cols_revision].mean(axis=1)
                        df_rev['Score_Planif_Moyen'] = df_rev[cols_planif].mean(axis=1)
                        
                        res_rev = df_rev.groupby('Profil_Usage')[['Score_Revision_Moyen', 'Score_Planif_Moyen']].mean().reset_index()
                        res_melt = res_rev.melt(id_vars='Profil_Usage', var_name='Type_Tache', value_name='Note_Moyenne')
                        res_melt['Type_Tache'] = res_melt['Type_Tache'].replace({'Score_Revision_Moyen': 'Processus Révision', 'Score_Planif_Moyen': 'Processus Planification'})
                        
                        fig_hyp = px.bar(
                            res_melt, 
                            x='Type_Tache', 
                            y='Note_Moyenne', 
                            color='Profil_Usage', 
                            barmode='group',
                            title="Comparaison : Le numérique aide-t-il plus pour la Révision ?",
                            text_auto='.2f'
                        )
                        st.plotly_chart(fig_hyp, use_container_width=True)
                    else:
                        st.warning("Impossible de trouver les questions scores 2.4, 2.5, 2.8 ou 2.9.")

                # --- ONGLET 8 (NOUVEAU) : EFFICACITÉ FORMATION ---
                with tab8:
                    st.subheader("🎓 Efficacité de la Formation (ROI)")
                    
                    # --- EXPLICATIONS PÉDAGOGIQUES ---
                    st.info("""
                    ### 📊 Retour sur Investissement (ROI) de la Formation
                    Cette analyse vise à mesurer l'impact concret des formations suivies par les enseignants.
                    
                    **La question clé :**
                    Les formations institutionnelles ou personnelles se traduisent-elles par une **diversification réelle des usages** en classe ?
                    
                    **Comment lire le graphique ?**
                    * Nous comparons deux groupes : ceux qui ont déclaré avoir été formés au numérique vs ceux qui ne l'ont pas été.
                    * La "Boîte à moustaches" montre la dispersion du nombre d'outils utilisés. Si la boîte des "Formés" est nettement plus haute, la formation est efficace.
                    """)
                    # ---------------------------------
                    
                    col_form_num = next((c for c in df.columns if "formation" in c.lower() and "numérique" in c.lower() and "suivi" in c.lower()), None)
                    
                    if col_form_num:
                        df_roi = df_filtered.copy()
                        if 'Indice_Div' not in df_roi.columns:
                             df_roi['Indice_Div'] = df_roi.apply(get_div_score, axis=1)
                        
                        def is_formed(val):
                            s = str(val).lower()
                            if "non" in s or "nan" in s or s=="" or s=="0": return "Non Formé"
                            return "Formé"
                            
                        df_roi['Statut_Formation'] = df_roi[col_form_num].apply(is_formed)
                        
                        fig_box_roi = px.box(
                            df_roi, 
                            x="Statut_Formation", 
                            y="Indice_Div", 
                            color="Statut_Formation",
                            title="Impact de la formation sur la diversité des outils utilisés",
                            labels={"Indice_Div": "Nombre d'outils différents (Indice)"},
                            points="all"
                        )
                        st.plotly_chart(fig_box_roi, use_container_width=True)
                        
                        from scipy import stats
                        grp_forme = df_roi[df_roi['Statut_Formation']=="Formé"]['Indice_Div']
                        grp_non = df_roi[df_roi['Statut_Formation']=="Non Formé"]['Indice_Div']
                        
                        if len(grp_forme)>1 and len(grp_non)>1:
                            u_stat, p_val = stats.mannwhitneyu(grp_forme, grp_non)
                            if p_val < 0.05:
                                st.success(f"✅ **Impact Significatif** (p={p_val:.4f}). La formation augmente bien la diversité des usages.")
                            else:
                                st.warning(f"❌ **Pas d'impact significatif** (p={p_val:.4f}). La formation ne semble pas changer le nombre d'outils utilisés.")
                    else:
                        st.error("Colonne sur la formation numérique introuvable.")

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
                        st.subheader("4. 🧠 Analyse Détaillée par Compétence (Focus)")
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
                        st.subheader("5. 🎓 Trajectoire : De la Formation Initiale à l'Expertise")
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
                        
            # =============================================================================
            # PAGE : TESTS STATISTIQUES AVANCÉS & MODÉLISATION (VERSION ULTIME)
            # =============================================================================
            elif page == "📈 Tests Statistiques":
                st.title("📈 Analyses Statistiques & Modélisation")
                st.markdown("---")

                # --- NAVIGATION : MENU À ONGLETS PRO ---
                # --- NAVIGATION : MENU À ONGLETS PRO ---
                tabs = st.tabs([
                    "📏 Variabilité & Dispersion", 
                    "🔍 Tests de Normalité", 
                    "📊 Inférence Statistique", 
                    "🔗 Mesures d'Association", 
                    "📐 Validité Psychométrique", 
                    "🔮 Modélisation Multivariée", 
                    "💬 Traitement Sémantique (NLP)"
                ])

                # ONGLET 0 : ÉCART TYPE ET CV (DÉPLACÉ ICI)
                # =========================================================================
                with tabs[0]:
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


                # ONGLET 1 : EXPLORATION (NORMALITÉ)
                # =========================================================================
                with tabs[1]:
                    st.header("1️⃣ Analyse de Distribution (Normalité)")
                    
                    # --- INTRODUCTION PÉDAGOGIQUE (MISE À JOUR) ---
                    st.info("""
                    ### 🧐 De quoi s'agit-il ?
                    Avant de comparer les notes, nous regardons la "forme" des données pour savoir si elles suivent une courbe en cloche (Loi Normale).
                    
                    **🤖 Choix Automatique du Test :**
                    L'application sélectionne le test mathématique le plus fiable selon le volume de données :
                    
                    * **Moins de 50 personnes** $\\rightarrow$ **Shapiro-Wilk** (Le microscope 🔬).
                        * *Pourquoi ?* Il est très précis pour détecter les anomalies dans les petits groupes.
                    * **Plus de 50 personnes** $\\rightarrow$ **Kolmogorov-Smirnov** (La vue d'ensemble 🔭).
                        * *Pourquoi ?* Il est plus robuste et évite de rejeter la normalité pour des détails insignifiants sur les grands volumes (comme le Total).
                    """)
                    
                    st.success("**❓ Question :** La répartition des scores est-elle équilibrée (Loi Normale) ?")
                    st.divider()

                    # --- SÉLECTEURS ---
                    c1, c2 = st.columns(2)
                    
                    # 1. Choix du Groupe (Avec Total)
                    with c1:
                        options_with_total = ["🌍 Total (Tous les participants)"] + list(all_options)
                        target_group = st.selectbox("1. Choisir un groupe à analyser :", options=options_with_total, key="norm_sel")

                    # 2. Choix de la Variable
                    with c2:
                        candidates = [
                            "Total_par_repondeur", 
                            "total_partie_2", "Total_partie_2",
                            "total_partie_3", "Total_partie_3",
                            "total_partie_4", "Total_partie_4",
                            "total_partie_5", "Total_partie_5", "total _partie_5"
                        ]
                        valid_cols = [c for c in candidates if c in df.columns]
                        
                        def get_nice_name(c):
                            if c == "Total_par_repondeur": return "🏆 Score Global"
                            if 'PARTIES_INFO' in globals() and c in PARTIES_INFO: return f"📂 {PARTIES_INFO[c]['short']}"
                            # Fallback manuel
                            c_lower = c.lower().replace(" ", "")
                            if "partie_2" in c_lower: return "📂 P2. Outils numériques"
                            if "partie_3" in c_lower: return "📂 P3. Usages pédagogiques"
                            if "partie_4" in c_lower: return "📂 P4. Compétences"
                            if "partie_5" in c_lower: return "📂 P5. Évaluation"
                            return c

                        col_map = {get_nice_name(c): c for c in valid_cols}
                        
                        if col_map:
                            sel_label = st.selectbox("2. Choisir la variable (Score) :", options=list(col_map.keys()))
                            col_norm = col_map[sel_label]
                        else:
                            col_norm = None
                            st.error("❌ Aucune colonne de score trouvée.")
                    
                    # --- EXÉCUTION ---
                    if st.button("🚀 Lancer l'analyse intelligente"):
                        if col_norm:
                            # LOGIQUE DE FILTRAGE
                            if "Total" in target_group:
                                data_norm = df[col_norm].dropna()
                                clean_grp = "Tous les participants"
                            else:
                                clean_grp = target_group.replace("🟩 ", "")
                                mask_grp = get_mask_for_status(clean_grp, df)
                                data_norm = df[mask_grp][col_norm].dropna()
                            
                            N = len(data_norm)
                            
                            if N > 3:
                                # --- INTELLIGENCE ARTIFICIELLE STATISTIQUE ---
                                # Choix automatique du test selon la taille (N)
                                if N < 50:
                                    test_name = "Shapiro-Wilk (Microscope 🔬)"
                                    stat_val, p_val = stats.shapiro(data_norm)
                                    msg_size = "Petit groupe (N < 50)"
                                else:
                                    test_name = "Kolmogorov-Smirnov (Vue d'ensemble 🔭)"
                                    # On compare les données à une loi normale théorique de même moyenne et écart-type
                                    stat_val, p_val = stats.kstest(data_norm, 'norm', args=(data_norm.mean(), data_norm.std()))
                                    msg_size = "Grand volume (N > 50)"

                                # Résultats Chiffrés
                                st.markdown(f"### 📊 Résultats : **{test_name}**")
                                st.caption(f"Analyse basée sur : **{msg_size}** avec {N} participants.")
                                
                                k1, k2 = st.columns(2)
                                k1.metric("Statistique", f"{stat_val:.3f}")
                                k2.metric("p-value", f"{p_val:.5f}")
                                
                                # Interprétation
                                if p_val < 0.05:
                                    st.warning(f"⚠️ **Distribution NON Normale** (p < 0.05).")
                                    st.write("La courbe s'éloigne significativement de la théorie. Pour les comparaisons, privilégiez les tests robustes (Kruskal-Wallis).")
                                else:
                                    st.success("✅ **Distribution Normale** (p > 0.05). La courbe est bien en forme de cloche.")
                                
                                # --- GRAPHIQUE ---
                                st.markdown("---")
                                st.subheader(f"Zoom sur : {sel_label}")
                                
                                fig_hist_norm = px.histogram(
                                    data_norm, 
                                    x=col_norm, 
                                    nbins=20, 
                                    histnorm='probability density',
                                    color_discrete_sequence=['#85C1E9'], 
                                    opacity=0.7 
                                )
                                
                                x_range = np.linspace(data_norm.min(), data_norm.max(), 100)
                                if data_norm.std() > 0:
                                    y_normal = stats.norm.pdf(x_range, data_norm.mean(), data_norm.std())
                                    fig_hist_norm.add_trace(go.Scatter(
                                        x=x_range, y=y_normal, 
                                        mode='lines', 
                                        line=dict(color='#E74C3C', width=3), 
                                        name='Modèle Théorique (Gauss)'
                                    ))
                                
                                fig_hist_norm.update_layout(
                                    title=f"Répartition des notes - {clean_grp}",
                                    xaxis_title="Note obtenue",
                                    yaxis_title="Fréquence",
                                    plot_bgcolor="white",
                                    bargap=0.05,
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                                )
                                fig_hist_norm.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
                                fig_hist_norm.update_xaxes(showgrid=False, linecolor='black')
                                
                                fig_hist_norm.data[0].name = 'Réalité (Vos données)'
                                fig_hist_norm.data[0].showlegend = True
                                
                                st.plotly_chart(fig_hist_norm, use_container_width=True)
                                

                                
                                
                            else:
                                st.error("⚠️ Pas assez de données pour ce groupe (N > 3 requis).")
                        else:
                            st.error("Variable invalide.")
                    
                # =========================================================================
                # ONGLET 2 : COMPARAISONS (T-TEST, MANN-WHITNEY, ANOVA, KRUSKAL)
                # =========================================================================
                with tabs[2]:
                    st.header("2️⃣ Comparaisons de Moyennes & Rangs")
                    
                    # --- BLOC D'EXPLICATION (ENCADRÉ BLEU) ---
                    st.info("""
                    ### 🧐 De quoi s'agit-il ?
                    Nous cherchons à savoir si les différences de notes entre les groupes sont réelles ou dues au hasard.
                    
                    * **Approche Paramétrique (T-Test / ANOVA) :** Compare les **Moyennes**. *Idéal si la distribution est Normale (voir Onglet 1).*
                    * **Approche Non-Paramétrique (Mann-Whitney / Kruskal-Wallis) :** Compare les **Rangs** (Médianes). *Idéal si la distribution n'est pas normale.*
                    """)

                    # --- LA QUESTION (ENCADRÉ VERT) ---
                    st.success("""
                    **❓ La Question posée :** "Le fait d'appartenir au groupe A ou B modifie-t-il significativement la performance ?"
                    """)
                    
                    st.divider()

                    # --- DÉBUT DES SOUS-ONGLETS ---
                    subtab_ttest, subtab_anova = st.tabs(["🅰️ Comparer 2 groupes (Duel)", "🅱️ Comparer + de 2 groupes (Multi)"])

                    # =====================================================================
                    # A. COMPARAISON 2 GROUPES (T-TEST & MANN-WHITNEY)
                    # =====================================================================
                    # =====================================================================
                    # A. COMPARAISON 2 GROUPES (T-TEST & MANN-WHITNEY)
                    # =====================================================================
                    with subtab_ttest:
                        st.subheader("Duel entre 2 groupes")
                        
                        # --- GUIDE DE CHOIX ---
                        st.info("""
                        **💡 Guide : Comment comparer 2 groupes ?**
                        Ici, on oppose deux équipes pour voir qui a la meilleure performance.
                        
                        * ✅ **Exemples valides :** Sexe (H/F), Statut (Titulaire/Stagiaire), Formation (Initiale/Continue).
                        * ❌ **Attention :** Ne comparez pas un groupe avec lui-même (ex: Hommes vs Hommes).
                        """)

                        # --- NOUVEAU SÉLECTEUR (Affichage Professionnel) ---
                        # --- NOUVEAU SÉLECTEUR (Affichage Professionnel) ---
                        candidates_comp = []
                        if total_cols:
                            candidates_comp.append(total_cols[0])
                            
                        # 🛠️ CORRECTION : On enlève les espaces pour chercher la colonne
                        for col in df.columns:
                            col_clean = col.lower().replace(" ", "")
                            if "total_partie" in col_clean and col not in candidates_comp:
                                candidates_comp.append(col)
                                
                        def get_nice_name_comp(c):
                            if total_cols and c == total_cols[0]: return "🏆 Score Global"
                            
                            # On sécurise aussi ici en enlevant les espaces
                            c_clean = c.lower().replace(" ", "")
                            
                            if "partie_2" in c_clean: return "📂 P2. Fonctionnement"
                            if "partie_3" in c_clean: return "📂 P3. Interventions"
                            if "partie_4" in c_clean: return "📂 P4. Outils Num."
                            if "partie_5" in c_clean: return "📂 P5. Évaluation"
                            
                            return c


                        # -------------------------------------------------------------
                        # Création du dictionnaire { "Beau Nom" : "vrai_nom_de_colonne" }
                        metric_options = {get_nice_name_comp(c): c for c in candidates_comp}
                        
                        # Affichage du menu déroulant avec les beaux noms
                        sel_label_comp = st.selectbox("Variable à comparer (Score) :", options=list(metric_options.keys()), key="ttest_met_v2")
                        
                        # Récupération de la vraie colonne en arrière-plan pour les calculs
                        sel_metric = metric_options[sel_label_comp]
                        # -------------------------------------------------------------

                        c1, c2 = st.columns(2)
                        with c1: group_A = st.selectbox("Groupe A (Réf)", options=all_options, index=0, key="grp_a")
                        with c2: group_B = st.selectbox("Groupe B (Comp)", options=all_options, index=1 if len(all_options)>1 else 0, key="grp_b")

                        if st.button("🚀 Lancer le Duel (Welch & Mann-Whitney)"):
                            # Préparation des données
                            data_A = df[get_mask_for_status(group_A.replace("🟩 ", ""), df)][sel_metric].dropna()
                            data_B = df[get_mask_for_status(group_B.replace("🟩 ", ""), df)][sel_metric].dropna()
                            
                            if len(data_A) > 1 and len(data_B) > 1:
                                # CALCULS
                                # 1. T-TEST (WELCH)
                                t_stat, p_ttest = stats.ttest_ind(data_A, data_B, equal_var=False)
                                
                                # 2. MANN-WHITNEY U (NON-PARAMÉTRIQUE)
                                u_stat, p_mann = stats.mannwhitneyu(data_A, data_B, alternative='two-sided')
                                
                                # Calcul Cohen's d (Taille d'effet)
                                pooled_std = np.sqrt(((len(data_A)-1)*data_A.std()**2 + (len(data_B)-1)*data_B.std()**2) / (len(data_A)+len(data_B)-2))
                                cohen_d = (data_A.mean() - data_B.mean()) / pooled_std if pooled_std != 0 else 0
                                
                                # --- AFFICHAGE RÉSULTATS ---
                                st.markdown("#### 📊 Résultats Comparés")
                                
                                col_res1, col_res2 = st.columns(2)
                                
                                # Colonne Paramétrique (Bleue)
                                with col_res1:
                                    st.info("🟦 **Test t de Welch (Paramétrique)**")
                                    st.caption("Basé sur les MOYENNES")
                                    st.metric("p-value", f"{p_ttest:.5f}")
                                    if p_ttest < 0.05: st.success("✅ Différence Significative")
                                    else: st.warning("❌ Pas de différence")
                                    st.write(f"**Taille d'effet (d) : {abs(cohen_d):.2f}**")

                                # Colonne Non-Paramétrique (Orange)
                                with col_res2:
                                    st.info("🟧 **Mann-Whitney U (Non-Paramétrique)**")
                                    st.caption("Basé sur les RANGS (Classement)")
                                    st.metric("p-value", f"{p_mann:.5f}")
                                    if p_mann < 0.05: st.success("✅ Différence Significative")
                                    else: st.warning("❌ Pas de différence")
                                    st.caption("À privilégier si vos données ne sont pas normales.")

                                st.markdown("---")
                                
                                # --- EXPLICATION PÉDAGOGIQUE (AJOUTÉE ICI) ---
                                with st.expander("🎓 Comprendre : Comment ces deux tests calculent-ils ?"):
                                    st.markdown("""
                                    ### 1. 🟦 "Compare les Moyennes" (Test T de Welch)
                                    *C'est la méthode classique.*
                                    
                                    * **Comment il calcule ?** Il compare la note moyenne du Groupe A (ex: 12/20) et celle du Groupe B (ex: 14/20) en tenant compte de l'écart-type (la dispersion).
                                    * **L'intuition :** Si l'écart entre 12 et 14 est grand et que les notes sont peu dispersées, il dit "C'est significatif".
                                    * **Image mentale :** Imaginez deux tas de sable. Le test vérifie si le sommet du tas A est vraiment loin du sommet du tas B.
                                    * **Faiblesse :** Si un enseignant a une note extrême (ex: 0 ou 100 alors que les autres sont à 50), la moyenne bouge énormément et le test peut se tromper.
                                    
                                    ---
                                    
                                    ### 2. 🟧 "Compare les Rangs" (Test de Mann-Whitney)
                                    *C'est la méthode "tout-terrain" (Robuste).*
                                    
                                    * **Comment il calcule ?** Il oublie les notes exactes. Il mélange tout le monde (Groupe A et B) et les classe du score le plus faible au plus fort (1er, 2ème, 3ème...).
                                    * **L'intuition :** Il regarde si les membres du Groupe A arrivent souvent en tête du classement par rapport au Groupe B.
                                    * **Image mentale :** C'est comme une course à pied. On se fiche du temps exact (chrono), on regarde juste qui est arrivé avant qui sur le podium.
                                    * **Force (Robuste) :** Si un répondant a mis une note aberrante, il sera juste classé "1er" ou "Dernier". Ça ne fausse pas tout le calcul.
                                    """)

                                st.markdown("---")
                                
                                # Visualisation Densité
                                st.subheader("Visualisation des distributions")
                                
                                fig_dist = go.Figure()
                                for dat, name, col in [(data_A, group_A, '#3498db'), (data_B, group_B, '#e74c3c')]:
                                    if len(dat) > 1 and dat.std() > 0:
                                        x_range = np.linspace(min(dat.min(), data_B.min()), max(dat.max(), data_B.max()), 200)
                                        try:
                                            kde = stats.gaussian_kde(dat)
                                            fig_dist.add_trace(go.Scatter(x=x_range, y=kde(x_range), name=name, fill='tozeroy', line_color=col))
                                        except:
                                            pass # Erreur si données constantes
                                
                                st.plotly_chart(fig_dist, use_container_width=True)
                                

                            else:
                                st.error("Données insuffisantes pour comparer ces groupes.")

                    # =====================================================================
                    # B. COMPARAISON >2 GROUPES (ANOVA & KRUSKAL)
                    # =====================================================================
                    with subtab_anova:
                        st.subheader("Comparaison Multi-Groupes")
                        
                        # --- GUIDE PÉDAGOGIQUE (SÉLECTION) ---
                        st.info("""
                        **💡 Guide : Que mettre dans 'Facteur de groupe' ?**
                        C'est le critère qui divise vos participants en **3 équipes ou plus**.
                        
                        * ✅ **Bons choix :** Une variable catégorielle (Texte).
                            * *Ex : Ancienneté (Débutant / Confirmé / Expert)*
                            * *Ex : Niveau (CP / CE1 / CM2 / ...)*
                            * *Ex : Zone (Rural / Urbain / REP)*
                        * ❌ **À éviter ici :**
                            * Les variables à 2 choix (H/F) $\rightarrow$ Utilisez l'onglet précédent "Duel".
                            * Les scores chiffrés (Total_Score) $\rightarrow$ Utilisez l'onglet "Corrélations".
                        """)
                        
                        if total_cols:
                            target_col = total_cols[0]
                            avail_cols = [c for c in df.columns if c != target_col]
                            
                            # --- FILTRAGE LOCAL AJOUTÉ (Sans modifier le reste) ---
                            c_filt1, c_filt2 = st.columns([1, 2])
                            filter_pop = c_filt1.selectbox("Qui inclure ?", ["Tout le monde"] + list(all_options), key="anova_filter_local")
                            
                            if filter_pop == "Tout le monde":
                                df_filtered = df.copy()
                            else:
                                clean_pop = filter_pop.replace("🟩 ", "")
                                mask_pop = get_mask_for_status(clean_pop, df)
                                df_filtered = df[mask_pop].copy()
                            # ----------------------------------------------------

                            # Essai de détection auto de "ancienneté"
                            def_idx = next((i for i, c in enumerate(avail_cols) if "ancien" in c.lower()), 0)
                            
                            col_group = st.selectbox("Facteur de groupe (Variable explicative) :", avail_cols, index=def_idx, key="anova_grp")
                            
                            # Préparation Données (AVEC df_filtered maintenant)
                            df_anova = df_filtered.dropna(subset=[col_group, target_col]).copy()
                            df_anova[col_group] = df_anova[col_group].astype(str)
                            grps = [df_anova[df_anova[col_group] == g][target_col] for g in sorted(df_anova[col_group].unique())]
                            
                            # VÉRIFICATION : A-t-on assez de groupes ?
                            if len(grps) > 2 and all(len(g) > 1 for g in grps):
                                
                                # --- 1. TEST DE LEVENE (HOMOGÉNÉITÉ) ---
                                st.markdown("##### 1. Vérification des Variances (Levene)")
                                try:
                                    stat_levene, p_levene = stats.levene(*grps)
                                    if p_levene > 0.05:
                                        st.success(f"✅ Variances homogènes (p={p_levene:.3f}). L'ANOVA classique est valide.")
                                    else:
                                        st.warning(f"⚠️ Variances différentes (p={p_levene:.3f}). Privilégiez Welch ou Kruskal-Wallis ci-dessous.")
                                except:
                                    st.info("Levene non calculable (Variance nulle dans un groupe ?).")

                                # --- 2. ANOVA (PARAMÉTRIQUE) ---
                                f_stat, p_anova = stats.f_oneway(*grps)
                                
                                # --- 3. KRUSKAL-WALLIS (NON-PARAMÉTRIQUE) ---
                                try: k_stat, p_kruskal = stats.kruskal(*grps)
                                except: p_kruskal = 1.0

                                # --- AFFICHAGE RÉSULTATS ---
                                st.markdown("#### 📊 Résultats Comparés")
                                c1, c2 = st.columns(2)
                                
                                with c1:
                                    st.info("🟦 **ANOVA (Moyennes)**")
                                    st.metric("p-value", f"{p_anova:.5f}")
                                    if p_anova < 0.05: st.success("✅ Différence détectée")
                                    else: st.warning("❌ Pas d'effet significatif")
                                
                                with c2:
                                    st.info("🟧 **Kruskal-Wallis (Rangs)**")
                                    st.metric("p-value", f"{p_kruskal:.5f}")
                                    if p_kruskal < 0.05: st.success("✅ Différence détectée")
                                    else: st.warning("❌ Pas d'effet significatif")

                                st.markdown("---")

                                # --- EXPLICATION PÉDAGOGIQUE (NOUVEAU BLOC AJOUTÉ) ---
                                with st.expander("🎓 Comprendre : Comment analyser ces 3 étapes ?"):
                                    st.markdown("""
                                    Pour comparer 3 groupes ou plus (ex: *M1 vs M2 vs Titulaires*), l'analyse se fait en étapes :

                                    ### 1. Le Test de Levene (Le Vigile) 👮‍♂️
                                    * **Son rôle :** Il vérifie si les groupes sont comparables (ont-ils la même dispersion ?).
                                    * **Si Vert (p > 0.05) :** C'est parfait, les groupes sont équilibrés.
                                    * **Si Orange (p < 0.05) :** Les variances sont inégales (un groupe est très homogène, l'autre très dispersé). Dans ce cas, **méfiez-vous de l'ANOVA** (Bleu) et faites confiance à **Kruskal-Wallis** (Orange).

                                    ### 2. ANOVA vs Kruskal-Wallis (Les Juges) ⚖️
                                    Ces deux tests répondent à la question : *"Y a-t-il au moins un groupe différent des autres ?"*
                                    * **🟦 ANOVA (Moyennes) :** Très puissant, mais sensible aux notes extrêmes. Il compare le "Signal" (différence entre les groupes) au "Bruit" (différence interne).
                                    * **🟧 Kruskal-Wallis (Rangs) :** Le "4x4" des statistiques. Il classe tous les enseignants/étudiants du 1er au dernier et regarde si un groupe truste le haut du classement. **C'est le résultat le plus sûr** si vos données ne sont pas parfaitement normales.

                                    ### 3. Le Test de Tukey (L'Enquêteur) 🕵️‍♂️
                                    * **Le problème :** L'ANOVA dit juste "Il y a une différence quelque part", mais ne dit pas où !
                                    * **La solution :** Si l'ANOVA est significative (Verte), le tableau de **Tukey** (plus bas) compare les groupes 2 par 2 pour trouver le coupable : *"C'est le groupe M2 qui est différent des Titulaires."*
                                    """)

                                st.markdown("---")
                                
                                # Boxplot
                                st.subheader("Visualisation par Boîtes à Moustaches")
                                
                                fig_box = px.box(df_anova.sort_values(col_group), x=col_group, y=target_col, color=col_group, points="outliers")
                                st.plotly_chart(fig_box, use_container_width=True)

                                # --- 4. POST-HOC (TUKEY) ---
                                if p_anova < 0.05:
                                    st.divider()
                                    st.subheader("🕵️‍♂️ Analyse Post-Hoc (Test de Tukey)")
                                    st.info("L'ANOVA dit qu'il y a une différence. Tukey nous dit ENTRE QUI.")
                                    
                                    try:
                                        from statsmodels.stats.multicomp import pairwise_tukeyhsd
                                        tukey = pairwise_tukeyhsd(endog=df_anova[target_col], groups=df_anova[col_group], alpha=0.05)
                                        
                                        res_tukey = pd.DataFrame(data=tukey.summary().data[1:], columns=tukey.summary().data[0])
                                        res_tukey = res_tukey.rename(columns={"group1": "Groupe A", "group2": "Groupe B", "p-adj": "p-value", "reject": "Significatif ?"})
                                        
                                        st.dataframe(res_tukey.style.applymap(lambda v: 'background-color: #d4edda' if v else 'background-color: #f8d7da', subset=['Significatif ?']))
                                    except:
                                        st.error("Librairie statsmodels manquante.")

                # =========================================================================
                # ONGLET 3 : ASSOCIATIONS (CORRÉLATIONS & CHI-2)
                with tabs[3]:
                    st.header("3️⃣ Associations & Liens")
                    
                    # --- BLOC D'EXPLICATION (ENCADRÉ BLEU - AJUSTÉ ÉTUDIANTS/ENSEIGNANTS) ---
                    st.info("""
                    ### 🧐 De quoi s'agit-il ?
                    Nous explorons ici les liens statistiques pour voir si les réponses diffèrent selon les groupes.
                    
                    * **Corrélations (Variables Numériques) :**
                        * **Pearson :** Lien linéaire (ex: Plus l'année d'étude est élevée, plus le score de connaissances IA augmente).
                        * **Spearman :** Lien de rang (ex: Est-ce que le niveau de stress évolue dans le même sens que la fréquence d'utilisation ?).
                    * **Chi-2 (Variables Catégorielles - Comparaison de groupes) :**
                        * Permet de voir si **le Statut (Étudiant vs Enseignant)** influence significativement une réponse donnée.
                        * *Exemple : La répartition des réponses "Oui/Non" à une question sur l'éthique est-elle différente chez les profs et les élèves ?*
                    """)

                    # --- LA QUESTION (ENCADRÉ VERT) ---
                    st.success("""
                    **❓ La Question posée :** "Existe-t-il une relation forte et significative entre ces deux variables ?"
                    """)
                    
                    st.divider()

                    # --- FILTRAGE LOCAL AJOUTÉ (Sans modifier le reste) ---
                    st.write("### 1. Population à analyser")
                    c_filt1, c_filt2 = st.columns([1, 2])
                    filter_assoc = c_filt1.selectbox("Qui inclure ?", ["Tout le monde"] + list(all_options), key="corr_filter")
                    
                    if filter_assoc == "Tout le monde":
                        df_corr = df.copy()
                    else:
                        clean_assoc = filter_assoc.replace("🟩 ", "")
                        mask_assoc = get_mask_for_status(clean_assoc, df)
                        df_corr = df[mask_assoc].copy()
                    
                    c_filt2.success(f"📊 Analyse sur **{len(df_corr)}** participants.")
                    st.divider()
                    # ----------------------------------------------------

                    subtab_corr, subtab_chi2 = st.tabs(["🔗 Corrélations (Numérique)", "📊 Chi-2 (Catégoriel)"])
                    
                    # --- CORRELATIONS ---
                    # --- CORRELATIONS ---
                    with subtab_corr:
                        st.subheader("Matrice de Corrélation")
                        
                        # SÉLECTEUR DE MÉTHODE
                        method = st.radio("Méthode de calcul :", ["Pearson (Linéaire)", "Spearman (Rangs/Ordinale)"], horizontal=True)
                        method_code = "pearson" if "Pearson" in method else "spearman"
                        
                        cols_corr = [k for k, v in PARTIES_INFO.items() if k in df_corr.columns]
                        if len(cols_corr) > 1:
                            df_mat = df_corr[cols_corr].dropna()
                            # On renomme les colonnes pour l'affichage
                            df_mat.columns = [PARTIES_INFO[c]['short'] for c in df_mat.columns]
                            
                            # Calcul dynamique de la matrice
                            corr_mat = df_mat.corr(method=method_code).round(2)
                            
                            fig_heat = px.imshow(corr_mat, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1, title=f"Matrice ({method})")
                            st.plotly_chart(fig_heat, use_container_width=True)
                            
                            if "Spearman" in method:
                                st.caption("ℹ️ **Note :** Spearman est recommandé pour les questionnaires (échelles de Likert) car il ne suppose pas une linéarité parfaite.")
                            
                            st.divider()
                            
                            # ==========================================
                            # NOUVEAU BLOC : NUAGE DE POINTS INTERACTIF
                            # ==========================================
                            st.subheader("📈 Visualisation détaillée (Nuage de points)")
                            st.info("Sélectionnez deux domaines pour visualiser leur relation de manière détaillée. La ligne rouge représente la tendance générale.")
                            
                            # Sélecteurs pour l'axe X et Y
                            col_x, col_y = st.columns(2)
                            var_x = col_x.selectbox("Sélectionner pour l'Axe X :", options=df_mat.columns, index=0)
                            var_y = col_y.selectbox("Sélectionner pour l'Axe Y :", options=df_mat.columns, index=1 if len(df_mat.columns)>1 else 0)
                            
                            if var_x and var_y:
                                # Récupération de la valeur de corrélation exacte depuis la matrice
                                corr_value = corr_mat.loc[var_y, var_x]
                                
                                # Création du graphique avec droite de tendance (OLS)
                                fig_scatter = px.scatter(
                                    df_mat, 
                                    x=var_x, 
                                    y=var_y, 
                                    title=f"Relation croisée : {var_x} vs {var_y}",
                                    trendline="ols", # Ajoute automatiquement la ligne de tendance mathématique
                                    trendline_color_override="#e74c3c", # Ligne rouge
                                    opacity=0.6,
                                    color_discrete_sequence=['#3498db']
                                )
                                fig_scatter.update_layout(
                                    xaxis_title=var_x,
                                    yaxis_title=var_y
                                )
                                st.plotly_chart(fig_scatter, use_container_width=True)
                                
                                # Interprétation pédagogique automatique
                                if var_x == var_y:
                                    st.info("💡 Vous comparez la variable avec elle-même. La corrélation est logiquement parfaite (1.0).")
                                elif corr_value > 0.5:
                                    st.success(f"📈 **Forte corrélation positive (r = {corr_value})** : Plus le score '{var_x}' augmente, plus le score '{var_y}' a tendance à augmenter de manière proportionnelle.")
                                elif corr_value < -0.5:
                                    st.error(f"📉 **Forte corrélation négative (r = {corr_value})** : Plus le score '{var_x}' augmente, plus le score '{var_y}' a tendance à chuter.")
                                elif -0.2 <= corr_value <= 0.2:
                                    st.write(f"⚪ **Corrélation très faible (r = {corr_value})** : Les points sont dispersés. Il n'y a pas de lien statistique évident entre ces deux dimensions.")
                                else:
                                    st.warning(f"🟡 **Corrélation modérée (r = {corr_value})** : Il y a bien une petite tendance (visible via la ligne rouge), mais elle n'est pas systématique pour tous les participants.")
                                    
                        else:
                            st.warning("Pas assez de colonnes de scores disponibles pour faire des corrélations.")

                    # --- CHI-2 & CRAMER ---
                    with subtab_chi2:
                        st.subheader("Indépendance (Chi-2)")
                        
                        if col_statut and col_plan:
                            # MODIFICATION ICI : Liste de TOUTES les colonnes sauf le statut lui-même
                            # On exclut la colonne utilisée comme pivot (col_statut) pour ne pas croiser "Statut" avec "Statut"
                            liste_variables_dispo = [c for c in df.columns if c != col_statut]
                            
                            var_col = st.selectbox("Croiser le Statut (Étudiant/Enseignant) avec :", liste_variables_dispo)
                            
                            ct = pd.crosstab(df_corr[col_statut], df_corr[var_col])
                            
                            # Calcul Chi-2
                            chi2, p, dof, ex = stats.chi2_contingency(ct)
                            
                            # Calcul V de Cramer (Taille d'effet)
                            n = ct.sum().sum()
                            min_dim = min(ct.shape) - 1
                            v_cramer = np.sqrt((chi2/n) / min_dim) if min_dim > 0 else 0
                            
                            c1, c2 = st.columns(2)
                            c1.metric("p-value (Chi-2)", f"{p:.4f}")
                            c2.metric("V de Cramer (Force)", f"{v_cramer:.3f}")
                            
                            if p < 0.05:
                                st.success(f"✅ **Lien Significatif.** Le statut (Étudiant/Enseignant) influence la réponse.")
                                # Interprétation de la force
                                if v_cramer < 0.10: strength = "Négligeable"
                                elif v_cramer < 0.30: strength = "Faible"
                                elif v_cramer < 0.50: strength = "Moyenne"
                                else: strength = "Forte"
                                st.info(f"💪 Force du lien : **{strength}**")
                            else:
                                st.warning("❌ **Indépendance.** Pas de lien statistique détecté entre le statut et cette réponse.")
                            
                            st.plotly_chart(px.imshow(ct, text_auto=True, title="Carte de Chaleur des Effectifs"), use_container_width=True)
                        else:
                            st.error("Variables catégorielles (Statut ou Plan) introuvables.")

                
                # ONGLET 4 : STRUCTURE & PSYCHOMETRIE
                # =========================================================================
                with tabs[4]:
                    st.header("4️⃣ Structure & Psychométrie")
                    
                    # --- BLOC D'EXPLICATION (ENCADRÉ BLEU) ---
                    st.info("""
                    ### 🧐 De quoi s'agit-il ?
                    Nous ne regardons plus les *réponses*, mais la **qualité des questions**. Nous vérifions si le questionnaire est un instrument de mesure fiable.
                    
                    * **Fiabilité (Alpha de Cronbach) :** Mesure la cohérence interne. Si un enseignant/étudiant est "bon", il doit réussir toutes les questions difficiles. Si les réponses partent dans tous les sens, la fiabilité est basse.
                    * **Structure (ACP) :** Vérifie combien de "compétences" ou dimensions cachées le questionnaire mesure réellement (1 seule compétence globale ? ou 3 compétences distinctes ?).
                    """)

                    # --- LA QUESTION (ENCADRÉ VERT) ---
                    st.success("""
                    **❓ La Question posée :** "Mon questionnaire est-il cohérent et mesure-t-il bien ce qu'il est censé mesurer ?"
                    """)
                    
                    st.divider()

                    # --- FILTRAGE LOCAL AJOUTÉ (Sans modifier le reste) ---
                    st.write("### 1. Population à cartographier")
                    c_acp1, c_acp2 = st.columns([1, 2])
                    filter_acp = c_acp1.selectbox("Qui inclure ?", ["Tout le monde"] + list(all_options), key="acp_filter")
                    
                    if filter_acp == "Tout le monde":
                        df_acp = df.copy()
                    else:
                        clean_acp = filter_acp.replace("🟩 ", "")
                        mask_acp = get_mask_for_status(clean_acp, df)
                        df_acp = df[mask_acp].copy()
                        
                    c_acp2.success(f"🗺️ Cartographie de **{len(df_acp)}** participants.")
                    st.divider()
                    # ----------------------------------------------------

                    # 1. SÉLECTION DES ITEMS
                    tech_cols = [c for c in df_acp.columns if str(c).startswith('score_')]
                    sel_cols = st.multiselect("Sélectionner les items (Questions notées) à analyser :", tech_cols, default=tech_cols[:10])
                    
                    if len(sel_cols) > 2:
                        # Nettoyage des données pour l'analyse
                        df_psy = df_acp[sel_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
                        # On retire les colonnes où tout le monde a la même note (Variance nulle)
                        df_psy = df_psy.loc[:, df_psy.var() > 0]
                        
                        # --- A. FIABILITÉ (CRONBACH) ---
                        st.subheader("🅰️ Fiabilité (Alpha de Cronbach)")
                        
                        # Calcul manuel de l'Alpha
                        k = df_psy.shape[1]
                        var_item = df_psy.var(ddof=1).sum()
                        var_tot = df_psy.sum(axis=1).var(ddof=1)
                        
                        if var_tot > 0:
                            alpha = (k / (k - 1)) * (1 - (var_item / var_tot))
                        else:
                            alpha = 0
                        
                        c1, c2 = st.columns([1, 3])
                        c1.metric("Score Alpha", f"{alpha:.3f}")
                        
                        with c2:
                            if alpha > 0.9: st.success("🌟 **Excellent.** Cohérence interne très forte.")
                            elif alpha > 0.7: st.success("✅ **Bon.** Le questionnaire est fiable.")
                            elif alpha > 0.6: st.warning("⚠️ **Acceptable.** Mais un peu fragile.")
                            else: st.error("❌ **Faible.** Les questions ne semblent pas mesurer la même chose.")
                        
                        st.markdown("---")

                        # --- B. STRUCTURE (ACP) ---
                        st.subheader("🅱️ Validité Structurelle (ACP)")
                        
                        if SKLEARN_AVAILABLE:
                            st.write("Analyse des dimensions latentes (Eboulis des valeurs propres).")
                            
                            try:
                                scaler = StandardScaler()
                                X_scaled = scaler.fit_transform(df_psy)
                                
                                # On limite à 10 composantes max pour la lisibilité
                                n_comps = min(len(sel_cols), 10)
                                pca = PCA(n_components=n_comps)
                                pca.fit(X_scaled)
                                
                                exp_var = pca.explained_variance_ratio_ * 100
                                cum_var = np.cumsum(exp_var)
                                
                                # Graphique combiné (Barres + Courbe)
                                fig_scree = go.Figure()
                                fig_scree.add_trace(go.Bar(
                                    x=[f"Dim {i+1}" for i in range(n_comps)], 
                                    y=exp_var, 
                                    name='Variance Expliquée (%)',
                                    marker_color='#3498db'
                                ))
                                fig_scree.add_trace(go.Scatter(
                                    x=[f"Dim {i+1}" for i in range(n_comps)], 
                                    y=cum_var, 
                                    name='Variance Cumulée (%)',
                                    mode='lines+markers',
                                    line=dict(color='#e74c3c')
                                ))
                                
                                fig_scree.update_layout(title="Poids des Dimensions (Scree Plot)", yaxis_title="% d'information expliquée")
                                st.plotly_chart(fig_scree, use_container_width=True)
                                
                                
                                st.caption(f"💡 Lecture : La 1ère dimension explique à elle seule **{exp_var[0]:.1f}%** des différences de niveau entre les participants.")
                                
                            except Exception as e:
                                st.error(f"Erreur lors du calcul de l'ACP : {e}")
                        else:
                            st.warning("⚠️ La librairie 'scikit-learn' est requise pour l'ACP.")
                            
                    else:
                        st.info("👈 Veuillez sélectionner au moins 3 questions dans la liste ci-dessus.")

                            # =========================================================================
                
                # =========================================================================
                # ONGLET 5 : MODÉLISATION PRÉDICTIVE (ML & IA)
                # =========================================================================
                with tabs[5]:
                    st.header("5️⃣ Modélisation Prédictive")
                    
                    # --- BLOC D'EXPLICATION (ENCADRÉ BLEU) ---
                    st.info("""
                    ### 🧐 De quoi s'agit-il ?
                    Ici, nous dépassons la simple observation pour essayer de **prédire** les résultats ou de **classer** les profils.
                    
                    * **Régression Linéaire :** Pour expliquer une note précise (ex: *"Chaque année d'ancienneté ajoute +0.5 point"*).
                    * **Régression Logistique :** Pour prédire une chance de succès (ex: *"Quels facteurs augmentent la probabilité d'être un 'Expert' ?"*).
                    * **Random Forest (IA) :** Une méthode plus puissante qui détecte les facteurs importants même si la relation est complexe (non-linéaire).
                    * **Clustering :** L'ordinateur crée lui-même des groupes d'enseignants qui se ressemblent ("Profils Types").
                    """)

                    # --- LA QUESTION (ENCADRÉ VERT) ---
                    st.success("""
                    **❓ La Question posée :** "Quels sont les leviers (Ancienneté, Statut, Formation...) qui déterminent réellement la performance ?"
                    """)
                    
                    st.divider()

                    # --- FILTRAGE LOCAL AJOUTÉ (Sans modifier le reste) ---
                    st.write("### 1. Population à modéliser")
                    c_mod1, c_mod2 = st.columns([1, 2])
                    filter_mod = c_mod1.selectbox("Qui inclure ?", ["Tout le monde"] + list(all_options), key="mod_filter")
                    
                    if filter_mod == "Tout le monde":
                        df_model = df.copy()
                    else:
                        clean_mod = filter_mod.replace("🟩 ", "")
                        mask_mod = get_mask_for_status(clean_mod, df)
                        df_model = df[mask_mod].copy()
                    
                    c_mod2.success(f"🔮 Modèle entraîné sur **{len(df_model)}** participants.")
                    st.divider()
                    # ----------------------------------------------------

                    # SOUS-ONGLETS
                    subtab_reg, subtab_logit, subtab_rf, subtab_clus = st.tabs([
                        "📉 Régression Linéaire", 
                        "🔮 Régression Logistique", 
                        "🌳 Random Forest (IA)", 
                        "🧩 Clustering (Profils)"
                    ])
                    
                    # --- 1. REGRESSION LINEAIRE (OLS) ---
                    with subtab_reg:
                        st.subheader("Régression Multiple (OLS)")
                        st.caption("Expliquer une note numérique par plusieurs facteurs.")
                        
                        if total_cols:
                            y_col = st.selectbox("Cible à expliquer (Y) :", total_cols, key="ols_y")
                            
                            # Création liste X (Facteurs potentiels)
                            x_cols = [c for c in df_model.columns if any(k in c.lower() for k in ["statut", "ancien", "score_", "zone"]) and c != y_col][:50]
                            sel_x = st.multiselect("Facteurs explicatifs (X) :", x_cols, default=x_cols[:2], key="ols_x")
                            
                            if st.button("🚀 Calculer le Modèle (OLS)"):
                                if sel_x:
                                    try:
                                        # Préparation (One-Hot Encoding pour les variables texte)
                                        df_r = df_model[[y_col] + sel_x].dropna()
                                        X = sm.add_constant(pd.get_dummies(df_r[sel_x], drop_first=True).astype(float))
                                        model = sm.OLS(df_r[y_col], X).fit()
                                        
                                        # Résultat R²
                                        st.success(f"**Puissance du modèle (R²) : {model.rsquared:.1%}**")
                                        st.info(f"Les facteurs choisis expliquent **{model.rsquared:.1%}** de la variation de la note.")

                                        # --- AJOUT : FENÊTRE D'AIDE CLIQUABLE ---
                                        with st.expander("📘 Aide à la lecture : Comment comprendre ces graphiques ?", expanded=False):
                                            st.markdown("""
                                            Voici comment interpréter les résultats ci-dessous :
                                            
                                            **1. Le Score (R²) juste au-dessus :**
                                            * C'est la note de votre modèle. S'il est à **10%**, vos facteurs expliquent peu de choses. S'il est à **50%** ou plus, c'est que vous avez trouvé des causes importantes !
                                            
                                            **2. L'Impact des Facteurs (1er graphique - Barres) :**
                                            * **Barre à Droite (>0) :** Ce facteur fait **monter** la note (Relation positive).
                                            * **Barre à Gauche (<0) :** Ce facteur fait **baisser** la note (Relation négative).
                                            * **La Couleur :** Regardez surtout les barres **VERTES**. Ce sont les seules qui sont statistiquement fiables. Les grises peuvent être dues au hasard.
                                            
                                            **3. Les Erreurs (2ème graphique - Résidus) :**
                                            * On vérifie si le modèle se trompe de façon aléatoire. Idéalement, les points ne doivent former aucun dessin particulier.
                                            
                                            **4. Réalité vs Prédiction (3ème graphique - Nuage) :**
                                            * **Ligne Rouge :** C'est la prédiction parfaite.
                                            * **Les Points :** Ce sont vos participants. Plus les points sont collés à la ligne rouge, plus le modèle a "deviné" juste leur note réelle.
                                            """)
                                        # ----------------------------------------
                                        
                                        # Graphique Coefficients
                                        res = pd.DataFrame({"Facteur": model.params.index, "Coef": model.params.values, "P": model.pvalues.values})
                                        res = res[res.Facteur != "const"]
                                        
                                        # Code couleur (Vert = Significatif, Gris = Hasard)
                                        res['Significatif'] = res['P'] < 0.05
                                        
                                        fig_coef = px.bar(res, x="Coef", y="Facteur", color="Significatif", orientation='h', title="Impact des facteurs (Coefficients)")
                                        fig_coef.add_vline(x=0, line_width=2, line_color="black")
                                        st.plotly_chart(fig_coef, use_container_width=True)
                                        
                                        # Diagnostic des Résidus
                                        st.markdown("#### 🩺 Diagnostic (Qualité du modèle)")
                                        fig_resid = px.scatter(x=model.fittedvalues, y=model.resid, title="Analyse des Résidus (Erreurs)")
                                        fig_resid.add_hline(y=0, line_dash="dash", line_color="red")
                                        fig_resid.update_layout(xaxis_title="Note Prédite", yaxis_title="Erreur (Réel - Prédit)")
                                        st.plotly_chart(fig_resid, use_container_width=True)

                                        # --- AJOUT DU NUAGE DE POINTS (RÉEL vs PRÉDIT) ---
                                        st.markdown("#### 🎯 Nuage de points : Réalité vs Prédiction")
                                        # On crée un DF temporaire pour le graphique
                                        df_cloud = pd.DataFrame({'Réel': df_r[y_col], 'Prédit': model.fittedvalues})
                                        
                                        fig_cloud = px.scatter(df_cloud, x='Réel', y='Prédit', 
                                                               title="Comparaison : Valeurs Réelles vs Prédites",
                                                               opacity=0.6,
                                                               labels={'Réel': 'Note Réelle (Observée)', 'Prédit': 'Note Prédite par le modèle'})
                                        
                                        # Ajout d'une ligne diagonale rouge (Idéal si tous les points sont dessus)
                                        min_val = min(df_cloud['Réel'].min(), df_cloud['Prédit'].min())
                                        max_val = max(df_cloud['Réel'].max(), df_cloud['Prédit'].max())
                                        fig_cloud.add_shape(type="line", x0=min_val, y0=min_val, x1=max_val, y1=max_val,
                                                            line=dict(color="red", dash="dash"))
                                        
                                        st.plotly_chart(fig_cloud, use_container_width=True)
                                        # -------------------------------------------------
                                        
                                    except Exception as e:
                                        st.error(f"Erreur de calcul : {e}")
                                else:
                                    st.warning("Veuillez sélectionner au moins un facteur X.")

                    # --- 2. REGRESSION LOGISTIQUE (LOGIT) ---
                    with subtab_logit:
                        st.subheader("Régression Logistique (Probabilités)")
                        st.caption("Prédire la chance d'appartenir au groupe 'Haut Niveau'.")
                        

                        if total_cols:
                            # 1. Définition du succès
                            target_bin = st.selectbox("Sur quelle note définir le succès ?", total_cols, key="logit_y")
                            median_val = df_model[target_bin].median()
                            st.write(f"👉 On considère comme **'Succès'** toute note supérieure à la médiane : **{median_val:.2f}**")
                            
                            # 2. Facteurs
                            sel_x_log = st.multiselect("Facteurs prédictifs :", x_cols, default=x_cols[:2], key="logit_x")
                            
                            if st.button("🔮 Calculer les Odds Ratios"):
                                try:
                                    df_l = df_model[[target_bin] + sel_x_log].dropna()
                                    # Binarisation : 1 si > médiane, 0 sinon
                                    df_l['Target_Bin'] = (df_l[target_bin] > median_val).astype(int)
                                    
                                    X = sm.add_constant(pd.get_dummies(df_l[sel_x_log], drop_first=True).astype(float))
                                    logit_model = sm.Logit(df_l['Target_Bin'], X).fit(disp=0)
                                    
                                    # Odds Ratios
                                    odds = np.exp(logit_model.params)
                                    pvals = logit_model.pvalues
                                    res_log = pd.DataFrame({"Facteur": odds.index, "Odds Ratio": odds.values, "P-value": pvals.values})
                                    res_log = res_log[res_log.Facteur != "const"]
                                    
                                    st.success("Modèle calculé avec succès !")

                                    # --- AJOUT : FENÊTRE D'AIDE CLIQUABLE ---
                                    with st.expander("📘 Aide à la lecture : Comprendre les Chances et la Précision", expanded=False):
                                        st.markdown("""
                                        Ce modèle ne prédit pas une note exacte, mais **la probabilité de réussir** (d'être au-dessus de la médiane).
                                        
                                        **1. Le graphique des barres (Odds Ratios) :**
                                        * C'est un multiplicateur de chance.
                                        * **Barre > 1 (Droite) :** C'est un **Bonus**. Ce facteur augmente la probabilité de succès (ex: 1.5 = +50% de chance).
                                        * **Barre < 1 (Gauche) :** C'est un **Malus**. Ce facteur diminue la probabilité de succès.
                                        * **Ligne pointillée (1) :** Zone neutre (aucun effet).
                                        
                                        **2. La Courbe ROC (Zone Bleue) :**
                                        * Elle mesure la capacité du modèle à ne pas se tromper.
                                        * Plus la zone bleue est **bombée vers le coin haut-gauche**, meilleur est le modèle.
                                        * **Score AUC :**
                                            * **0.50 :** Pile ou face (le modèle devine au hasard).
                                            * **0.70 :** Modèle correct.
                                            * **0.90 :** Excellent modèle.
                                        """)
                                    # ----------------------------------------
                                    
                                    # Graphique Odds Ratios
                                    st.markdown("### 📊 Les Facteurs de Chance (Odds Ratios)")
                                    fig_or = px.bar(res_log, x="Odds Ratio", y="Facteur", color="P-value", title="Impact sur la probabilité de succès")
                                    fig_or.add_vline(x=1, line_dash="dash", line_color="black", annotation_text="Neutre")
                                    st.plotly_chart(fig_or, use_container_width=True)
                                    st.caption("💡 **Lecture :** Si la barre dépasse 1, ce facteur **favorise** la réussite. Si elle est en dessous de 1, il la pénalise.")
                                    
                                    # Courbe ROC
                                    st.markdown("---")
                                    st.subheader("🎯 Précision (Courbe ROC)")
                                    y_prob = logit_model.predict(X)
                                    fpr, tpr, _ = roc_curve(df_l['Target_Bin'], y_prob)
                                    roc_auc = auc(fpr, tpr)
                                    
                                    col_auc1, col_auc2 = st.columns([3, 1])
                                    with col_auc1:
                                        fig_roc = px.area(x=fpr, y=tpr, title=f'Courbe ROC (AUC = {roc_auc:.2f})', labels={'x':'Faux Positifs', 'y':'Vrais Positifs'})
                                        fig_roc.add_shape(type='line', line=dict(dash='dash'), x0=0, x1=1, y0=0, y1=1)
                                        st.plotly_chart(fig_roc, use_container_width=True)
                                    with col_auc2:
                                        st.metric("Score AUC", f"{roc_auc:.2f}")
                                        if roc_auc > 0.7: st.success("✅ Bon Modèle")
                                        else: st.warning("⚠️ Modèle Faible")
                                    
                                except Exception as e:
                                    st.error(f"Le modèle n'a pas convergé (Données insuffisantes ou trop séparées). Erreur : {e}")

                    # --- 3. RANDOM FOREST (IA) ---
                    with subtab_rf: 
                        st.subheader("Importance des Variables (Random Forest)")
                        st.caption("Intelligence Artificielle pour détecter les facteurs clés (linéaires ou non).")
                        
                        if total_cols:
                            rf_target = st.selectbox("Cible à expliquer :", total_cols, key="rf_y")
                            
                            # --- AJOUT FILTRES (Parties vs Questions) ---
                            st.write("###### ⚙️ Choisir les variables à tester")
                            filter_mode = st.radio(
                                "Niveau de détail :", 
                                ["Tout inclure (Automatique)", "Scores & Totaux (Parties)", "Questions détaillées (Items)"],
                                horizontal=True
                            )
                            
                            # 1. On récupère toutes les numériques possibles
                            all_candidates = [c for c in df.columns if df[c].dtype in ['float64', 'int64'] and c != rf_target and "ID" not in c]
                            
                            # 2. On applique le filtre
                            if "Scores" in filter_mode:
                                # Garde ce qui contient "score", "total", "moyenne", "dim"
                                default_feats = [c for c in all_candidates if any(x in c.lower() for x in ['score', 'total', 'moyenne', 'dim', 'partie'])]
                            elif "Questions" in filter_mode:
                                # Garde ce qui contient "Q", "Item" et qui n'est pas un total
                                default_feats = [c for c in all_candidates if any(x in c.lower() for x in ['q', 'item']) and "total" not in c.lower()]
                            else:
                                default_feats = all_candidates

                            # 3. Multiselect pour ajustement final
                            rf_features = st.multiselect("Confirmez les variables (X) :", all_candidates, default=default_feats)
                            # --------------------------------------------
                            
                            if st.button("🌲 Lancer l'IA (Random Forest)"):
                                if rf_features:
                                    try:
                                        from sklearn.ensemble import RandomForestRegressor
                                        
                                        # Utilisation de df_model si disponible, sinon df (sécurité)
                                        data_src = df_model if 'df_model' in locals() else df
                                        df_rf = data_src[[rf_target] + rf_features].dropna()
                                        
                                        X = df_rf[rf_features]
                                        y = df_rf[rf_target]
                                        
                                        # Modèle
                                        rf = RandomForestRegressor(n_estimators=100, random_state=42)
                                        rf.fit(X, y)
                                        
                                        # Importance
                                        importances = pd.DataFrame({
                                            'Variable': rf_features,
                                            'Importance': rf.feature_importances_
                                        }).sort_values('Importance', ascending=True).tail(15)
                                        
                                        st.success(f"Précision IA (R²) : {rf.score(X, y):.1%}")

                                        # --- AJOUT : FENÊTRE D'AIDE CLIQUABLE ---
                                        with st.expander("📘 Aide à la lecture : Qu'est-ce que l'Importance ?", expanded=False):
                                            st.markdown("""
                                            L'IA (Forêt Aléatoire) a testé des milliers de combinaisons pour prédire la note cible.
                                            
                                            **Comment lire le graphique ci-dessous ?**
                                            * **La longueur de la barre :** Elle indique le **poids** de la variable dans la décision finale.
                                            * **Une grande barre :** Signifie que si cette variable change, la note cible change beaucoup. C'est un facteur déterminant.
                                            * **Une petite barre :** Cette variable a peu d'impact sur le résultat.
                                            
                                            *Note : Contrairement à la régression classique, ce graphique ne dit pas si l'effet est positif ou négatif, il dit juste que c'est "Important".*
                                            """)
                                        # ----------------------------------------
                                        
                                        fig_rf = px.bar(importances, x='Importance', y='Variable', orientation='h', title="Top 15 des Facteurs d'influence")
                                        st.plotly_chart(fig_rf, use_container_width=True)
                                        st.caption("Lecture : Plus la barre est longue, plus cette variable est cruciale pour la prédiction.")
                                    
                                    except Exception as e:
                                        st.error(f"Erreur Random Forest : {e}")
                                else:
                                    st.warning("Veuillez sélectionner au moins une variable explicative.")

                    # --- 4. CLUSTERING (K-MEANS) ---
                    with subtab_clus:
                        st.subheader("Clustering (K-Means)")
                        st.caption("Regrouper automatiquement les enseignants qui se ressemblent.")
                        
                        # --- DEFINITION DES NOMS PERSONNALISÉS ---
                        mapping_noms = {
                            "total_partie_2": "1-Fonctionnement et développement de la production écrite chez les élèves",
                            "total_partie_3": "2-Interventions pour améliorer la production écrite",
                            "total_partie_4": "3-Des outils numériques pour enseigner et apprendre la production écrite",
                            "total_partie_5": "4-Évaluation de la production écrite",
                            "total _partie_5": "4-Évaluation de la production écrite" # Cas avec espace (si présent dans fichier)
                        }

                        # --- CORRECTION FILTRES ---
                        # 1. On ne prend QUE les colonnes qui sont des chiffres (float/int)
                        cols_numeriques = df.select_dtypes(include=['float64', 'int64']).columns
                        
                        # 2. On garde celles qui contiennent "total" ET "partie"
                        # 3. ET on exclut explicitement "Quelle", "appro" ou "3.6" pour nettoyer l'affichage
                        options_cluster = [
                            c for c in cols_numeriques 
                            if "total" in c.lower() 
                            and "partie" in c.lower() 
                            and "quelle" not in c.lower()
                        ]
                        
                        # Sécurité : Si la liste est vide, on prend toutes les numériques (sauf ID et Questions)
                        if not options_cluster:
                             options_cluster = [c for c in cols_numeriques if "ID" not in c and "quelle" not in c.lower()]
                        
                        # AJOUT format_func pour afficher tes titres
                        vars_c = st.multiselect(
                            "Critères de regroupement :", 
                            options_cluster, 
                            default=options_cluster, 
                            key="clus_vars",
                            format_func=lambda x: mapping_noms.get(x, x) # Affiche le titre si dispo, sinon le nom original
                        )
                        
                        if len(vars_c) > 1:
                            nk = st.slider("Nombre de profils à créer :", 2, 5, 3)
                            
                            if st.button("🔍 Identifier les profils"):
                                try:
                                    # On utilise df avec les colonnes sélectionnées (Noms originaux pour le calcul)
                                    data_clus = df[vars_c].dropna()
                                    
                                    # Standardisation
                                    X_std = StandardScaler().fit_transform(data_clus)
                                    
                                    # Algorithme
                                    km = KMeans(n_clusters=nk, random_state=42).fit(X_std)
                                    
                                    # Préparation Résultats
                                    # ICI : On renomme les colonnes pour que le graphique affiche tes titres
                                    cols_display = [mapping_noms.get(c, c) for c in vars_c]
                                    df_res = pd.DataFrame(X_std, columns=cols_display)
                                    
                                    df_res['Cluster'] = km.labels_.astype(str)
                                    
                                    st.success(f"✅ {nk} groupes identifiés avec succès sur {len(data_clus)} participants.")

                                    # --- FENÊTRE D'AIDE CLIQUABLE ---
                                    with st.expander("📘 Aide à la lecture : Comment comprendre ces Profils ?", expanded=False):
                                        st.markdown("""
                                        L'ordinateur a scanné les réponses pour créer des "familles" de participants qui se ressemblent.
                                        
                                        **1. La Carte d'Identité (Graphique Radar - En haut) :**
                                        * C'est le "portrait robot" de chaque groupe.
                                        * **Comment lire ?** Regardez les pointes colorées.
                                        * Si la ligne d'un groupe tire vers **l'extérieur** sur une branche (ex: Total Partie 5), cela veut dire que ce groupe est **très fort** dans ce domaine.
                                        * Si elle reste au **centre**, le groupe est faible.
                                        
                                        **2. La Carte des Individus (Nuage de points - En bas) :**
                                        * Chaque point est une personne réelle (un enseignant).
                                        * **Proximité :** Deux points côte à côte sont deux personnes qui ont répondu presque la même chose.
                                        * **Couleurs :** Elles montrent comment l'algorithme a découpé la population. Si les couleurs sont bien séparées, les profils sont très distincts.
                                        """)
                                    # ----------------------------------------
                                    
                                    # 1. Graphique Radar (Profils)
                                    means = df_res.groupby('Cluster').mean().reset_index().melt(id_vars='Cluster')
                                    fig_radar = px.line_polar(means, r='value', theta='variable', color='Cluster', line_close=True, title="Carte d'Identité des Profils")
                                    fig_radar.update_traces(fill='toself')
                                    st.plotly_chart(fig_radar, use_container_width=True)
                                    
                                    st.caption("Les axes sont des valeurs standardisées (0 = Moyenne globale). Si ça tend vers l'extérieur, le groupe est fort dans ce domaine.")
                                    
                                    # 2. Graphique PCA (Nuage de points 2D)
                                    st.markdown("---")
                                    st.subheader("Visualisation des individus (Projection 2D)")
                                    pca = PCA(n_components=2)
                                    coords = pca.fit_transform(X_std)
                                    df_res['x'] = coords[:, 0]
                                    df_res['y'] = coords[:, 1]
                                    
                                    fig_pca = px.scatter(df_res, x='x', y='y', color='Cluster', title="Carte des individus", opacity=0.7)
                                    st.plotly_chart(fig_pca, use_container_width=True)
                                    
                                except Exception as e:
                                    st.error(f"Erreur Clustering : {e}")
                
                # ONGLET 6 : ANALYSE TEXTUELLE (NLP)
                # =========================================================================
                with tabs[6]:
                    st.header("6️⃣ Analyse Textuelle (NLP)")
                    
                    # --- BLOC D'EXPLICATION (ENCADRÉ BLEU) ---
                    st.info("""
                    ### 🧐 De quoi s'agit-il ?
                    Le NLP (Traitement du Langage Naturel) permet de transformer du texte brut (commentaires libres) en données statistiques.
                    
                    * **Nuage de Mots :** Pour voir en un coup d'œil les termes les plus fréquents.
                    * **Analyse de Sentiment :** Pour identifier automatiquement les commentaires les plus élogieux et les plus critiques.
                    """)

                    # --- LA QUESTION (ENCADRÉ VERT) ---
                    st.success("""
                    **❓ La Question posée :** "Quels sont les mots-clés dominants et quel est le ressenti général des participants ?"
                    """)
                    
                    st.divider()

                    # --- FILTRAGE LOCAL AJOUTÉ (Sans modifier le reste) ---
                    st.write("### 1. De qui veut-on lire les réponses ?")
                    c_txt1, c_txt2 = st.columns([1, 2])
                    filter_txt = c_txt1.selectbox("Qui inclure ?", ["Tout le monde"] + list(all_options), key="txt_filter")
                    
                    if filter_txt == "Tout le monde":
                        df_txt = df.copy()
                    else:
                        clean_txt = filter_txt.replace("🟩 ", "")
                        mask_txt = get_mask_for_status(clean_txt, df)
                        df_txt = df[mask_txt].copy()
                        
                    c_txt2.success(f"📚 Analyse sur **{len(df_txt)}** participants.")
                    st.divider()
                    # ----------------------------------------------------

                    # 1. SÉLECTION DE LA COLONNE TEXTE
                    target_col_name = "Nous sommes preneurs, le cas échéant, de vos commentaires...(Réponse non obligatoire)"
                    
                    # Si la colonne existe, on ne propose qu'elle. Sinon, on garde l'ancienne méthode.
                    if target_col_name in df_txt.columns:
                        text_cols = [target_col_name]
                    else:
                        text_cols = [c for c in df_txt.columns if df_txt[c].dtype == 'object' and df_txt[c].str.len().mean() > 15]
                    
                    if text_cols:
                        sel_text = st.selectbox("Choisir la question ouverte à analyser :", text_cols)
                        
                        if st.button("🚀 Lancer l'analyse textuelle"):

                            # --- FENÊTRE D'AIDE CLIQUABLE ---
                            with st.expander("📘 Aide à la lecture : Comment interpréter ces résultats ?", expanded=False):
                                st.markdown("""
                                Voici les clés pour lire l'analyse automatique des commentaires :
                                
                                **1. Le Nuage de Mots (Image colorée) :**
                                * **La taille = La fréquence.** Plus un mot est écrit gros, plus il a été répété par les participants.
                                * C'est idéal pour repérer instantanément le sujet n°1 (ex: "Manque", "Temps", "Super").
                                
                                **2. Les Sentiments (Top & Flop) :**
                                * L'ordinateur cherche des mots positifs (super, bien, merci) et négatifs (nul, déçu, difficile).
                                * Il affiche ensuite les commentaires les plus **enthousiastes** (👍) et les plus **critiques** (👎) pour vous faire gagner du temps de lecture.
                                """)
                            # ----------------------------------------
                            
                            # --- PRÉPARATION (NETTOYAGE) ---
                            raw_text_series = df_txt[sel_text].dropna().astype(str)
                            # Tout en minuscule
                            all_text = " ".join(raw_text_series.str.lower())
                            
                            # Stopwords (Mots vides à retirer)
                            stopwords = {
                                "le", "la", "les", "de", "des", "du", "un", "une", "et", "est", "en", "à", 
                                "pour", "dans", "ce", "par", "pas", "sur", "au", "qui", "que", "je", "ne", 
                                "se", "c'est", "il", "a", "on", "nous", "vous", "ai", "mais", "très", "bien", 
                                "plus", "mon", "ma", "mes", "sont", "ont", "y", "ou", "donc", "car", "ni",
                                "si", "tout", "tous", "faire", "fait", "comme", "aussi", "avec", "sans"
                            }

                            # --- A. NUAGE DE MOTS ---
                            st.subheader("🅰️ Nuage de Mots (WordCloud)")
                            try:
                                from wordcloud import WordCloud
                                import matplotlib.pyplot as plt
                                
                                # Génération
                                wc = WordCloud(width=800, height=400, background_color='white', stopwords=stopwords, colormap='viridis').generate(all_text)
                                
                                # Affichage
                                fig, ax = plt.subplots(figsize=(10, 5))
                                ax.imshow(wc, interpolation='bilinear')
                                ax.axis("off")
                                st.pyplot(fig)
                                
                            except ImportError:
                                st.warning("⚠️ Librairie 'wordcloud' absente. Affichage Histogramme à la place.")
                                # Fallback : Histogramme simple
                                words = [w.strip(".,;!?'\"") for w in all_text.split() if w.strip(".,;!?'\"") not in stopwords and len(w) > 3]
                                st.bar_chart(pd.Series(words).value_counts().head(20))

                            st.markdown("---")

                            # --- B. SENTIMENTS (POS/NEG) ---
                            st.subheader("🅱️ Analyse de Sentiment (Top & Flop)")
                            st.caption("Classement basé sur la présence de mots positifs ou négatifs.")
                            
                            # Dictionnaires simples
                            mots_pos = ["super", "bien", "bon", "excellent", "génial", "top", "parfait", "aimé", "intéressant", "utile", "clair", "efficace", "enrichissant", "merci", "bravo", "satisfait"]
                            mots_neg = ["nul", "mauvais", "problème", "difficile", "ennuyeux", "compliqué", "déçu", "long", "bof", "inutile", "flou", "manque", "regrette", "dommage", "pas terrible", "lent", "insuffisant"]

                            def get_score(text):
                                t = text.lower()
                                score = 0
                                score += sum(1 for w in mots_pos if w in t)
                                score -= sum(1 for w in mots_neg if w in t)
                                return score

                            # Calcul
                            df_sent = df_txt[[sel_text]].dropna().copy()
                            df_sent['Score'] = df_sent[sel_text].apply(get_score)
                            
                            # Tri
                            top_3 = df_sent.sort_values('Score', ascending=False).head(3)
                            flop_3 = df_sent.sort_values('Score', ascending=True).head(3)

                            c_pos, c_neg = st.columns(2)
                            
                            with c_pos:
                                st.success("🌟 **Les plus POSITIFS**")
                                if not top_3.empty and top_3.iloc[0]['Score'] > 0:
                                    for i, row in top_3.iterrows():
                                        if row['Score'] > 0:
                                            st.markdown(f"👍 *\"{row[sel_text]}\"*")
                                            st.caption(f"Score : +{row['Score']}")
                                else:
                                    st.info("Aucun commentaire clairement positif.")

                            with c_neg:
                                st.error("🌧️ **Les plus NÉGATIFS**")
                                if not flop_3.empty and flop_3.iloc[0]['Score'] < 0:
                                    for i, row in flop_3.iterrows():
                                        if row['Score'] < 0:
                                            st.markdown(f"👎 *\"{row[sel_text]}\"*")
                                            st.caption(f"Score : {row['Score']}")
                                else:
                                    st.info("Aucun commentaire clairement négatif.")
                                    
                    else:
                        st.warning("⚠️ Aucune colonne de texte long (Commentaires) détectée dans ce fichier.")

    
        
                # >>> PAGE 7 : ASSISTANT COGNITIF (MODE DIAGNOSTIC + LECTURE CODE)
            elif page == "🧠 Assistant Cognitif":
                
                # --- 🎨 INJECTION CSS POUR LE DESIGN DU CHAT ---
                st.markdown("""
                <style>
                    /* Agrandir et styliser le conteneur du chat en bas */
                    [data-testid="stChatInput"] {
                        padding-bottom: 2rem;
                    }
                    /* Styliser la zone de saisie du texte (textarea) */
                    [data-testid="stChatInput"] textarea {
                        font-size: 1.15rem !important;
                        padding: 1.2rem !important;
                        border: 2px solid #FF4B4B !important;
                        border-radius: 15px !important;
                        box-shadow: 0px 8px 20px rgba(255, 75, 75, 0.15) !important;
                        transition: all 0.3s ease-in-out;
                        min-height: 60px;
                    }
                    /* Effet au clic (focus) */
                    [data-testid="stChatInput"] textarea:focus {
                        box-shadow: 0px 8px 20px rgba(255, 75, 75, 0.3) !important;
                    }
                    /* Icône d'envoi */
                    [data-testid="stChatInput"] button {
                        background-color: #FF4B4B !important;
                        color: white !important;
                        border-radius: 50% !important;
                        height: 40px;
                        width: 40px;
                        margin-right: 10px;
                    }
                </style>
                """, unsafe_allow_html=True)

                # --- EN-TÊTE PROFESSIONNEL ---
                col_h1, col_h2 = st.columns([1, 8])
                with col_h1:
                    # Icône de cerveau stylisée
                    st.image("https://cdn-icons-png.flaticon.com/512/8649/8649603.png", width=70) 
                with col_h2:
                    st.title("Assistant IA SciCoNum")
                    st.caption("Votre Data Scientist virtuel. Interrogez vos données ou décortiquez le code source en langage naturel.")
                
                st.info("💡 **Mode Expert activé :** L'IA a mémorisé l'intégralité de votre fichier Excel (statistiques, colonnes) ainsi que le code Python de cette application.")
                st.divider()

            
                # 1. CLÉ API SECURISEE
                GOOG_API_KEY = st.secrets["GOOG_API_KEY"]
                

                # Bouton Reset dans la Sidebar (Plus élégant)
                with st.sidebar:
                    st.markdown("---")
                    st.markdown("### ⚙️ Options de l'Assistant")
                    if st.button("🔄 Nouvelle conversation", use_container_width=True, type="primary"):
                        for key in ["gemini_chat_history", "chat_session", "gemini_model_ready"]:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

                import google.generativeai as genai
                import io
                
                # =========================================================
                # INITIALISATION DIRECTE ET UNIQUE
                # =========================================================
                if "gemini_model_ready" not in st.session_state:
                    with st.spinner("⚡ Connexion au réseau neuronal Gemini 2.5 Flash..."):
                        try:
                            genai.configure(api_key=GOOG_API_KEY)
                            
                            # --- 🚀 DÉTECTION SÉCURISÉE DU MODÈLE ---
                            modeles_dispos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                            
                            if not modeles_dispos:
                                st.error("❌ Votre clé API est valide, mais n'a accès à aucun modèle. Activez l'API sur Google Cloud.")
                                st.stop()
                                
                            # On force l'utilisation de Gemini 2.5 Flash en priorité
                            nom_modele_choisi = None
                            modeles_cibles = ['models/gemini-2.5-flash', 'models/gemini-2.5-flash-latest', 'gemini-2.5-flash']
                            
                            for m_ideal in modeles_cibles:
                                if m_ideal in modeles_dispos:
                                    nom_modele_choisi = m_ideal
                                    break
                            
                            # Si Gemini 2.5 n'est pas trouvé, on prend le premier qui n'est PAS la version 3
                            if not nom_modele_choisi:
                                modeles_sans_v3 = [m for m in modeles_dispos if "gemini-3" not in m]
                                nom_modele_choisi = modeles_sans_v3[0] if modeles_sans_v3 else modeles_dispos[0]
                            # ------------------------------------------------------

                            buffer = io.StringIO()
                            df.info(buf=buffer)
                            df_info = buffer.getvalue()
                            
                            try:
                                with open(__file__, "r", encoding='utf-8') as f:
                                    code_source = f.read()[:25000] + "\n... [Suite du code tronquée] ..."
                            except Exception as e:
                                code_source = f"Impossible de lire le code source : {e}"

                            system_prompt = f"""
                            Tu es un expert SciCoNum et Data Scientist.
                            
                            CONTEXTE 1 : LE CODE DE L'APPLICATION
                            Voici le code Python que l'utilisateur a écrit :
                            ----- DÉBUT CODE -----
                            {code_source}
                            ----- FIN CODE -----

                            CONTEXTE 2 : LES DONNÉES (Le fichier Excel)
                            Participants: {len(df)}
                            Structure: {df_info}
                            
                            TES MISSIONS :
                            1. Réponds aux questions sur les données.
                            2. Réponds aux questions sur le CODE.
                            Confirme simplement que tu as bien compris tes instructions.
                            """

                            model = genai.GenerativeModel(model_name=nom_modele_choisi)
                            
                            historique_initial = [
                                {"role": "user", "parts": [system_prompt]},
                                {"role": "model", "parts": [f"Compris. Connecté au modèle {nom_modele_choisi}. Je suis prêt."]}
                            ]
                            
                            st.session_state.chat_session = model.start_chat(history=historique_initial)
                            st.session_state.gemini_chat_history = []
                            st.session_state.gemini_model_ready = True
                            
                        except Exception as e:
                            st.error(f"❌ Erreur de l'API Google : {e}")
                            st.stop()

                # =========================================================
                # AFFICHAGE DE L'INTERFACE DE CHAT
                # =========================================================
                chat_container = st.container()
                
                with chat_container:
                    # ÉCRAN D'ACCUEIL : Si l'historique est vide, on affiche de jolies suggestions
                    if len(st.session_state.gemini_chat_history) == 0:
                        st.markdown("<br><h3 style='text-align: center; color: #2c3e50;'>Comment puis-je vous aider aujourd'hui ?</h3><br>", unsafe_allow_html=True)
                        
                        col_sug1, col_sug2, col_sug3 = st.columns(3)
                        with col_sug1:
                            st.success("**📊 Exploration des données**\n\n*« Quel est le score moyen des enseignants en Partie 3 ? »*")
                        with col_sug2:
                            st.info("**💻 Explication du code**\n\n*« Comment est calculé le graphique radar de la page Théorie vs Pratique ? »*")
                        with col_sug3:
                            st.warning("**🧠 Analyse cognitive**\n\n*« Résume-moi le profil d'usage numérique des néo-titulaires. »*")
                        
                        st.markdown("<br><br><br>", unsafe_allow_html=True)
                    
                    # Sinon, on affiche l'historique normal
                    else:
                        for role, text in st.session_state.gemini_chat_history:
                            avatar = "👤" if role == "user" else "🧠"
                            with st.chat_message(role, avatar=avatar):
                                st.markdown(text)

                # =========================================================
                # GESTION DU CHAMP DE SAISIE (INPUT)
                # =========================================================
                if prompt := st.chat_input("✨ Posez votre question ici (ex: Résume les forces et faiblesses des titulaires...)"):
                    
                    # 1. Afficher la question
                    with chat_container:
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(prompt)
                    st.session_state.gemini_chat_history.append(("user", prompt))
                    
                    # 2. Interroger l'IA
                    try:
                        with st.spinner("L'IA réfléchit..."):
                            response = st.session_state.chat_session.send_message(prompt)
                            
                        # 3. Afficher la réponse
                        with chat_container:
                            with st.chat_message("assistant", avatar="🧠"):
                                st.markdown(response.text)
                        st.session_state.gemini_chat_history.append(("assistant", response.text))
                    except Exception as e:
                        st.error(f"❌ Erreur de réponse : {e}")