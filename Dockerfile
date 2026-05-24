FROM python:3.12-slim

# Install Filebeat
RUN apt-get update && apt-get install -y curl && \
    curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.13.0-amd64.deb && \
    dpkg -i filebeat-8.13.0-amd64.deb && \
    rm filebeat-8.13.0-amd64.deb && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./
COPY filebeat/filebeat.yml /etc/filebeat/filebeat.yml

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 8000

# Start filebeat in background, then run the app in foreground
CMD bash -c "filebeat -e -c /etc/filebeat/filebeat.yml &>/dev/null & exec python -u main.py"

