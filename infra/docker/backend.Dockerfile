# 1. Point de départ : Python 3.12 en version légère ("slim")
FROM python:3.12-slim

# 2. Pas de fichiers .pyc, et les logs s'affichent tout de suite
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# 3. D'abord les dépendances (cette couche reste en cache tant que requirements.txt ne change pas)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Puis le code (il change souvent : on le copie en dernier)
COPY backend ./backend

# 5. Ne pas tourner en root : si l'application est piratée, l'attaquant a moins de droits
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]