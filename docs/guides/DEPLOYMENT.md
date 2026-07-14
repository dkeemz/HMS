# Deployment Guide

## Overview

HMS supports hybrid deployment (on-premise + cloud) with Docker and Kubernetes.

## Prerequisites

### On-Premise
- Ubuntu 22.04 LTS or RHEL 9
- Docker 24+ and Docker Compose v2
- Kubernetes 1.28+ (if using K8s)
- Helm 3.14+
- SSL certificates
- Network access to cloud services

### Cloud (AWS/Azure)
- VPC with private subnets
- RDS PostgreSQL 17 (or self-managed)
- ElastiCache Redis 7
- S3/MinIO for object storage
- CloudFront/CDN for static assets

---

## Development Setup

### Local Development

```bash
# Prerequisites
- Node.js 22+
- PostgreSQL 17
- Redis 7
- Docker (for Keycloak, Elasticsearch)

# Quick Start
git clone https://github.com/dkeemz/HMS.git
cd HMS
npm install
docker compose up -d  # Start dependencies
npx prisma migrate dev
npm run dev

# Access
- App: http://localhost:3000
- API: http://localhost:3001
- Keycloak: http://localhost:8080
```

### Docker Compose (Full Stack)

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: hms
      POSTGRES_USER: hms
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  keycloak:
    image: quay.io/keycloak/keycloak:26.0
    command: start
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/hms
      KC_DB_USERNAME: hms
      KC_DB_PASSWORD: ${DB_PASSWORD}
      KC_HOSTNAME: keycloak.localhost
      KC_HTTP_RELATIVE_PATH: /auth
      KC_HEALTH_ENABLED: true
    ports:
      - "8080:8080"

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"

  app:
    build: .
    environment:
      DATABASE_URL: postgresql://hms:${DB_PASSWORD}@postgres:5432/hms
      REDIS_URL: redis://redis:6379
      KEYCLOAK_URL: http://keycloak:8080
    ports:
      - "3000:3000"
    depends_on:
      - postgres
      - redis
      - keycloak

volumes:
  postgres_data:
```

---

## Production Deployment

### Step 1: Infrastructure Setup

#### AWS

```bash
# VPC Setup
aws ec2 create-vpc --cidr-block 10.0.0.0/16
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24
aws ec2 create-internet-gateway
aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID

# RDS PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier hms-db \
  --db-instance-class db.r6g.xlarge \
  --engine postgres \
  --engine-version 17 \
  --master-username hms \
  --master-user-password $DB_PASSWORD \
  --allocated-storage 100 \
  --storage-type gp3 \
  --vpc-security-group-ids $SG_ID \
  --db-subnet-group-name $SUBNET_GROUP

# ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id hms-redis \
  --cache-node-type cache.r6g.large \
  --engine redis \
  --engine-version 7 \
  --num-cache-nodes 1
```

#### Azure

```bash
# AKS Cluster
az aks create \
  --resource-group hms-rg \
  --name hms-cluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-managed-identity

# Azure Database for PostgreSQL
az postgres flexible-server create \
  --resource-group hms-rg \
  --name hms-db \
  --admin-user hms \
  --admin-password $DB_PASSWORD \
  --sku-name Standard_D4s_v3 \
  --tier GeneralPurpose

# Azure Cache for Redis
az redis create \
  --resource-group hms-rg \
  --name hms-redis \
  --sku Premium \
  --vm-size P1
```

### Step 2: Kubernetes Deployment

#### Helm Values

```yaml
# values-production.yaml
replicaCount: 3

image:
  repository: ghcr.io/dkeemz/hms
  tag: "latest"
  pullPolicy: Always

env:
  DATABASE_URL: postgresql://hms:${DB_PASSWORD}@hms-db.internal:5432/hms
  REDIS_URL: redis://hms-redis.internal:6379
  KEYCLOAK_URL: https://auth.hms.com
  FHIR_SERVER_URL: https://fhir.hms.com/fhir

resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: hms.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: hms-tls
      hosts:
        - hms.com

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
```

#### Deploy

```bash
# Add Helm repos
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install dependencies
helm install hms-postgres bitnami/postgresql -f values-postgres.yaml
helm install hms-redis bitnami/redis -f values-redis.yaml

# Deploy HMS
helm install hms ./helm/hms -f values-production.yaml

# Verify
kubectl get pods
kubectl get ingress
```

### Step 3: SSL/TLS Setup

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Create ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@hms.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Step 4: Database Migration

```bash
# Run migrations
kubectl exec -it $POD_NAME -- npx prisma migrate deploy

# Seed initial data
kubectl exec -it $POD_NAME -- npm run seed
```

### Step 5: Monitoring Setup

```bash
# Install Prometheus + Grafana
helm install prometheus bitnami/kube-prometheus-stack -f values-monitoring.yaml

# Import HMS dashboards
kubectl apply -f dashboards/
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql://user:pass@host:5432/db |
| REDIS_URL | Redis connection string | redis://host:6379 |
| KEYCLOAK_URL | Keycloak base URL | https://auth.hms.com |
| KEYCLOAK_REALM | Keycloak realm name | hms |
| KEYCLOAK_CLIENT_ID | Keycloak client ID | hms-backend |
| JWT_SECRET | JWT signing secret | (generate random 256-bit) |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| FHIR_SERVER_URL | FHIR server URL | http://localhost:8081/fhir |
| SENDGRID_API_KEY | SendGrid API key | - |
| TWILIO_SID | Twilio account SID | - |
| ELASTICSEARCH_URL | Elasticsearch URL | http://localhost:9200 |
| LOG_LEVEL | Logging level | info |
| NODE_ENV | Environment | development |

---

## Backup & Restore

### Database Backup

```bash
# Manual backup
pg_dump -h $DB_HOST -U hms hms > backup_$(date +%Y%m%d).sql

# Automated backup (cron)
0 2 * * * pg_dump -h $DB_HOST -U hms hms | gzip > /backups/hms_$(date +\%Y\%m\%d).sql.gz
```

### Restore

```bash
# Restore from backup
psql -h $DB_HOST -U hms hms < backup_20260714.sql
```

---

## Security Checklist

### Pre-Deployment
- [ ] SSL certificates configured
- [ ] Environment variables secured (not in git)
- [ ] Database passwords rotated
- [ ] JWT secret generated (256-bit minimum)
- [ ] CORS whitelist configured
- [ ] Rate limiting enabled
- [ ] Security headers configured

### Post-Deployment
- [ ] HTTPS enforced
- [ ] HTTP → HTTPS redirect working
- [ ] MFA enabled for all admin accounts
- [ ] Audit logging verified
- [ ] Backup schedule confirmed
- [ ] Monitoring alerts configured
- [ ] Incident response plan documented

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Pod CrashLoopBackOff | Check logs: `kubectl logs $POD` |
| Database connection refused | Verify network, credentials, and DB status |
| Keycloak not responding | Check Keycloak pod, restart if needed |
| SSL certificate errors | Verify cert-manager, check certificate status |
| High memory usage | Check for memory leaks, adjust limits |
| Slow queries | Enable query logging, check indexes |

### Health Checks

```bash
# API health
curl https://hms.com/api/health

# Database
psql -h $DB_HOST -U hms -c "SELECT 1"

# Redis
redis-cli -h $REDIS_HOST ping

# Keycloak
curl https://auth.hms.com/auth/realms/hms/.well-known/openid-configuration
```
