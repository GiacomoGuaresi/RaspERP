# Usa un'immagine base Python
FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file del progetto
COPY . /app

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta Flask (di default è la 5000)
EXPOSE 5000

# Comando per avviare l'app
CMD ["flask", "run", "--host=0.0.0.0"]
