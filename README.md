# Blog CMS - EKS Deployment with ECR

A production-ready, containerized 3-tier Blog/Content Management System deployed on **Amazon EKS** with **ECR** registry and **Jenkins CI/CD** pipeline.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS EKS Cluster (blog-eks)                    │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Frontend     │  │   Backend    │  │    MySQL     │        │
│  │  (React+Nginx) │→ │   (Flask)    │→ │  (StatefulSet)│        │
│  │   2 replicas   │  │  2 replicas  │  │  EBS Storage │        │
│  │   Port: 80     │  │  Port: 5000  │  │  Port: 3306  │        │
│  └────────────────┘  └──────────────┘  └──────────────┘        │
│         ↑                                                         │
│    AWS LoadBalancer (ELB)                                        │
└──────────────────────────────────────────────────────────────────┘
         ↑
    Public Access (*.elb.amazonaws.com)

Container Images: AWS ECR (335853528110.dkr.ecr.us-east-1.amazonaws.com)
CI/CD: Jenkins → ECR → EKS
```

## ✨ Features

### Application Features
- 🔐 User Authentication (JWT-based)
- 👥 Role-based access control (Admin/Author)
- 📝 CRUD operations for blog posts
- 🏷️ Category management
- 💬 Comment system with approval workflow
- 📝 Rich text editor for content
- 🖼️ Image upload and management
- 🔍 SEO-friendly URLs with slugs
- 📊 Draft/Published status workflow

### DevOps Features
- 🐳 Docker containerization (multi-stage builds)
- ☸️ **Amazon EKS** orchestration
- 📦 **AWS ECR** for container registry
- 🔄 CI/CD with **Jenkins** (automated builds & deployments)
- 🌐 Nginx reverse proxy
- 💾 **EBS persistent storage** for MySQL
- 🔒 AWS Secrets management
- 🚀 Auto-scaling ready
- 📊 CloudWatch monitoring ready

## 🚀 Quick Start (EKS Deployment)

### Prerequisites
- **AWS Account** with ECR and EKS access
- **AWS CLI** configured (`aws configure`)
- **eksctl** installed
- **kubectl** CLI installed
- **Jenkins** server with AWS credentials

### Step 1: Create EKS Cluster

```bash
eksctl create cluster \
  --name blog-eks \
  --region us-east-1 \
  --nodes 2 \
  --node-type t3.small \
  --with-oidc \
  --managed

# Install EBS CSI Driver (for persistent storage)
eksctl create addon \
  --cluster blog-eks \
  --name aws-ebs-csi-driver \
  --region us-east-1 \
  --force
```

### Step 2: Create ECR Repositories

```bash
aws ecr create-repository --repository-name blog-backend --region us-east-1
aws ecr create-repository --repository-name blog-frontend --region us-east-1
```

### Step 3: Push Images to ECR

```bash
# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Pull from Docker Hub and push to ECR
docker pull priteecha/blog-backend:latest
docker tag priteecha/blog-backend:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blog-backend:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blog-backend:latest

docker pull priteecha/blog-frontend:latest
docker tag priteecha/blog-frontend:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blog-frontend:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blog-frontend:latest
```

### Step 4: Deploy to EKS

```bash
# Update kubeconfig
aws eks update-kubeconfig --name blog-eks --region us-east-1

# Deploy all resources
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/mysql-storage.yaml
kubectl apply -f k8s/mysql-init-configmap.yaml
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# Get LoadBalancer URL
kubectl get svc frontend-service -n blog-app
# Access via: http://<EXTERNAL-IP>.elb.amazonaws.com
```

### Default Credentials
- **Username:** admin / author1
- **Password:** password123

## 📁 Project Structure

```
.
├── backend/
│   ├── app.py                 # Flask application
│   ├── Dockerfile             # Backend container image
│   ├── requirements.txt       # Python dependencies
│   └── .env.example          # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── contexts/        # React contexts
│   ├── Dockerfile           # Frontend multi-stage build
│   ├── nginx.conf          # Nginx configuration
│   └── package.json        # Node.js dependencies
├── k8s/
│   ├── namespace.yaml           # Kubernetes namespace
│   ├── configmap.yaml          # App configuration
│   ├── secret.yaml             # Sensitive data
│   ├── mysql-deployment.yaml   # MySQL StatefulSet
│   ├── mysql-storage.yaml      # PersistentVolumeClaim
│   ├── backend-deployment.yaml # Backend Deployment
│   ├── frontend-deployment.yaml # Frontend Deployment
│   └── storageclass.yaml       # Storage class definition
├── database/
│   └── schema.sql             # Database schema
├── Jenkinsfile                # CI/CD pipeline
├── docker-compose.yml         # Local development setup
└── README.md

