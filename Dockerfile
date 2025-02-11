FROM python:3.9-slim
RUN apt-get update && apt-get install -y nodejs npm
COPY package*.json ./
RUN npm install
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .