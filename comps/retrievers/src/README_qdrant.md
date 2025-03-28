# Retriever Microservice with Qdrant

## 1. 🚀Start Microservice with Python (Option 1)

### 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

### 1.2 Start Qdrant Server

Please refer to this [readme](../../third_parties/pgvector/src/README.md).

### 1.3 Setup Environment Variables

```bash
export QDRANT_HOST=${your_qdrant_host_ip}
export QDRANT_PORT=6333
export EMBED_DIMENSION=${your_embedding_dimension}
export INDEX_NAME=${your_index_name}
```

### 1.4 Start Retriever Service

```bash
export TEI_EMBEDDING_ENDPOINT="http://${your_ip}:6060"
export RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_QDRANT"
python opea_retrievers_microservice.py
```

## 2. 🚀Start Microservice with Docker (Option 2)

### 2.1 Setup Environment Variables

```bash
export QDRANT_HOST=${your_qdrant_host_ip}
export QDRANT_PORT=6333
export TEI_EMBEDDING_ENDPOINT="http://${your_ip}:6060"
export RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_QDRANT"
```

### 2.2 Build Docker Image

```bash
cd ../../../
docker build -t opea/retriever:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
```

### 2.3 Run Docker with CLI (Option A)

```bash
docker run -d --name="retriever-qdrant-server" -p 7000:7000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e TEI_EMBEDDING_ENDPOINT=$TEI_EMBEDDING_ENDPOINT -e QDRANT_HOST=$QDRANT_HOST -e QDRANT_PORT=$QDRANT_PORT -e RETRIEVER_COMPONENT_NAME=$RETRIEVER_COMPONENT_NAME opea/retriever:latest
```

### 2.4 Run Docker with Docker Compose (Option B)

```bash
cd ../deployment/docker_compose
export service_name="retriever-qdrant"
docker compose -f compose.yaml up ${service_name} -d
```

## 🚀3. Consume Retriever Service

### 3.1 Check Service Status

```bash
curl http://${your_ip}:7000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

### 3.2 Consume Embedding Service

To consume the Retriever Microservice, you can generate a mock embedding vector of length 768 with Python.

```bash
export your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://${your_ip}:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```
