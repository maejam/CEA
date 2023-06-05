FROM ghcr.io/mlflow/mlflow:v2.3.2
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y sqlite3 libsqlite3-dev
RUN /usr/bin/sqlite3 /mlflow/mlruns.db
