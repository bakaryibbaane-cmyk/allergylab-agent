# Nécessite streamlit et plotly, hors verrouillage : uv run --with streamlit --with plotly streamlit run equipe/analyse/interface/app.py (voir README.md et JOURNAL.md)
# L'onglet d'analyse exploratoire demande en plus --with scikit-learn. Aucun autre fichier n'importe cette interface.
from __future__ import annotations
import sys, io
from pathlib import Path
from datetime import datetime
from html import escape

ROOT = Path(__file__).resolve().parents[3]  # racine du dépôt : equipe/analyse/interface/app.py
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from kit.donnees import charger, colonnes as charger_dictionnaire
from equipe.analyse.phase2 import (
    descriptive_statistics, compare_groups, correlation_matrix,
    data_quality, numeric_columns
)
# ml_exploratoire a besoin de scikit-learn : on ne l'importe qu'à l'usage, pour que le reste de l'interface se lance sans.
def _ml(nom, *args):
    try:
        from equipe.analyse import ml_exploratoire
    except ModuleNotFoundError as e:
        raise RuntimeError("Cet onglet nécessite scikit-learn : relancer avec uv run --with streamlit --with plotly --with scikit-learn streamlit run equipe/analyse/interface/app.py") from e
    return getattr(ml_exploratoire, nom)(*args)
def pca_projection(*args): return _ml("pca_projection", *args)
def clustering(*args): return _ml("clustering", *args)
def anomaly_detection(*args): return _ml("anomaly_detection", *args)


import base64

DOSSIER = Path(__file__).resolve().parent
# Icône passée par son chemin : pas de dépendance à Pillow, qui n'est pas dans pyproject.toml.
ICONE = str(DOSSIER / "assets" / "favicon.png")
LOGO_B64 = base64.b64encode((DOSSIER / "assets" / "logo_puce.svg").read_bytes()).decode("ascii")

st.set_page_config(page_title="AllergyLab | Research workspace", page_icon=ICONE,
                   layout="wide", initial_sidebar_state="expanded")

# ---------- Identité visuelle : AllergyLab Premium ----------
# Les couleurs de base viennent de .streamlit/config.toml (thème natif).
# Ce CSS ne règle que ce que le thème ne couvre pas. Palette :
#   nuit #07131f · abysse #0b2233 · pétrole #0f4c5c · turquoise #2dd4bf (accent)
#   blanc cassé #f4f1ea (zones de lecture) · ambre #e8b04b (alertes seulement)
PALETTE = ["#2dd4bf", "#4d8ea0", "#e8b04b", "#a6c7c5", "#0f4c5c"]
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght%409..144,500;9..144,600&family=IBM+Plex+Sans:wght%40400;500;600&family=IBM+Plex+Mono:wght%40500&display=swap');
:root{--bg:#07131f;--bg2:#0b2233;--panel:#0e2a3b;--line:#1b4357;--ink:#e9f1f2;--mute:#8fa9b5;
--petrol:#0f4c5c;--teal:#2dd4bf;--paper:#f4f1ea;--paperink:#12303d;--amber:#e8b04b;
--serif:'Fraunces',Georgia,serif;--sans:'IBM Plex Sans',system-ui,sans-serif;--mono:'IBM Plex Mono',ui-monospace,monospace}
html,body,[class*="css"],.stApp{font-family:var(--sans)}
.stApp{background:radial-gradient(1200px 600px at 80% -10%,var(--bg2),var(--bg))}
.block-container{padding-top:1.6rem;padding-bottom:3rem;max-width:1400px}
h1,h2,h3,h4{font-family:var(--serif)!important;font-weight:600!important;letter-spacing:-.01em;color:var(--ink)}
header[data-testid="stHeader"]{background:transparent}
footer{visibility:hidden}

