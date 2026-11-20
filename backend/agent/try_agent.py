"""Essai de l'agent dans le terminal :  python -m backend.agent.try_agent"""
import uuid

from langgraph.types import Command

from backend.agent.graph import graph

questions = [
    "Quel est le délai d'exécution prévu dans l'appel d'offres AO-2026-0002 ?",
    "Combien d'appels d'offres y a-t-il par secteur ?",
    "Envoie un résumé de l'appel d'offres AO-2026-0001 à equipe@exemple.tn",
]
for q in questions:
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}   # un fil de conversation par question
    result = graph.invoke({"question": q}, config)
    print(f"\n❓ {q}\n➡ route : {result.get('route')}")
    if "__interrupt__" in result:                                # le graphe est en pause
        draft = result["__interrupt__"][0].value["draft"]
        print(f"✉ Brouillon pour {draft['to']} : {draft['subject']}\n{draft['body']}")
        choice = input("Valider l'envoi ? (o/n) ")
        result = graph.invoke(Command(resume="approve" if choice == "o" else "reject"), config)
    print(f"💬 {result.get('answer')}")