# Blog CMS - Kubernetes Deployment

A production-ready, containerized 3-tier Blog/Content Management System deployed on Kubernetes with CI/CD pipeline.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Frontend     │  │   Backend    │  │    MySQL     │   │
│  │  (React+Nginx) │→ │   (Flask)    │→ │  (StatefulSet)│   │
│  │   2 replicas   │  │  2 replicas  │  │  Persistent   │   │
│  │   Port: 80     │  │  Port: 5000  │  │  Port: 3306   │   │
│  └────────────────┘  └──────────────┘  └──────────────┘   │
│         ↑                                                    │
│    NodePort :32743                                          │
└─────────────────────────────────────────────────────────────┘
         ↑
    Load Balancer / Public Access
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
- ☸️ Kubernetes orchestration
- 📦 Helm-ready configuration
- 🔄 CI/CD with Jenkins
- 🌐 Nginx reverse proxy
- 📊 Service mesh ready
- 🔒 Secrets management
- 💾 Persistent storage for MySQL

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster (v1.28+)
- kubectl configured
- Docker Hub account (or private registry)
- kubectl CLI installed

### Deploy to Kubernetes

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/blog-cms-k8s.git
cd blog-cms-k8s
```

2. **Create namespace:**
```bash
kubectl apply -f k8s/namespace.yaml
```

3. **Deploy MySQL with storage:**
```bash
kubectl apply -f k8s/storageclass.yaml
kubectl apply -f k8s/mysql-storage.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/mysql-init-configmap.yaml
kubectl apply -f k8s/mysql-deployment.yaml
```

4. **Deploy Backend:**
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/backend-deployment.yaml
```

5. **Deploy Frontend:**
```bash
kubectl apply -f k8s/frontend-deployment.yaml
```

6. **Access the application:**
```bash
kubectl get svc -n blog-app
# Access via NodePort: http://<node-ip>:32743
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

## 🐳 Docker Images

Build and push custom images:

```bash
# Backend
cd backend
docker build -t yourusername/blog-backend:latest .
docker push yourusername/blog-backend:latest

# Frontend
cd frontend
docker build --build-arg REACT_APP_API_URL=/api -t yourusername/blog-frontend:latest .
docker push yourusername/blog-frontend:latest
```

## 🔄 CI/CD Pipeline

Jenkins pipeline stages:
1. **Checkout** - Pull code from Git
2. **Build Backend** - Build Flask Docker image
3. **Build Frontend** - Build React Docker image
4. **Push Images** - Push to Docker Hub
5. **Deploy to K8s** - Update Kubernetes deployments

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
