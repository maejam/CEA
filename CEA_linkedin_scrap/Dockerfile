FROM node:lts-alpine3.18

WORKDIR /app
COPY . /app
RUN npm install
RUN npm install swagger-ui-express swagger-jsdoc
RUN npm install axios