"""Vérifie l'installation point par point : `uv run kit controle`.

Chaque vérification rend des lignes (bon, texte, que_faire). Une ligne en
échec dit ce qui ne va pas, puis quoi faire. La dernière ligne affichée est
RÉUSSITE (code 0) ou ÉCHEC (code 1).
"""

import hashlib
import re
import tempfile
import tomllib

from kit import donnees

RACINE = donnees.RACINE
EQUIPE_VALIDE = re.compile(r"accueil|equipe-[1-9]")

RESTAURER_DONNEES = (
    "restaure le dossier avec « git checkout -- donnees/ », "
    "ou retélécharge l'archive du dépôt."
)
RESTAURER_KIT = (
    "restaure le dossier kit/ avec « git checkout -- kit/ », "
    "ou retélécharge l'archive du dépôt."
)


def empreinte(chemin):
    """Empreinte SHA-256 d'un fichier, en hexadécimal."""
    with open(chemin, "rb") as fichier:
        return hashlib.file_digest(fichier, "sha256").hexdigest()


def lire_attendu(racine):
    """Lit kit/empreintes.toml : empreintes des fichiers et forme du tableau."""
    texte = (racine / "kit" / "empreintes.toml").read_text(encoding="utf-8")
    return tomllib.loads(texte)


def verifier_donnees(racine, attendu):
    """Chaque fichier de donnees/ est présent et a l'empreinte publiée."""
    lignes = []
    for nom, valeur in attendu["fichiers"].items():
        chemin = racine / "donnees" / nom
        if not chemin.is_file():
            lignes.append((False, f"données : donnees/{nom} est absent.", RESTAURER_DONNEES))
        elif empreinte(chemin) != valeur:
            lignes.append((
                False,
                f"données : donnees/{nom} n'a pas l'empreinte publiée. Le fichier a "
                "été modifié, ou ses fins de ligne ont été converties.",
                RESTAURER_DONNEES,
            ))
        else:
            lignes.append((True, f"données : donnees/{nom}, empreinte conforme", None))
    return lignes


def verifier_tableau(racine, attendu):
    """Le tableau se charge et a la forme attendue. Rend la ligne et le tableau."""
    chemin = racine / "donnees" / donnees.NOM_FICHIER
    if not chemin.is_file():
        return (False, "tableau : non chargé, le fichier de données est absent.", RESTAURER_DONNEES), None
    try:
        tableau = donnees.charger(chemin)
    except (ValueError, UnicodeDecodeError) as erreur:
        return (False, f"tableau : il ne se charge pas. {erreur}", RESTAURER_DONNEES), None
    lignes, colonnes = tableau.shape
    forme = attendu["forme"]
    if (lignes, colonnes) != (forme["lignes"], forme["colonnes"]):
        texte = (
            f"tableau : {lignes} lignes et {colonnes} colonnes, "
            f"au lieu de {forme['lignes']} et {forme['colonnes']}."
        )
        return (False, texte, RESTAURER_DONNEES), tableau
    return (True, f"tableau : {lignes} lignes, {colonnes} colonnes", None), tableau


def verifier_dictionnaire(racine, tableau):
    """kit/colonnes.csv décrit les colonnes du tableau, dans l'ordre, avec leur lecture."""
    if tableau is None:
        return False, "dictionnaire des colonnes : non vérifié, le tableau ne se charge pas.", RESTAURER_DONNEES
    chemin = racine / "kit" / "colonnes.csv"
    if not chemin.is_file():
        return False, "dictionnaire des colonnes : kit/colonnes.csv est absent.", RESTAURER_KIT
    dico = donnees.colonnes(chemin)
    probleme = None
    puces = {f"puce_{valeur}" for valeur in tableau[donnees.COLONNE_PUCE].dropna().unique()}
    if list(dico.columns[:3]) != ["colonne", "bloc", "lecture"] or set(dico.columns[3:]) != puces:
        probleme = "ses en-têtes ne sont pas colonne, bloc, lecture et une colonne puce_ par type de puce."
    elif list(dico["colonne"]) != list(tableau.columns):
        probleme = "il ne nomme pas les colonnes du fichier, dans le même ordre."
    else:
        for position, ligne in enumerate(dico.itertuples()):
            bloc = "clinique" if position < donnees.NB_CLINIQUES else "dosage"
            if ligne.bloc != bloc or ligne.lecture != donnees.lecture(tableau[ligne.colonne]):
                probleme = f"la ligne de la colonne {ligne.colonne} ne correspond pas au fichier."
                break
    if probleme:
        return False, f"dictionnaire des colonnes : kit/colonnes.csv, {probleme}", RESTAURER_KIT
    return True, f"dictionnaire des colonnes : {len(dico)} colonnes, cohérent avec le fichier", None


def verifier_equipe(racine):
    """equipe.toml existe et donne un identifiant valide."""
    que_faire = (
        'dans equipe.toml, écris equipe = "accueil" avant la constitution des '
        'équipes, puis equipe = "equipe-N", N étant le numéro de ton équipe (1 à 9).'
    )
    chemin = racine / "equipe.toml"
    if not chemin.is_file():
        return False, "équipe : equipe.toml est absent.", que_faire
    try:
        equipe = tomllib.loads(chemin.read_text(encoding="utf-8")).get("equipe")
    except (tomllib.TOMLDecodeError, UnicodeDecodeError):
        return False, "équipe : equipe.toml ne se lit pas.", que_faire
    if not isinstance(equipe, str) or not EQUIPE_VALIDE.fullmatch(equipe):
        return False, f"équipe : identifiant {equipe!r} non valide.", que_faire
    return True, f"équipe : {equipe}", None


def verifier_traces(racine):
    """Le kit peut écrire dans traces/ : il y crée un fichier provisoire, aussitôt effacé."""
    dossier = racine / "traces"
    try:
        dossier.mkdir(exist_ok=True)
        with tempfile.TemporaryFile(dir=dossier):
            pass
    except OSError:
        return (
            False,
            "traces : le kit ne peut pas écrire dans le dossier traces/.",
            "vérifie que traces/ est un dossier et que le dépôt n'est pas en lecture seule ; "
            "sinon, clone le dépôt à nouveau dans ton dossier personnel, hors de OneDrive ou iCloud.",
        )
    return True, "traces : dossier traces/ inscriptible", None


def afficher(bon, texte, que_faire):
    print(f"  {'OK   ' if bon else 'ÉCHEC'}  {texte}")
    if not bon:
        print(f"         Que faire : {que_faire}")


def controler(racine=RACINE, hors_ligne=False):
    """Fait toutes les vérifications, les affiche, rend 0 (réussite) ou 1 (échec)."""
    print("Contrôle du kit AllergyLab")
    try:
        attendu = lire_attendu(racine)
    except (OSError, tomllib.TOMLDecodeError):
        afficher(False, "données : kit/empreintes.toml est absent ou illisible.", RESTAURER_KIT)
        print("ÉCHEC")
        return 1
    lignes = verifier_donnees(racine, attendu)
    for ligne in lignes:
        afficher(*ligne)
    ligne_tableau, tableau = verifier_tableau(racine, attendu)
    suite = [
        ligne_tableau, verifier_dictionnaire(racine, tableau), verifier_equipe(racine), verifier_traces(racine),
    ]
    for ligne in suite:
        afficher(*ligne)
    lignes += suite
    if hors_ligne:
        print("  --     appel au modèle : sauté (--hors-ligne)")
    else:
        print("  --     appel au modèle : pas encore disponible dans cette version du kit")
    reussi = all(bon for bon, _, _ in lignes)
    print("RÉUSSITE" if reussi else "ÉCHEC")
    return 0 if reussi else 1
