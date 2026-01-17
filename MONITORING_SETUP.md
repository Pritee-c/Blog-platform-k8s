# 📊 Monitoring Setup Guide - Prometheus & Grafana

This guide covers setting up Prometheus and Grafana for monitoring your EKS blog platform.

## 🎯 Prerequisites

- **EKS Cluster** running (with at least 2 t3.large nodes)
- **kubectl** CLI installed and configured
- **Helm** package manager installed (`sudo snap install helm --classic`)
- **EBS CSI Driver** addon installed on EKS
- **StorageClass** configured (e.g., `ebs-sc`)

## 📦 Installation

### Step 1: Create Monitoring Namespace

```bash
kubectl create namespace monitoring
```

### Step 2: Add Prometheus Helm Repository

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### Step 3: Create Storage Class for Persistent Volumes

Apply the `k8s/storageclass.yaml` to create EBS-backed storage:

```bash
kubectl apply -f k8s/storageclass.yaml
```

This creates:
- `ebs-sc`: EBS gp3 storage for Prometheus and Grafana data
- `manual`: Manual storage provisioning for other uses

### Step 4: Install kube-prometheus-stack

The kube-prometheus-stack includes Prometheus, Grafana, AlertManager, and node exporter.

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --set grafana.adminPassword=admin123 \
  --set grafana.persistence.enabled=true \
  --set grafana.persistence.storageClassName=ebs-sc \
  --set grafana.persistence.size=5Gi \
  --set prometheus.prometheusSpec.retention=15d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName=ebs-sc \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi
```

**What gets installed:**
- ✅ Prometheus: Metrics collection and storage
- ✅ Grafana: Visualization and dashboards
- ✅ AlertManager: Alert routing and notifications
- ✅ node-exporter: Node metrics (CPU, memory, disk)
- ✅ kube-state-metrics: Kubernetes object metrics

### Step 5: Verify Installation

```bash
# Check if all monitoring pods are running
kubectl get pods -n monitoring

# Expected output (all should show Running):
# prometheus-grafana-xxxxxxxx-xxxxx                    3/3     Running
# prometheus-kube-prometheus-operator-xxxxxxxxx-xxxxx  1/1     Running
# prometheus-kube-state-metrics-xxxxxxxxx-xxxxx        1/1     Running
# prometheus-prometheus-kube-prometheus-prometheus-0   2/2     Running
# prometheus-prometheus-node-exporter-xxxxx            1/1     Running
```

### Step 6: Apply ServiceMonitors for Microservices

This enables Prometheus to scrape metrics from your auth, post, and comment services:

```bash
kubectl apply -f monitoring/servicemonitor.yaml
```

**Verify ServiceMonitors are created:**
```bash
kubectl get servicemonitors -n monitoring
# Output should show: auth-service, post-service, comment-service
```

## 🌐 Access Grafana & Prometheus

### Option 1: Port Forwarding (Recommended for Testing)

**Expose Grafana on port 3001:**
```bash
kubectl port-forward svc/prometheus-grafana 3001:80 -n monitoring --address=0.0.0.0 &
```

**Expose Prometheus on port 9090:**
```bash
kubectl port-forward svc/prometheus-operated 9090:9090 -n monitoring --address=0.0.0.0 &
```

**Access from your browser:**
- **Grafana**: http://<your-public-ip>:3001 (admin / admin123)
- **Prometheus**: http://<your-public-ip>:9090

### Option 2: LoadBalancer Service (Production)

Create a LoadBalancer service to expose Grafana externally:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: grafana-lb
  namespace: monitoring
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 3000
  selector:
    app.kubernetes.io/name: grafana
```

## 📊 Import Grafana Dashboards

### Quick Import (Easiest Method)

1. **Open Grafana** at http://your-ip:3001
2. **Login**: admin / admin123
3. Click **"+" (Plus icon)** → **"Import"**
4. **Enter Dashboard ID**: `6417` (Kubernetes Cluster Monitoring)
5. Click **"Load"**
6. Select **"Prometheus"** datasource
7. Click **"Import"**

**Dashboard shows:**
- Node CPU and memory usage
- Pod count and status
- Deployment replicas
- Network I/O
- Container resource usage

### Alternative Dashboards

Try these dashboard IDs for different views:

| ID | Dashboard Name | Content |
|---|---|---|
| 6417 | Kubernetes Cluster Monitoring | Overall cluster health |
| 1860 | Node Exporter for Prometheus | Detailed node metrics |
| 3662 | Prometheus 2.0 Stats | Prometheus performance |
| 12114 | Kubernetes Cluster Monitoring (Advanced) | Advanced cluster insights |

**To import:**
1. Click **"+" → "Import"**
2. Paste the **ID**
3. Click **"Load"** → Select **"Prometheus"** → **"Import"**

### Import Custom JSON Dashboard

If you have a dashboard JSON file (e.g., `12114_rev1.json`):

1. Click **"+" → "Import"**
2. Click **"Upload JSON file"**
3. Select your downloaded JSON file
4. Select **"Prometheus"** datasource
5. Click **"Import"**

## 🔍 Querying Prometheus Directly

Open http://your-ip:9090 and use the **Graph** tab to query metrics:

### Cluster Health Metrics

