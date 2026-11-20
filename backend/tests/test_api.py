from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)                 # un "faux navigateur" qui appelle l'API sans serveur réseau


def token(username, password):
    return client.post("/auth/token", data={"username": username, "password": password}).json()["access_token"]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_sans_token_401():
    assert client.get("/tenders").status_code == 401


def test_mauvais_mot_de_passe_401():
    assert client.post("/auth/token", data={"username": "admin", "password": "faux"}).status_code == 401


def test_analyste_ne_peut_pas_valider_403():
    headers = {"Authorization": f"Bearer {token('analyste', 'analyste123')}"}
    r = client.post("/approve", json={"thread_id": "x", "decision": "approve"}, headers=headers)
    assert r.status_code == 403


def test_question_trop_courte_422():
    headers = {"Authorization": f"Bearer {token('analyste', 'analyste123')}"}
    assert client.post("/ask", json={"question": "a"}, headers=headers).status_code == 422