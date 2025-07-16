# AutoGraph Setup-Anleitung

**Installation, Konfiguration und Deployment von AutoGraph**

---

## 📚 Inhaltsverzeichnis

- [⚡ Schnellstart](#-schnellstart)
- [🔧 System-Anforderungen](#-system-anforderungen)
- [📦 Installation](#-installation)
- [🗄️ Datenbank-Setup](#️-datenbank-setup)
- [⚙️ Konfiguration](#️-konfiguration)
- [🚀 Deployment](#-deployment)
- [✅ Validierung](#-validierung)
- [🔧 Troubleshooting](#-troubleshooting)

---

## ⚡ Schnellstart

### 1-Minute Setup für lokale Entwicklung

```bash
# 1. Repository klonen
git clone https://github.com/FBR65/AutoGraph.git
cd AutoGraph

# 2. Python Environment erstellen
python -m venv autograph_env
# Windows
autograph_env\Scripts\activate
# Linux/macOS  
source autograph_env/bin/activate

# 3. Abhängigkeiten installieren
pip install -r requirements.txt

# 4. Neo4j mit Docker starten
docker run -d \
  --name neo4j-autograph \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/autograph123 \
  neo4j:latest

# 5. API Server starten
python -m uvicorn src.autograph.api.server:app --reload --port 8001

# 6. Testen
curl http://localhost:8001/health
```

**🎯 Fertig! AutoGraph läuft unter http://localhost:8001/docs**

---

## 🔧 System-Anforderungen

### 🖥️ Hardware-Anforderungen

| Komponente | Minimum | Empfohlen | Enterprise |
|------------|---------|-----------|------------|
| **CPU** | 2 Cores | 4 Cores | 8+ Cores |
| **RAM** | 4 GB | 8 GB | 16+ GB |
| **Storage** | 5 GB | 20 GB | 100+ GB |
| **GPU** | - | NVIDIA GTX 1060+ | RTX 3070+ |

### 💻 Software-Anforderungen

**Betriebssystem:**
- Windows 10/11 (64-bit)
- Ubuntu 18.04+ / Debian 10+
- macOS 10.15+
- Docker (für Container-Deployment)

**Python:**
- Python 3.8+ (empfohlen: 3.9 oder 3.10)
- pip 21.0+
- venv oder conda

**Datenbank:**
- Neo4j 4.4+ (empfohlen: 5.x)
- Optional: PostgreSQL 12+ (für Metadaten)

**Zusätzliche Tools:**
- Git 2.20+
- curl oder wget (für API-Tests)
- Docker & Docker Compose (optional)

---

## 📦 Installation

### 🐍 Python Environment Setup

#### Mit venv (empfohlen)

```bash
# 1. Projekt-Verzeichnis erstellen
mkdir autograph-project
cd autograph-project

# 2. Repository klonen
git clone https://github.com/FBR65/AutoGraph.git
cd AutoGraph

# 3. Virtual Environment erstellen
python -m venv autograph_env

# 4. Environment aktivieren
# Windows
autograph_env\Scripts\activate
# Linux/macOS
source autograph_env/bin/activate

# 5. pip aktualisieren
pip install --upgrade pip setuptools wheel
```

#### Mit conda

```bash
# 1. Conda Environment erstellen
conda create -n autograph python=3.9
conda activate autograph

# 2. Repository klonen
git clone https://github.com/FBR65/AutoGraph.git
cd AutoGraph

# 3. Zusätzliche Pakete
conda install pip git
```

### 📚 Abhängigkeiten installieren

#### Basis-Installation

```bash
# Core-Abhängigkeiten
pip install -r requirements.txt
```

#### Entwickler-Installation

```bash
# Mit Entwickler-Tools
pip install -r requirements-dev.txt

# Pre-commit hooks installieren
pre-commit install
```

#### GPU-Support (optional)

```bash
# CUDA-fähige PyTorch Installation
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Oder für CPU-only
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 🔍 NLP Models herunterladen

```bash
# spaCy Modelle
python -m spacy download de_core_news_sm
python -m spacy download en_core_web_sm

# NLTK Daten
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Transformers Cache (automatisch beim ersten Lauf)
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('dbmdz/bert-large-cased-finetuned-conll03-english')"
```

---

## 🗄️ Datenbank-Setup

### 🐳 Neo4j mit Docker (empfohlen)

```bash
# 1. Neo4j Container erstellen
docker run -d \
  --name neo4j-autograph \
  --restart unless-stopped \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/autograph123 \
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
  -e NEO4J_apoc_export_file_enabled=true \
  -e NEO4J_apoc_import_file_enabled=true \
  -v neo4j_data:/data \
  -v neo4j_logs:/logs \
  neo4j:5.15

# 2. Warten bis Neo4j bereit ist
echo "Warte auf Neo4j..."
until curl -f http://localhost:7474 > /dev/null 2>&1; do
  printf '.'
  sleep 2
done
echo " Neo4j ist bereit!"

# 3. Browser öffnen (optional)
# http://localhost:7474
# Username: neo4j, Password: autograph123
```

### 🖥️ Native Neo4j Installation

#### Windows

```powershell
# 1. Java 11+ installieren
winget install Microsoft.OpenJDK.11

# 2. Neo4j Community Edition herunterladen
# https://neo4j.com/download-center/#community

# 3. Entpacken und konfigurieren
# Bearbeite conf/neo4j.conf:
# dbms.default_listen_address=0.0.0.0
# dbms.connector.bolt.listen_address=:7687
# dbms.connector.http.listen_address=:7474

# 4. Starten
bin\neo4j.bat console
```

#### Linux (Ubuntu/Debian)

```bash
# 1. Repository hinzufügen
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# 2. Installation
sudo apt update
sudo apt install neo4j

# 3. Service konfigurieren
sudo systemctl enable neo4j
sudo systemctl start neo4j

# 4. Passwort setzen
sudo neo4j-admin set-initial-password autograph123
```

#### macOS

```bash
# 1. Mit Homebrew
brew install neo4j

# 2. Starten
neo4j start

# 3. Passwort setzen (beim ersten Besuch von http://localhost:7474)
```

### 🔧 Datenbank-Konfiguration

```bash
# 1. Verbindung testen
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'autograph123'))
with driver.session() as session:
    result = session.run('RETURN 1 as test')
    print('Neo4j Connection:', result.single()['test'])
driver.close()
"

# 2. AutoGraph-Schemas erstellen
python -c "
from src.autograph.storage.neo4j import Neo4jStorage
storage = Neo4jStorage({
    'uri': 'bolt://localhost:7687',
    'username': 'neo4j',
    'password': 'autograph123'
})
storage.create_constraints()
print('Schemas erstellt!')
"
```

---

## ⚙️ Konfiguration

### 📄 Basis-Konfiguration

Erstellen Sie `config/autograph_config.yaml`:

```yaml
# AutoGraph Configuration
project:
  name: "AutoGraph Production"
  version: "1.0.0"
  environment: "production"

# Neo4j Database
database:
  neo4j:
    uri: "bolt://localhost:7687"
    username: "neo4j"
    password: "autograph123"
    database: "neo4j"
    connection_pool_size: 50
    max_retry_time: 30

# API Server
api:
  host: "0.0.0.0"
  port: 8001
  reload: false
  workers: 4
  cors_origins: ["*"]

# NLP Processing
nlp:
  ner:
    model_name: "dbmdz/bert-large-cased-finetuned-conll03-english"
    batch_size: 8
    max_length: 512
    confidence_threshold: 0.7
  
  relations:
    extraction_mode: "hybrid"
    ml_confidence_threshold: 0.65
    ensemble_method: "weighted_union"
    ensemble_weights:
      ml: 0.6
      rules: 0.4

# Entity Linking
entity_linking:
  mode: "offline"
  confidence_threshold: 0.5
  custom_catalogs_dir: "./entity_catalogs"
  cache_dir: "./cache/entities"
  max_candidates: 5

# Ontology
ontology:
  mode: "offline"
  custom_ontologies_dir: "./custom_ontologies"
  namespace_prefix: "http://autograph.custom/"

# Performance
performance:
  max_workers: 4
  batch_size: 8
  cache_ttl: 3600
  enable_caching: true

# Logging
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/autograph.log"
  max_size: "10MB"
  backup_count: 5
```

### 🔐 Environment Variables

Erstellen Sie `.env`:

```bash
# Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=autograph123
NEO4J_DATABASE=neo4j

# API
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=4

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# Paths
ENTITY_CATALOGS_DIR=./entity_catalogs
CUSTOM_ONTOLOGIES_DIR=./custom_ontologies
CACHE_DIR=./cache
LOGS_DIR=./logs

# External APIs (optional)
OPENAI_API_KEY=your-openai-key
HUGGINGFACE_API_TOKEN=your-hf-token

# Performance
MAX_WORKERS=4
BATCH_SIZE=8
CACHE_TTL=3600
```

### 📁 Verzeichnisstruktur erstellen

```bash
# Erstelle notwendige Verzeichnisse
mkdir -p entity_catalogs
mkdir -p custom_ontologies
mkdir -p cache/entities
mkdir -p cache/relations
mkdir -p logs
mkdir -p data/input
mkdir -p data/output

# Beispiel-Kataloge kopieren (falls vorhanden)
cp -r examples/entity_catalogs/* entity_catalogs/ 2>/dev/null || true
cp -r examples/custom_ontologies/* custom_ontologies/ 2>/dev/null || true

# Berechtigungen setzen (Linux/macOS)
chmod -R 755 entity_catalogs custom_ontologies cache logs data
```

---

## 🚀 Deployment

### 🐳 Docker Deployment

#### Single-Container Setup

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendung kopieren
COPY . .

# NLP-Modelle herunterladen
RUN python -m spacy download de_core_news_sm
RUN python -m spacy download en_core_web_sm

# Port freigeben
EXPOSE 8001

# Startkommando
CMD ["uvicorn", "src.autograph.api.server:app", "--host", "0.0.0.0", "--port", "8001"]
```

```bash
# Build und Run
docker build -t autograph:latest .
docker run -d -p 8001:8001 --name autograph-app autograph:latest
```

#### Docker Compose (empfohlen)

```yaml
# docker-compose.yml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.15
    container_name: autograph-neo4j
    restart: unless-stopped
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/autograph123
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_apoc_export_file_enabled: true
      NEO4J_apoc_import_file_enabled: true
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7474"]
      interval: 30s
      timeout: 10s
      retries: 3

  autograph:
    build: .
    container_name: autograph-api
    restart: unless-stopped
    ports:
      - "8001:8001"
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USERNAME: neo4j
      NEO4J_PASSWORD: autograph123
    volumes:
      - ./entity_catalogs:/app/entity_catalogs
      - ./custom_ontologies:/app/custom_ontologies
      - ./cache:/app/cache
      - ./logs:/app/logs
    depends_on:
      neo4j:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  neo4j_data:
  neo4j_logs:
```

```bash
# Deployment
docker-compose up -d

# Logs verfolgen
docker-compose logs -f

# Stoppen
docker-compose down
```

### 🖥️ Production Deployment

#### Systemd Service (Linux)

```ini
# /etc/systemd/system/autograph.service
[Unit]
Description=AutoGraph API Server
After=network.target

[Service]
Type=exec
User=autograph
Group=autograph
WorkingDirectory=/opt/autograph
Environment=PATH=/opt/autograph/venv/bin
ExecStart=/opt/autograph/venv/bin/uvicorn src.autograph.api.server:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Service aktivieren und starten
sudo systemctl enable autograph
sudo systemctl start autograph
sudo systemctl status autograph
```

#### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/autograph
server {
    listen 80;
    server_name autograph.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (optional)
    location /static {
        alias /opt/autograph/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### SSL mit Let's Encrypt

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx

# SSL-Zertifikat erstellen
sudo certbot --nginx -d autograph.yourdomain.com

# Auto-Renewal testen
sudo certbot renew --dry-run
```

---

## ✅ Validierung

### 🔍 System-Check Script

```bash
#!/bin/bash
# system_check.sh

echo "🔍 AutoGraph System Check"
echo "========================"

# Python Version
echo -n "Python Version: "
python --version

# Dependencies Check
echo -n "Dependencies: "
python -c "
import sys
required = ['fastapi', 'neo4j', 'spacy', 'transformers', 'torch']
missing = []
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)
if missing:
    print(f'❌ Missing: {missing}')
    sys.exit(1)
else:
    print('✅ All dependencies installed')
"

# Neo4j Connection
echo -n "Neo4j Connection: "
python -c "
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'autograph123'))
    with driver.session() as session:
        session.run('RETURN 1')
    print('✅ Connected')
    driver.close()
except Exception as e:
    print(f'❌ Failed: {e}')
"

# NLP Models
echo -n "spaCy Models: "
python -c "
import spacy
try:
    nlp = spacy.load('de_core_news_sm')
    print('✅ German model loaded')
except Exception as e:
    print(f'❌ Failed: {e}')
"

# API Server Test
echo -n "API Server: "
python -c "
import requests
try:
    response = requests.get('http://localhost:8001/health', timeout=5)
    if response.status_code == 200:
        print('✅ API responding')
    else:
        print(f'❌ API error: {response.status_code}')
except Exception as e:
    print(f'❌ API unreachable: {e}')
"

echo "========================"
echo "System Check Complete!"
```

### 🧪 Funktions-Tests

```bash
# API-Funktionstest
curl -X POST "http://localhost:8001/process/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Aspirin hilft gegen Kopfschmerzen",
    "domain": "medizin",
    "enable_entity_linking": true
  }'

# Entity Linking Test
curl -X POST "http://localhost:8001/entity-linking/link-entity" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_text": "Aspirin",
    "entity_type": "DRUG",
    "domain": "medizin"
  }'

# Ontology Test
curl "http://localhost:8001/ontology/status"

# CLI Test
python autograph_cli.py yaml wizard
```

---

## 🔧 Troubleshooting

### ❌ Häufige Probleme

#### 1. **Neo4j Verbindungsfehler**

```bash
# Problem: "ServiceUnavailable: Could not perform discovery"
# Lösung:
docker restart neo4j-autograph
# Oder
sudo systemctl restart neo4j

# Verbindung testen
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'autograph123'))
print('Connection OK')
driver.close()
"
```

#### 2. **ModuleNotFoundError**

```bash
# Problem: "No module named 'transformers'"
# Lösung:
pip install --upgrade -r requirements.txt

# Oder spezifisch:
pip install transformers torch spacy
```

#### 3. **spaCy Model Fehler**

```bash
# Problem: "Can't find model 'de_core_news_sm'"
# Lösung:
python -m spacy download de_core_news_sm
python -m spacy download en_core_web_sm

# Verifizierung:
python -c "import spacy; nlp = spacy.load('de_core_news_sm'); print('Model loaded')"
```

#### 4. **Port bereits in Verwendung**

```bash
# Problem: "Address already in use"
# Port finden:
lsof -i :8001
# Oder auf Windows:
netstat -ano | findstr :8001

# Prozess beenden:
kill -9 <PID>
# Oder auf Windows:
taskkill /PID <PID> /F
```

#### 5. **Memory-Probleme**

```bash
# Problem: "CUDA out of memory" oder "Memory Error"
# Lösung: Batch-Größe reduzieren
export BATCH_SIZE=4
export MAX_WORKERS=2

# Oder in der Konfiguration:
# batch_size: 4
# max_workers: 2
```

### 📊 Logging und Monitoring

```python
# logs/autograph.log aktivieren
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/autograph.log'),
        logging.StreamHandler()
    ]
)
```

```bash
# Log-Monitoring
tail -f logs/autograph.log

# Fehler-Analyse
grep "ERROR" logs/autograph.log

# Performance-Monitoring
grep "processing_time" logs/autograph.log
```

### 🔧 Performance-Tuning

```yaml
# Hochleistungs-Konfiguration
performance:
  # CPU-intensive Tasks
  max_workers: 8              # Anzahl CPU-Kerne
  batch_size: 16              # Größere Batches für GPU
  
  # Memory Management
  cache_ttl: 7200             # Längeres Caching
  enable_caching: true
  max_cache_size: "2GB"
  
  # Neo4j Optimization
  neo4j:
    connection_pool_size: 100
    max_retry_time: 60
    
  # Model Optimization
  nlp:
    use_gpu: true
    mixed_precision: true     # Für RTX GPUs
    model_parallel: true      # Für große Modelle
```

---

## 🔒 Sicherheit

### 🛡️ Production Security

```yaml
# Sicherheits-Konfiguration
security:
  # API Security
  enable_https: true
  ssl_cert: "/path/to/cert.pem"
  ssl_key: "/path/to/key.pem"
  
  # Authentication
  jwt_secret: "your-secure-jwt-secret"
  jwt_expiry: 3600
  
  # Rate Limiting
  rate_limit:
    requests_per_minute: 100
    burst_size: 20
  
  # CORS
  cors_origins: ["https://yourdomain.com"]
  
  # Database Security
  neo4j:
    encrypted: true
    trust_strategy: "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES"
```

### 🔐 Secrets Management

```bash
# Mit Docker Secrets
echo "autograph123" | docker secret create neo4j_password -

# Mit Environment Files
echo "NEO4J_PASSWORD=autograph123" > .env.production
chmod 600 .env.production

# Mit Kubernetes Secrets
kubectl create secret generic autograph-secrets \
  --from-literal=neo4j-password=autograph123
```

---

## 🚀 Nächste Schritte

1. **[API-Dokumentation](./API-Documentation.md)** - REST API verwenden
2. **[CLI-Dokumentation](./CLI-Documentation.md)** - Command Line Tools
3. **[Tutorials](./Tutorials.md)** - Praktische Beispiele
4. **[Entwickler-Guide](./Developer-Guide.md)** - Erweiterungen entwickeln

**📞 Support**: Bei Setup-Problemen siehe [GitHub Issues](https://github.com/FBR65/AutoGraph/issues)