```promql
# Check if all services are up
up

# Pods status
kube_pod_status_phase

# Deployment replicas
kube_deployment_status_replicas

# Pod restart rate (per 5 minutes)
rate(kube_pod_container_status_restarts_total[5m])
```

### Node Metrics

```promql
# CPU usage per node (last 1 minute)
rate(node_cpu_seconds_total[1m])

# Memory available per node (in GB)
node_memory_MemAvailable_bytes / 1024 / 1024 / 1024

# Disk usage per node
node_filesystem_size_bytes{fstype="ext4"}

# Network traffic in/out
rate(node_network_receive_bytes_total[1m])
rate(node_network_transmit_bytes_total[1m])
```

### Your Microservices Metrics

```promql
# Check if your services are up
up{job=~"auth-service|post-service|comment-service"}

# Auth service status
up{job="auth-service"}

# Post service status
up{job="post-service"}

# Comment service status
up{job="comment-service"}
```

## 📈 Create Custom Dashboards

### Step 1: Create a New Dashboard

1. Click **"+" → "Create" → "Dashboard"**
2. Click **"Add Panel"**

### Step 2: Add a Panel (Example: Service Status)

1. In the **Metrics** field, type: `up{job="auth-service"}`
2. Click outside to confirm
3. Click **Panel title** to rename it to "Auth Service Status"
4. Click **Panel options** and change **Visualization** to **"Stat"**
5. Click **"Save panel"**

### Step 3: Add More Panels

Repeat Step 2 for other services and metrics:

- **Post Service**: `up{job="post-service"}`
- **Comment Service**: `up{job="comment-service"}`
- **MySQL Status**: `up{job="mysql"}`
- **Pod Restarts**: `rate(kube_pod_container_status_restarts_total[5m])`
- **CPU Usage**: `rate(node_cpu_seconds_total[1m])`
- **Memory Usage**: `node_memory_MemAvailable_bytes / 1024 / 1024 / 1024`

### Step 4: Save Dashboard

Click **"Save"** at the top and name it "Blog Platform - Live Monitoring"

## 🔔 Configure Alerts (Optional)

### Create PrometheusRule for Alerts

Create a file `k8s/prometheus-rules.yaml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: blog-alerts
  namespace: monitoring
spec:
  groups:
  - name: kubernetes.rules
    interval: 30s
    rules:
    # Alert if pod is restarting frequently
    - alert: PodRestartingTooOften
      expr: rate(kube_pod_container_status_restarts_total[15m]) > 0.1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Pod {{ $labels.pod }} restarting frequently"
        
    # Alert if service is down
    - alert: ServiceDown
      expr: up{job=~"auth-service|post-service|comment-service"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Service {{ $labels.job }} is down"
        
    # Alert if CPU usage is high
    - alert: HighCPUUsage
      expr: rate(node_cpu_seconds_total[5m]) > 0.8
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High CPU usage on {{ $labels.node }}"
```

Apply the rules:
```bash
kubectl apply -f k8s/prometheus-rules.yaml
```

## 🧹 Cleanup

To remove the monitoring stack:

```bash
# Delete ServiceMonitors
kubectl delete servicemonitors -n monitoring --all

# Delete PrometheusRules
kubectl delete prometheusrules -n monitoring --all

# Uninstall Helm release
helm uninstall prometheus -n monitoring

# Delete PVCs
kubectl delete pvc -n monitoring --all

# Delete namespace
kubectl delete namespace monitoring
```

## 🐛 Troubleshooting

### Prometheus not scraping services

**Problem**: ServiceMonitors created but services show as "DOWN" in Prometheus

**Solution**:
```bash
# Check if ServiceMonitors exist
kubectl get servicemonitors -n monitoring

# Verify Prometheus operator is running
kubectl get pods -n monitoring | grep operator

# Check Prometheus targets
# Open: http://your-ip:9090/targets
# Look for your services - should show "UP"
```

### High memory usage in Prometheus

**Problem**: Prometheus pod using too much memory

**Solution**: Reduce retention period in Helm values:
```bash
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --set prometheus.prometheusSpec.retention=7d
```

### Grafana dashboards not showing data

**Problem**: Imported dashboards show "No data"

**Solution**:
1. Verify Prometheus datasource is set as default
2. Check datasource in dashboard settings (Dashboard → Settings → Datasource)
3. Verify Prometheus has scraped metrics: http://your-ip:9090/graph

### Port-forward connection refused

**Problem**: `Unable to connect to the server: dial tcp`

**Solution**:
```bash
# Kill existing port-forward processes
pkill -f "port-forward"

# Start fresh with correct service name
kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80 --address=0.0.0.0
```

## 📚 Useful Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Kubernetes Monitoring with Prometheus](https://prometheus.io/docs/prometheus/latest/installation/#kubernetes)
- [Grafana Dashboard Repository](https://grafana.com/grafana/dashboards/)

---

**Next Steps:**
1. ✅ Import dashboard 6417 to see cluster metrics
2. ✅ Verify ServiceMonitors are scraping your services
3. ✅ Create custom dashboard for your blog platform
4. ⏳ Configure alerts for critical failures
5. ⏳ Set up alert notifications (Slack, email, PagerDuty)