```

## 🔧 Configuration

### Environment Variables

**Backend (ConfigMap):**
- `DATABASE_URL`: MySQL connection string
- `JWT_SECRET_KEY`: JWT signing key
- `JWT_EXPIRES_DAYS`: Token expiration (default: 1)

**Frontend (Build-time):**
- `REACT_APP_API_URL`: Backend API URL (default: `/api`)

### Kubernetes Resources

| Resource | Type | Replicas | Storage |
|----------|------|----------|---------|
| Frontend | Deployment | 2 | - |
| Backend | Deployment | 2 | - |
| MySQL | StatefulSet | 1 | 5Gi PVC |

### Service Endpoints

| Service | Type | Port | Internal DNS |
|---------|------|------|-------------|
| frontend-service | LoadBalancer | 80 | frontend-service.blog-app.svc.cluster.local |
| backend | ClusterIP | 5000 | backend.blog-app.svc.cluster.local |
| mysql-service | ClusterIP | 3306 | mysql-service.blog-app.svc.cluster.local |

## 🐳 Container Images (ECR)

**ECR Registry:** `335853528110.dkr.ecr.us-east-1.amazonaws.com`

Build and push to ECR:

```bash
# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push Backend
cd backend
docker build -t $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blog-backend:latest .
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blog-backend:latest

# Build and push Frontend
cd frontend
docker build -t $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blog-frontend:latest .
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/blog-frontend:latest
```

## 🔄 CI/CD Pipeline (Jenkins + EKS + ECR)

**Jenkins Pipeline Stages:**
1. **Checkout** - Pull code from GitHub
2. **Build Images** - Build Backend & Frontend (parallel)
3. **Security Scan** - Trivy vulnerability scanning (optional)
4. **Push to ECR** - Push images to AWS ECR
5. **K8s Precheck** - Update kubeconfig for EKS
6. **Deploy to EKS** - Rolling update deployments
7. **Verify** - Check pod/service status

**Jenkins Setup:**
```bash
# On Jenkins EC2, configure AWS CLI
aws configure

# Update kubeconfig for EKS
aws eks update-kubeconfig --name blog-eks --region us-east-1

# Test access
kubectl get nodes
```

**Jenkinsfile Key Features:**
- Uses AWS IAM role (no hardcoded credentials)
- Automated ECR login
- Rolling updates with zero downtime
- Automatic rollback on failure

## 📡 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration

### Posts
- `GET /api/posts` - List all posts (pagination)
- `GET /api/posts/:id` - Get single post
- `POST /api/posts` - Create new post (requires auth)
- `PUT /api/posts/:id` - Update post (requires auth)
- `DELETE /api/posts/:id` - Delete post (requires auth)

### Categories
- `GET /api/categories` - List all categories
- `POST /api/categories` - Create category (requires auth)

### Comments
- `GET /api/posts/:id/comments` - Get post comments
- `POST /api/comments` - Add comment

### File Upload
- `POST /api/upload` - Upload image (requires auth)
- `GET /api/uploads/:filename` - Get uploaded file

## 🛠️ Troubleshooting

Common issues and solutions are documented in [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Quick Checks

**1. Check pod status:**
```bash
kubectl get pods -n blog-app
```

**2. View logs:**
```bash
kubectl logs -f <pod-name> -n blog-app
```

**3. Test DNS resolution:**
```bash
kubectl exec -n blog-app <frontend-pod> -- nslookup backend
```

**4. Check services:**
```bash
kubectl get svc -n blog-app
```

## 🌐 Accessing the Application

### NodePort (Development)
```
http://<node-ip>:32743
```

### LoadBalancer (Production)
```
http://<load-balancer-ip>
```

### Port Forwarding (Testing)
```bash
kubectl port-forward -n blog-app svc/frontend-service 8080:80
# Access: http://localhost:8080
```

## 🔒 Security Considerations

- ✅ JWT-based authentication
- ✅ Secrets stored in Kubernetes Secrets (base64)
- ✅ CORS configured for frontend domain
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Environment-based configuration
- ⚠️ **Production:** Use external secrets manager (AWS Secrets Manager, HashiCorp Vault)
- ⚠️ **Production:** Enable TLS/SSL with cert-manager
- ⚠️ **Production:** Implement network policies

## 📊 Monitoring & Logging

**Recommended tools:**
- Prometheus + Grafana for metrics
- EFK Stack (Elasticsearch, Fluentd, Kibana) for logs
- Jaeger for distributed tracing

## 🧪 Testing

**Local Development:**
```bash
docker-compose up
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- MySQL: localhost:3306



## 👥 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request



## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Review troubleshooting guide

---

**Built with ❤️ using React, Flask, MySQL, Docker, and Kubernetes**
