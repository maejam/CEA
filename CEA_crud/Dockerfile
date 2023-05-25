FROM python:3.9

# Créer un dossier /app dans le container
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Copier le contenu des fichier a la a racine, dans le dossier app du container
COPY . /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]