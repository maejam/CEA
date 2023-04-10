FROM python:3.8-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /home/app/CEA_mongo

# Copier le fichier init_db__if_empty.py dans le container
COPY init_db__if_empty.py /home/app/CEA_mongo/init_db__if_empty.py

# Copier le contenu du dossier data dans le container
COPY data /home/app/CEA_mongo/data

CMD ["python", "init_db__if_empty.py"]