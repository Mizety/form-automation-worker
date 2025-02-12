FROM mcr.microsoft.com/playwright/python:v1.50.0-noble
 
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
COPY . .

RUN playwright install

 
