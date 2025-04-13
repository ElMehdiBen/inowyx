from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os

app = FastAPI(
    title="Assistants API",
    description="An API for managing assistants within Onyx",
    version="1.0.0",
    servers=[{"url": "http://localhost:8080"}]
)

router = APIRouter()

if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "API_KEY_SECRET"

llm = ChatOpenAI(model="gpt-4o-mini")
non_conformite_db = """ID\tDate\tMois\tObjet\tDescription courte\tGravité\tDétecté par\tStatut
NC01\t2025-01-10\tJanvier\tTeneur hors spécification\tTeneur matière active non conforme sur 3 lots.\tCritique\tLaboratoire Contrôle\tRésolu
NC02\t2025-01-22\tJanvier\tRupture de stock\tComposant principal manquant, arrêt de ligne 4h.\tMoyenne\tLogistique\tRésolu
NC03\t2025-02-05\tFévrier\tSurdosage\tMachine mal calibrée, 15% en excès de dosage.\tCritique\tSuperviseur Production\tEn cours
NC04\t2025-02-17\tFévrier\tRetard de livraison fournisseur\tLivraison avec 3 jours de retard.\tMineure\tAchats\tRésolu
NC05\t2025-03-03\tMars\tOmission de traçabilité\tÉchantillons non tracés sur ligne 2.\tÉlevée\tQualité (QL-027)\tClôturé
NC06\t2025-03-15\tMars\tAbsence de relevé température\tDonnées manquantes sur 2h de production.\tÉlevée\tQualité\tEn cours
NC07\t2025-04-02\tAvril\tOmission de vérification des équipements\tContrôles avant lancement non effectués.\tCritique\tSuperviseur Production\tEn cours
NC08\t2025-04-04\tAvril\tRetard traitement réclamation client\t48h de délai au-delà de la norme.\tÉlevée\tService Client\tRésolu
NC09\t2025-04-08\tAvril\tMauvais étiquetage\tMauvais étiquetage sur 12 lots produits.\tMoyenne\tContrôle Qualité\tEn cours
"""

actions_correctives_db = """ID\tAction Corrective\tDate Mise en Place\tEfficacité confirmée ?\tCommentaire
NC01\tAjustement process + double vérification\t2025-01-12\t✅ Oui\tNon-conformité non réapparue
NC02\tRévision gestion stock + seuil alerte\t2025-01-23\t✅ Oui\tProblème évité depuis
NC03\tRecalibrage équipement + alarme\t2025-02-06\t❌ En observation\tNon-conformité similaire en attente de validation
NC05\tFormation express + checklist obligatoire\t2025-03-10\t✅ Oui\t100% traçabilité depuis
NC06\tMise à jour procédure + supervision renforcée\t2025-03-18\t❌ Trop récent\tAudits hebdomadaires en cours
NC07\tFormation, alerte système, audit hebdo\t2025-04-03\t❌ Trop récent\tRésultats d’audit en attente
NC08\tProcédure accélérée + alerte réclamation\t2025-04-05\t✅ Oui\tDélais de réponse respectés depuis
"""

responsables_causes_db = """ID\tResponsable\tPoste / ID\tCause identifiée
NC01\tTechnicien contrôle\tLAB-112\tErreur de mesure manuelle
NC02\tChef logistique\tLOG-021\tMauvais paramétrage des seuils d’alerte
NC03\tOpérateur machine\tPROD-008\tDéfaut de calibration automatique
NC05\tOpérateur ligne 2\tQL-027\tMauvaise prise en main du nouveau logiciel
NC06\tAgent qualité\tQL-051\tOubli relevé manuel suite à changement de poste
NC07\tChef d'équipe prod\tPROD-004\tContrôle ignoré dans planning
NC08\tAgent SAV\tSAV-019\tRéclamations non priorisées
NC09\tÉquipe étiquetage\tETIQ-003\tMauvaise version de template utilisée
"""

tool = {"type": "web_search_preview"}
llm_with_tools = llm.bind_tools([tool])

@router.post("/query_table", summary="Query Table Data", description="Query the specified database for information.")
async def query_table_based_on_db(db_name: str, input: str):

    prompt_non_conformite_db = {
            "non_conformite": ChatPromptTemplate.from_messages([
                ("system", f"You are a helpful assistant that will help the user to get information based on the following database markdown, Format the answer after sending it back in a human readable way, the delimiter is '\t' in {non_conformite_db}"),
                ("human", "{input}")
            ]),
            "actions_correctives": ChatPromptTemplate.from_messages([
                ("system", f"You are a helpful assistant that will help the user to get information based on the following database markdown, Format the answer after sending it back in a human readable way, the delimiter is '\t' in {actions_correctives_db}"),
                ("human", "{input}")
            ]),
    }
    prompt_actions_correctives_db = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"You are a helpful assistant that will help the user to get information based on the following database markdown, "
                f"Format the answer after sending it back in a human readable way, the delimiter is '\t' in {actions_correctives_db}",
            ),
            ("human", "{input}"),
        ]
    )
    prompt_responsables_causes_db = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"You are a helpful assistant that will help the user to get information based on the following database markdown,"
                f" Format the answer after sending it back in a human readable way, the delimiter is '\t' in {responsables_causes_db}",
            ),
            ("human", "{input}"),
        ]
    )
    tools_dict = dict(
        non_conformite=prompt_non_conformite_db,
        actions_correctives=prompt_actions_correctives_db,
        responsables_causes=prompt_responsables_causes_db
    )
    chain_for_query = tools_dict.get(db_name) | llm
    print(f"using {tools_dict.get(db_name)}")
    response = chain_for_query.invoke(
        {
            "input": input,
        }
    )
    print(f"chain_for_query {chain_for_query}")
    print(f"response {response}")
    return {"message": response.content}


@router.post("/query_internet", summary="Query Internet", description="Perform a web search based on user input.")
async def query_internet(input: str):
    prompt_search_internet = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant do web search based on the user input and return the best results following the internet search",
            ),
            ("human", "{input}"),
        ]
    )
    chain_for_web_search = prompt_search_internet | llm_with_tools

    response = chain_for_web_search.invoke(
        {
            "input": input,
        })
    print(f"chain_for_query {chain_for_web_search}")
    print(f"response {response}")
    return {"message": response.content}

# Exemples de questions que l’utilisateur peut poser à l’agent :
# Quelles non-conformités critiques ont été détectées en mars ?
#
# Qui est responsable de la non-conformité NC05 ?
#
# Quelles actions correctives ont été mises en place en avril ?
#
# Est-ce que l’action corrective de la NC03 est efficace ?
#
# Rédige un rapport de non-conformité pour l’incident du 2 avril.
#
# Combien de non-conformités sont encore en cours ?
#
# Montre-moi les causes les plus fréquentes.