/* Barre latérale */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#081a28,#0a2434);border-right:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:12px;padding:6px 4px 20px}
.brand img{width:42px;height:42px;display:block}
.brand-name{font:600 19px var(--serif);color:var(--ink)}
.brand-sub{font-size:11px;color:var(--mute);letter-spacing:.08em;text-transform:uppercase}
[data-testid="stSidebar"] [role="radiogroup"]{gap:2px}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:8px 12px;border-radius:10px;width:100%;cursor:pointer}
[data-testid="stSidebar"] [role="radiogroup"] label>div:first-child{display:none}
[data-testid="stSidebar"] [role="radiogroup"] label p{color:var(--mute);font-size:14px}
[data-testid="stSidebar"] [role="radiogroup"] label:hover p{color:var(--ink)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:linear-gradient(90deg,#2dd4bf26,#2dd4bf08);box-shadow:inset 2px 0 0 var(--teal)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:var(--ink);font-weight:600}
.ds{margin-top:4px;padding:12px;border:1px solid var(--line);border-radius:12px;font-size:12px;color:var(--mute);line-height:1.6}
.ds i{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--teal);margin-right:6px;box-shadow:0 0 8px var(--teal)}
.ds i.alt{background:var(--amber);box-shadow:0 0 8px var(--amber)}
.small-muted{color:var(--mute);font-size:12px}

/* En-têtes de page */
.eyebrow{font:500 12px var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--teal)}
.page-title{font:600 clamp(28px,4vw,40px)/1.1 var(--serif);margin:4px 0 6px;color:var(--ink)}
.page-desc{color:var(--mute);max-width:70ch;margin-bottom:18px}
.hero{background:linear-gradient(115deg,#0b2233 0%,#0f4c5c 70%,#12665f 100%);border:1px solid var(--line);
 padding:28px 30px;border-radius:16px;margin-bottom:20px}
.hero h1{font:600 clamp(28px,4vw,42px)/1.1 var(--serif)!important;margin:6px 0 8px}
.hero p{color:#cfe3e4;max-width:62ch;margin:0}

/* Indicateurs */
.kpi{background:linear-gradient(160deg,#0f3447,#0b2536);border:1px solid var(--line);border-radius:14px;padding:14px 16px;height:100%}
.kpi-label{font-size:12px;color:var(--mute)}
.kpi-value{font:600 30px var(--serif);margin:2px 0;color:var(--ink)}
.kpi-foot{font-size:11px;color:var(--teal)}
div[data-testid="stMetric"]{background:linear-gradient(160deg,#0f3447,#0b2536);border:1px solid var(--line);border-radius:14px;padding:12px 16px}
div[data-testid="stMetric"] label p{color:var(--mute)}
.panel-title{font:600 18px var(--serif);color:var(--ink)}
.panel-sub{color:var(--mute);font-size:13px;margin-bottom:6px}
div[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--line)!important;border-radius:14px}

/* Assistant : messages bien différenciés ; blanc cassé pour la lecture des réponses */
.chat-user{background:var(--petrol);border-radius:14px;padding:12px 16px;margin:10px 0 10px auto;max-width:86%;color:var(--ink)}
.chat-ai{display:flex;gap:12px;margin:10px 0}
.chat-ai img{width:30px;height:30px;flex:none;margin-top:2px}
.chat-ai .read{max-width:92%}
.read{background:var(--paper);color:var(--paperink);border-radius:14px;padding:14px 18px}
.read b,.read span{color:var(--paperink)}
.read .valeur{font:600 34px var(--serif);display:block;margin:2px 0 6px}
.read .statut{font:500 11px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:#0f5f58}
.read.abst{border-left:4px solid var(--amber)}
.mono{font:500 12px var(--mono);color:var(--mute)}

/* Saisie, boutons, onglets */
[data-testid="stChatInput"]{border:1px solid var(--line);border-radius:14px;background:var(--bg2)!important}
/* Champ de discussion : texte blanc sur fond bleu nuit, curseur et indication lisibles */
[data-testid="stChatInput"]>div{background:var(--bg2)!important}
[data-testid="stChatInput"] textarea{background:var(--bg2)!important;color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;caret-color:#ffffff!important}
[data-testid="stChatInput"] textarea::placeholder{color:#c9d6de!important;-webkit-text-fill-color:#c9d6de!important;opacity:1!important}
.stButton>button{border-radius:10px;font-weight:600;border:1px solid var(--line)}
.stButton>button:hover{border-color:var(--teal);color:var(--teal)}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#2dd4bf,#14a899);border:0;color:#06231f}
.stTabs [data-baseweb="tab-list"]{gap:8px}
hr{border-color:var(--line)}
@media(max-width:760px){.chat-user,.chat-ai .read{max-width:100%}}
</style>
""", unsafe_allow_html=True)

# Graphiques : même palette partout, fonds transparents sur le fond nuit.
_axe = dict(gridcolor="#1b4357", zerolinecolor="#1b4357", linecolor="#1b4357")
pio.templates["allergylab"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e9f1f2", family="IBM Plex Sans, system-ui, sans-serif"),
    colorway=PALETTE, xaxis=_axe, yaxis=_axe,
    title=dict(font=dict(family="Fraunces, Georgia, serif", size=18)),
    margin=dict(l=10, r=10, t=44, b=10)))
px.defaults.template = "allergylab"
px.defaults.color_discrete_sequence = PALETTE


def show_chart(fig, **kw):
    """Affiche un graphique plotly avec le gabarit AllergyLab, sans le recolorer."""
    kw.pop("use_container_width", None)
    st.plotly_chart(fig, theme=None, width="stretch", **kw)


def show_table(data, **kw):
    kw.pop("use_container_width", None)
    st.dataframe(data, width="stretch", **kw)

@st.cache_data(show_spinner="Lecture du dataset…")
def get_df():
    return charger()

@st.cache_data(show_spinner=False)
def get_dict():
    return charger_dictionnaire()

# ALLERGYLAB_CSV_IMPORT_V1
if "active_df" not in st.session_state:
    st.session_state["active_df"] = None

if "active_dataset_name" not in st.session_state:
    st.session_state["active_dataset_name"] = None

# Numéro du jeu actif : il change à chaque activation ou retour au jeu officiel,
# ce qui sert à ne recalculer les indicateurs qu'à ce moment-là.
if "active_version" not in st.session_state:
    st.session_state["active_version"] = 0

# Ce dont les pages ont besoin pour fonctionner sur un CSV importé.
COLONNES_REQUISES = ["Chip_Type", "Patient_ID"]


@st.cache_data(show_spinner="Lecture du CSV…", max_entries=2)
def lire_csv(raw_csv):
    """Lit un CSV en essayant plusieurs séparateurs et encodages. Même résultat qu'avant, mis en cache
    pour ne pas relire le fichier à chaque interaction. Rend (tableau, séparateur, encodage)."""
    parsed_candidates = []
    parsing_errors = []
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        for separator in (";", ",", "\\t", "|"):
            try:
                parsed = pd.read_csv(io.BytesIO(raw_csv), sep=separator, engine="python", encoding=encoding)
                if len(parsed.columns) > 0 and len(parsed) > 0:
                    parsed_candidates.append((parsed, separator, encoding))
            except Exception as parse_error:
                parsing_errors.append(f"{separator!r}/{encoding}: {parse_error}")
    if not parsed_candidates:
        raise ValueError(
            "Impossible de lire ce CSV. Vérifiez les séparateurs, "
            "les guillemets et la structure des lignes. "
            + " | ".join(parsing_errors[:3])
        )
    return max(parsed_candidates, key=lambda item: (item[0].shape[1], item[0].shape[0]))


def colonnes_manquantes(tableau):
    """Ce qui manque à un CSV pour que toutes les pages fonctionnent (liste de textes, vide si tout y est)."""
    manque = [c for c in COLONNES_REQUISES if c not in tableau.columns]
    if not numeric_columns(tableau):
        manque.append("au moins une colonne numérique")
    return manque


def activer_dataset(tableau, nom):
    st.session_state["active_df"] = tableau
    st.session_state["active_dataset_name"] = nom
    st.session_state["active_version"] += 1


def page_dataset():
    """Importer un CSV pour les pages d'analyse, ou revenir au jeu officiel."""
    with st.container():
        uploaded = st.file_uploader(
            "Choisir un fichier CSV depuis votre ordinateur",
            type=["csv"],
            key="allergylab_csv_import"
        )

        if uploaded is not None:
            try:
                candidate, detected_separator, detected_encoding = lire_csv(uploaded.getvalue())
                st.caption(f"Format détecté : séparateur {detected_separator!r} · encodage {detected_encoding}")
                st.write("Aperçu du fichier :")
                show_table(candidate.head(10), use_container_width=True)
                st.caption(f"{len(candidate)} lignes · {len(candidate.columns)} colonnes")

                manque = colonnes_manquantes(candidate)
                if manque:
                    st.warning(
                        "Ce fichier ne peut pas être activé : il manque " + ", ".join(manque)
                        + ". Les pages d'analyse en ont besoin. Ajoutez ces colonnes au CSV, "
                        "ou gardez le jeu officiel."
                    )
                if st.button("Activer ce nouveau dataset", type="primary", disabled=bool(manque)):
                    activer_dataset(candidate, uploaded.name)
                    st.rerun()
            except Exception as exc:
                st.error(f"Erreur de lecture du CSV : {exc}")

        if st.session_state["active_df"] is not None:
            st.success(
                "Dataset actif : "
                + str(st.session_state["active_dataset_name"])
            )
            if st.button("Revenir au dataset original"):
                activer_dataset(None, None)
                st.rerun()


def calculs_du_jeu():
    """Le tableau actif et les indicateurs qui en dépendent, calculés une seule fois par jeu (et non à chaque clic).
    Mémorisé dans la session, avec le numéro du jeu comme clé : les chiffres affichés sont ceux d'avant."""
    memo = st.session_state.get("calculs")
    if memo is not None and memo["version"] == st.session_state["active_version"]:
        return memo
    tableau = st.session_state["active_df"]
    if tableau is None:
        tableau = get_df()
    dico = get_dict()
    memo = {
        "version": st.session_state["active_version"],
        "df": tableau,
        "dictionary": dico,
        "num_cols": numeric_columns(tableau),
        "quality_df": data_quality(tableau, dico),
        "chip_counts": tableau["Chip_Type"].value_counts() if "Chip_Type" in tableau.columns else pd.Series(dtype=int),
        "n_patients": int(tableau["Patient_ID"].nunique()) if "Patient_ID" in tableau.columns else len(tableau),
        "completion": 100 * tableau.notna().sum().sum() / max(1, tableau.shape[0] * tableau.shape[1]),
    }
    st.session_state["calculs"] = memo
    return memo


try:
    _calculs = calculs_du_jeu()
except Exception as e:
    st.error(f"Chargement impossible. Vérifie que l'application est lancée depuis le dépôt : {e}")
    st.stop()

df = _calculs["df"]
dictionary = _calculs["dictionary"]
num_cols = _calculs["num_cols"]
quality_df = _calculs["quality_df"]
chip_counts = _calculs["chip_counts"]
n_patients = _calculs["n_patients"]
completion = _calculs["completion"]

# Session state
for key, default in {
    "chat_messages": [],
    "analysis_history": [],
    "chat_input": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


PAGES = {
    "Accueil": "Vue générale du laboratoire",
    "Assistant IA": "Posez vos questions au copilote",
    "Jeu de données": "Importer un CSV, revenir au jeu officiel",
    "Exploration": "Parcourir les variables du dataset",
    "Questionnaire d’analyse": "Construire une analyse guidée",
    "Qualité des données": "Complétude et valeurs particulières",
    "Statistiques": "Descriptifs et distributions",
    "Comparaison des puces": "Comparer les groupes de puces",
    "Corrélations": "Explorer les associations",
    "Machine Learning": "Analyses exploratoires non diagnostiques",
    "Historique": "Retrouver les analyses effectuées",
}


def aller_a(page):
    """Change de page depuis un bouton (appelé avant le rendu suivant)."""
    st.session_state["navigation"] = page


dataset_officiel = st.session_state["active_df"] is None
nom_dataset = "Jeu officiel" if dataset_officiel else str(st.session_state["active_dataset_name"])

with st.sidebar:
    st.markdown(f"""
    <div class="brand"><img alt="" src="data:image/svg+xml;base64,{LOGO_B64}">
      <div><div class="brand-name">AllergyLab</div><div class="brand-sub">Research workspace</div></div></div>""",
                unsafe_allow_html=True)
    selected = st.radio("Navigation", list(PAGES.keys()), key="navigation", label_visibility="collapsed",
                        help=None)
    st.divider()
    marque = "" if dataset_officiel else " class='alt'"
    st.markdown(
        f"<div class='ds'><i{marque}></i><b>{escape(nom_dataset)}</b> actif<br>"
        f"{n_patients:,} patients · {len(df.columns)} variables<br>"
        f"{len(chip_counts)} types de puces</div>".replace(",", " "), unsafe_allow_html=True)
    st.markdown("<div class='small-muted' style='margin-top:14px'>Résultats exploratoires : ils ne constituent pas un avis médical.</div>",
                unsafe_allow_html=True)


def page_header(kicker, title, desc):
    st.markdown(f"<div class='eyebrow'>{escape(kicker)}</div><h1 class='page-title'>{escape(title)}</h1>"
                f"<div class='page-desc'>{escape(desc)}</div>", unsafe_allow_html=True)


def rendu_reponse(msg):
    """HTML d'une réponse de l'agent. Présentation seulement : la valeur et la justification sont recopiées telles quelles
    (seulement protégées pour l'affichage HTML). Si la réponse n'est pas un dictionnaire complet, on la montre en texte."""
    brut = msg.get("brut")
    if not (isinstance(brut, dict) and {"statut", "valeur", "justification"} <= brut.keys() and brut["statut"] in ("reponse", "abstention")):
        return "<div class='read'>" + escape(str(msg["content"])).replace("\n", "<br>") + "</div>"
    justification = escape(str(brut["justification"]))
    if brut["statut"] == "abstention":
        return ("<div class='read abst'><span class='statut'>Abstention</span><br>"
                f"L'agent ne peut pas conclure.<br><br>{justification}</div>")
    valeur = escape(str(brut["valeur"]))
    return ("<div class='read'><span class='statut'>Réponse</span>"
            f"<span class='valeur'>{valeur}</span>{justification}</div>")


AIDE_EXCLUSION = ("Cette option s'écarte de la règle de l'équipe : les -1 sont comptés et signalés, jamais interprétés ni exclus, "
                  "et le 9 n'est exclu que pour les colonnes de COLONNES_9_NON_RENSEIGNE. Ici les deux codes sont retirés de toutes "
                  "les variables choisies. Décochée par défaut ; à cocher seulement si le protocole le justifie.")


def save_history(kind, params, result_summary):
    st.session_state.analysis_history.insert(0, {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": kind, "paramètres": str(params), "résumé": str(result_summary)
    })


def show_kpis():
    cols = st.columns(4)
    puces = " · ".join(str(p) for p in chip_counts.index) if len(chip_counts) else "aucune colonne Chip_Type"
    data = [
        ("Patients", f"{n_patients:,}".replace(",", " "), "identifiants distincts" if "Patient_ID" in df.columns else "lignes du tableau"),
        ("Variables", str(len(df.columns)), "colonnes disponibles"),
        ("Types de puces", str(len(chip_counts)), puces),
        ("Cellules renseignées", f"{completion:.1f} %", "toutes colonnes ; un vide peut vouloir dire « non mesuré »"),
    ]
    for c, (label, value, foot) in zip(cols, data):
        c.markdown(f"<div class='kpi'><div class='kpi-label'>{label}</div><div class='kpi-value'>{value}</div>"
                   f"<div class='kpi-foot'>{escape(foot)}</div></div>", unsafe_allow_html=True)

# ---------- Pages ----------
if selected == "Accueil":
    st.markdown("""<div class="hero"><div class="eyebrow">Plateforme d’analyse · version équipe</div>
    <h1>Bienvenue dans votre laboratoire.</h1>
    <p>Explorez les données, lancez des analyses reproductibles et gardez une trace claire de vos résultats.</p></div>""", unsafe_allow_html=True)
    show_kpis()
    st.write("")
    left, right = st.columns([1.15, .85])
    with left:
        with st.container(border=True):
            st.markdown("<div class='panel-title'>Répartition des patients par puce</div><div class='panel-sub'>Effectifs présents dans le jeu de données actif</div>", unsafe_allow_html=True)
            if len(chip_counts):
                fig = px.bar(chip_counts.rename_axis("Puce").reset_index(name="Patients"), x="Puce", y="Patients",
                             text_auto=True, color="Puce")
                fig.update_layout(showlegend=False)
                show_chart(fig)
            else:
                st.info("Pas de colonne Chip_Type dans ce jeu de données.")
    with right:
        with st.container(border=True):
            st.markdown("<div class='panel-title'>Accès rapide</div><div class='panel-sub'>Choisissez votre prochaine action</div>", unsafe_allow_html=True)
            for label, target in [
                ("Poser une question à l’assistant", "Assistant IA"),
                ("Construire une analyse guidée", "Questionnaire d’analyse"),
                ("Contrôler la qualité des données", "Qualité des données"),
                ("Explorer les corrélations", "Corrélations"),
            ]:
                st.button(label, width="stretch", key=f"acces_{target}", on_click=aller_a, args=(target,))
        if st.session_state.analysis_history:
            with st.container(border=True):
                st.markdown("<div class='panel-title'>Dernières analyses</div>", unsafe_allow_html=True)
                show_table(pd.DataFrame(st.session_state.analysis_history)[["date", "type"]].head(5), hide_index=True)
    st.info("Important : les valeurs -1 et 9 sont conservées. Leur signification doit être vérifiée colonne par colonne avant toute interprétation clinique.")

elif selected == "Assistant IA":
    page_header("COPILOTE SCIENTIFIQUE", "Assistant AllergyLab", "Un espace de dialogue pour interroger le jeu de données et comprendre les résultats. Les calculs sont réalisés par les outils Python de l’agent, la réponse indique sa justification.")
    if not dataset_officiel:
        st.warning("Un CSV importé est actif dans les pages d’analyse, mais l’assistant interroge toujours le jeu officiel du dépôt. Ses réponses ne portent donc pas sur le fichier importé.")
    suggestions = [
        "Combien de patients sont présents dans le dataset ?",
        "Quelle est la répartition des patients entre les trois puces ?",
        "Quelles variables cliniques sont disponibles ?",
        "Quels sont les points de vigilance concernant les valeurs -1 et 9 ?",
    ]
    st.caption("Exemples de questions")
    scols = st.columns(2)
    for i, q in enumerate(suggestions):
        # Un clic ne lance rien : il demande confirmation, car envoyer la question appelle le modèle (payant).
        if scols[i % 2].button(q, key=f"suggest_{i}", width="stretch"):
            st.session_state["question_a_confirmer"] = q
    pending = None
    a_confirmer = st.session_state.get("question_a_confirmer")
    if a_confirmer:
        with st.container(border=True):
            st.markdown(f"<div class='panel-sub'>{escape(a_confirmer)}</div>", unsafe_allow_html=True)
            st.warning("Cette question appelle le modèle (coût de quelques centimes). Envoyer ?")
            b_envoyer, b_annuler = st.columns(2)
            if b_envoyer.button("Envoyer", type="primary", key="confirmer_envoyer", width="stretch"):
                st.session_state.pop("question_a_confirmer", None)
                st.session_state.chat_messages.append({"role": "user", "content": a_confirmer})
                pending = a_confirmer
            if b_annuler.button("Annuler", key="confirmer_annuler", width="stretch"):
                st.session_state.pop("question_a_confirmer", None)
                st.rerun()
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-user'>{escape(str(msg['content']))}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-ai'><img alt='' src='data:image/svg+xml;base64,{LOGO_B64}'>{rendu_reponse(msg)}</div>", unsafe_allow_html=True)
    question = st.chat_input("Écrivez votre question sur les données…")
    if question or pending:
        q = question or pending
        if question:
            st.session_state.chat_messages.append({"role": "user", "content": q})
        with st.spinner("L’agent analyse votre question…"):
            brut = None
            try:
                from equipe.agent import repondre
                brut = repondre(q)  # la réponse brute, gardée telle quelle
                answer = str(brut)
            except Exception as e:
                answer = (f"Je n’ai pas pu interroger l’agent : {e}\n\n"
                          "Vérifiez la configuration ModeleKit et les dépendances. "
                          "Les pages statistiques restent utilisables sans appel IA.")
        st.session_state.chat_messages.append({"role": "assistant", "content": answer, "brut": brut})
        st.rerun()
    if st.session_state.chat_messages and st.button("Effacer cette conversation"):
        st.session_state.chat_messages = []
        st.rerun()
    st.caption("Confidentialité : ne saisissez pas d’informations directement identifiantes. L’agent actuel est un CodeAgent qui exécute du code sur cette machine ; réservez son usage à l’équipe tant que cette exécution n’a pas été sécurisée.")

elif selected == "Jeu de données":
    page_header("DONNÉES", "Jeu de données", "Importez un fichier CSV pour les pages d’analyse, ou revenez au jeu officiel. Le fichier du dépôt n’est jamais modifié.")
    page_dataset()
elif selected == "Exploration":
    page_header("EXPLORER","Exploration des données","Parcourez les variables et leurs valeurs sans modifier le fichier source.")
    c1,c2=st.columns([1,1])
    with c1:
        variable=st.selectbox("Variable à explorer",list(df.columns))
    with c2:
        filter_chip=st.selectbox("Périmètre",["Toutes les puces"]+list(chip_counts.index.astype(str)))
    view=df if filter_chip=="Toutes les puces" or "Chip_Type" not in df else df[df["Chip_Type"].astype(str)==filter_chip]
    s=view[variable]
    a,b,c=st.columns(3)
    a.metric("Lignes",len(view)); b.metric("Valeurs renseignées",int(s.notna().sum())); c.metric("Valeurs absentes",int(s.isna().sum()))
    if pd.api.types.is_numeric_dtype(s):
        show_chart(px.histogram(pd.DataFrame({"Valeur":s.dropna()}),x="Valeur",nbins=40,
                                     title=f"Distribution — {variable}"),use_container_width=True)
        st.write("Résumé rapide")
        show_table(s.describe().to_frame("Valeur").T,use_container_width=True)
        st.write({"Code -1":int((s==-1).sum()),"Code 9":int((s==9).sum())})
    else:
        counts=s.astype("string").fillna("∅").value_counts().head(40)
        show_chart(px.bar(counts.rename_axis("Modalité").reset_index(name="Effectif"),
                               x="Modalité",y="Effectif"),use_container_width=True)
    with st.expander("Voir un aperçu tabulaire (premières lignes)"):
        show_table(view[[variable]].head(100),use_container_width=True)

elif selected == "Questionnaire d’analyse":
    page_header("PARCOURS GUIDÉ","Construire une analyse","Répondez à quelques questions : AllergyLab prépare l’analyse, affiche sa méthode et vous laisse contrôler les paramètres avant exécution.")
    with st.form("analysis_builder"):
        st.markdown("<div class='panel-title'>1 · Quel est votre objectif ?</div>",unsafe_allow_html=True)
        objective=st.selectbox("Type d’analyse",[
            "Statistiques descriptives","Distribution d’une variable","Comparer les puces",
            "Corrélations entre variables","PCA exploratoire","Clustering exploratoire",
            "Détection d’observations atypiques","Qualité des données"
        ])
        st.markdown("<div class='panel-title'>2 · Quelles données souhaitez-vous étudier ?</div>",unsafe_allow_html=True)
        variable=st.selectbox("Variable principale",num_cols if num_cols else list(df.columns))
        variables=st.multiselect("Variables complémentaires (si nécessaire)",num_cols)
        group=st.selectbox("Groupe de comparaison",["Chip_Type"] if "Chip_Type" in df else list(df.columns))
        st.markdown("<div class='panel-title'>3 · Quelles précautions appliquer ?</div>",unsafe_allow_html=True)
        exclude_special=st.checkbox("Pour cette analyse exploratoire seulement, exclure les codes -1 et 9",value=False,
                                help=AIDE_EXCLUSION)
        st.caption("Par défaut, les codes sont conservés et signalés. Cochez cette option uniquement si votre protocole le justifie.")
        submitted=st.form_submit_button("Préparer et exécuter l’analyse",type="primary",width="stretch")
    if submitted:
        try:
            if objective=="Statistiques descriptives":
                result=descriptive_statistics(df,variable); st.json(result); save_history(objective,{"variable":variable},result)
            elif objective=="Distribution d’une variable":
                vals=pd.to_numeric(df[variable],errors="coerce")
                if exclude_special: vals=vals.mask(vals.isin([-1,9]))
                fig=px.histogram(pd.DataFrame({"Valeur":vals.dropna()}),x="Valeur",nbins=40)
                show_chart(fig,use_container_width=True); save_history(objective,{"variable":variable},f"{vals.notna().sum()} valeurs")
            elif objective=="Comparer les puces":
                result=compare_groups(df,variable,group); show_table(result,use_container_width=True)
                show_chart(px.box(df,x=group,y=variable),use_container_width=True)
                save_history(objective,{"variable":variable,"groupe":group},result.to_dict())
                st.info("Comparaison descriptive : aucun test de significativité n’est réalisé.")
            elif objective=="Corrélations entre variables":
                cols=list(dict.fromkeys([variable]+variables))
                if len(cols)<2: st.warning("Ajoutez au moins une variable complémentaire.")
                else:
                    corr=correlation_matrix(df,cols,"spearman")
                    show_chart(px.imshow(corr,text_auto=".2f",zmin=-1,zmax=1,color_continuous_scale="RdBu_r"),use_container_width=True)
                    show_table(corr,use_container_width=True); save_history(objective,{"variables":cols},corr.to_dict())
            elif objective=="PCA exploratoire":
                cols=list(dict.fromkeys([variable]+variables))
                coords,var,meta=pca_projection(df,cols,exclude_special)
                show_chart(px.scatter(coords,x="PC1",y="PC2"),use_container_width=True)
                st.write("Variance expliquée :",var); st.write(meta); save_history(objective,{"variables":cols},meta)
            elif objective=="Clustering exploratoire":
                cols=list(dict.fromkeys([variable]+variables))
                if len(cols)<2: st.warning("Sélectionnez au moins deux variables.")
                else:
                    labels,meta=clustering(df,cols,3,exclude_special)
                    show_chart(px.histogram(labels,x="cluster"),use_container_width=True)
                    st.write(meta); save_history(objective,{"variables":cols},meta)
            elif objective=="Détection d’observations atypiques":
                cols=list(dict.fromkeys([variable]+variables))
                if len(cols)<2: st.warning("Sélectionnez au moins deux variables.")
                else:
                    labels,meta=anomaly_detection(df,cols,0.03,exclude_special)
                    show_table(labels["statut"].value_counts().to_frame("Effectif")); st.write(meta)
                    save_history(objective,{"variables":cols},meta)
            elif objective=="Qualité des données":
                show_table(quality_df,use_container_width=True); save_history(objective,{},f"{len(quality_df)} colonnes auditées")
        except Exception as e:
            st.error(f"Analyse non exécutée : {e}")

elif selected == "Qualité des données":
    page_header("DATA QUALITY","Qualité des données","Repérez les variables incomplètes et les codes particuliers avant toute analyse.")
    st.warning("Une valeur absente dans une colonne de dosage peut correspondre à une puce qui ne mesure pas l’allergène. La complétude brute ne suffit donc pas à conclure.")
    q=quality_df.copy()
    if "bloc" in q.columns:
        bloc=st.radio("Bloc de variables",["Tous","clinique","dosage"],horizontal=True)
        if bloc!="Tous": q=q[q["bloc"]==bloc]
    a,b,c=st.columns(3)
    a.metric("Colonnes affichées",len(q)); b.metric("Complétude moyenne",f"{q['completude_pct'].mean():.1f}%" if len(q) else "—")
    c.metric("Colonnes entièrement vides",int((q["renseignes"]==0).sum()))
    show_chart(px.bar(q.sort_values("completude_pct").head(35),x="completude_pct",y="colonne",
                           orientation="h",title="Variables les moins complètes"),use_container_width=True)
    show_table(q,use_container_width=True,hide_index=True)
    st.download_button("Exporter le rapport qualité (CSV)",q.to_csv(index=False).encode("utf-8-sig"),
                       "allergylab_qualite_donnees.csv","text/csv")

elif selected == "Statistiques":
    page_header("STATISTIQUES","Statistiques descriptives","Décrivez une variable et visualisez sa distribution.")
    variable=st.selectbox("Variable numérique",num_cols)
    try:
        stats=descriptive_statistics(df,variable)
        cards=st.columns(4)
        for c,label,key in zip(cards,["Moyenne","Médiane","Écart-type","Effectif"],["moyenne","mediane","ecart_type","n_renseignes"]):
            val=stats[key]; c.metric(label, f"{val:.4g}" if isinstance(val,(float,int)) and val is not None else "—")
        st.markdown("<div class='panel'><div class='panel-title'>Détail statistique</div></div>",unsafe_allow_html=True)
        st.json({k:v for k,v in stats.items() if k not in ["moyenne","mediane","ecart_type","n_renseignes"]})
        s=pd.to_numeric(df[variable],errors="coerce").dropna()
        left,right=st.columns(2)
        with left: show_chart(px.histogram(pd.DataFrame({"Valeur":s}),x="Valeur",nbins=40,title="Histogramme"))
        with right: show_chart(px.box(pd.DataFrame({"Valeur":s}),y="Valeur",title="Boîte à moustaches"))
        st.warning(stats["avertissement"])
        save_history("Statistiques descriptives",{"variable":variable},stats)
    except Exception as e: st.error(str(e))

elif selected == "Comparaison des puces":
    page_header("COMPARAISON","Comparer les puces","Comparez les distributions observées sans confondre description et significativité statistique.")
    variable=st.selectbox("Variable numérique",num_cols)
    try:
        result=compare_groups(df,variable)
        show_table(result,use_container_width=True,hide_index=True)
        if "Chip_Type" in df:
            show_chart(px.box(df,x="Chip_Type",y=variable,color="Chip_Type",
                                   color_discrete_sequence=["#197d78","#4d8ea0","#a6c7c5"]),use_container_width=True)
        st.info("Les puces peuvent mesurer des ensembles différents. Vérifiez le dictionnaire de mesure et la comparabilité avant toute conclusion.")
        save_history("Comparaison des puces",{"variable":variable},result.to_dict())
    except Exception as e:
        st.error(f"Comparaison impossible : {e}. Cette page demande une colonne Chip_Type et une variable numérique dans le jeu de données actif.")

elif selected == "Corrélations":
    page_header("ASSOCIATIONS","Corrélations","Explorez les associations entre variables. Une corrélation ne démontre pas une causalité.")
    chosen=st.multiselect("Variables numériques",num_cols,default=num_cols[:min(6,len(num_cols))])
    method=st.selectbox("Coefficient",["spearman","pearson","kendall"])
    if len(chosen)>=2:
        corr=correlation_matrix(df,chosen,method)
        show_chart(px.imshow(corr,text_auto=".2f",zmin=-1,zmax=1,color_continuous_scale="RdBu_r",
                                  title=f"Matrice {method.title()}"),use_container_width=True)
        show_table(corr,use_container_width=True)
        st.download_button("Exporter la matrice CSV",corr.to_csv().encode("utf-8-sig"),
                           "allergylab_correlations.csv","text/csv")
        save_history("Corrélations",{"variables":chosen,"méthode":method},corr.to_dict())
    else: st.info("Choisissez au moins deux variables.")

elif selected == "Machine Learning":
    page_header("LABORATOIRE ML","Machine Learning exploratoire","PCA, regroupements et détection de profils atypiques. Ces résultats ne sont ni des diagnostics ni des catégories médicales validées.")
    st.warning("Les résultats dépendent des variables sélectionnées, des valeurs manquantes, de la standardisation et du traitement explicite des codes particuliers.")
    chosen=st.multiselect("Variables numériques",num_cols,default=num_cols[:min(5,len(num_cols))])
    exclude=st.checkbox("Exclure les codes -1 et 9 pour cette analyse",value=False,help=AIDE_EXCLUSION)
    method=st.selectbox("Méthode",["PCA","Clustering KMeans","Détection d'anomalies"])
    k=st.slider("Nombre de clusters",2,8,3) if method=="Clustering KMeans" else 3
    contamination=st.slider("Taux d'anomalies attendu",0.01,0.20,0.03,0.01) if method=="Détection d'anomalies" else .03
    if st.button("Lancer l'analyse",type="primary",disabled=len(chosen)<2):
        try:
            if method=="PCA":
                coords,var,meta=pca_projection(df,chosen,exclude)
                show_chart(px.scatter(coords,x="PC1",y="PC2",title="Projection des observations"),use_container_width=True)
                st.write("Variance expliquée par composante :",[round(float(v),4) for v in var])
            elif method=="Clustering KMeans":
                labels,meta=clustering(df,chosen,k,exclude)
                show_chart(px.histogram(labels,x="cluster",title="Effectif par cluster"),use_container_width=True)
            else:
                labels,meta=anomaly_detection(df,chosen,contamination,exclude)
                show_chart(px.histogram(labels,x="statut",title="Observations signalées"),use_container_width=True)
            st.write("Périmètre et paramètres :",meta)
            save_history(method,{"variables":chosen,"exclusion_codes":exclude},meta)
        except Exception as e: st.error(str(e))

elif selected == "Historique":
    page_header("TRAÇABILITÉ","Historique des analyses","Retrouvez les opérations effectuées dans cette session.")
    if not st.session_state.analysis_history:
        st.info("Aucune analyse enregistrée dans cette session. Les analyses lancées depuis les pages statistiques et analytiques apparaîtront ici.")
    else:
        hist=pd.DataFrame(st.session_state.analysis_history)
        show_table(hist,use_container_width=True,hide_index=True)
        st.download_button("Exporter l’historique CSV",hist.to_csv(index=False).encode("utf-8-sig"),
                           "allergylab_historique.csv","text/csv")
        if st.button("Vider l’historique de cette session"):
            st.session_state.analysis_history=[]; st.rerun()

st.divider()
st.markdown("<div class='small-muted'>AllergyLab · Outil d’aide à l’exploration scientifique · Vérifiez les hypothèses, les codes et les périmètres avant publication.</div>",unsafe_allow_html=True)
