# Kubernetes Cluster Setup with Kubeadm on EC2

This guide will help you set up a Kubernetes cluster with 1 Master node and 1 Worker node using kubeadm.

---

## **Prerequisites**

- 2 EC2 instances (Ubuntu 20.04 or 22.04)
- Minimum 2 CPUs per instance
- Minimum 2GB RAM per instance
- Minimum 20GB disk space
- Security group allowing:
  - Port 6443 (API server)
  - Port 10250 (kubelet)
  - Port 30000-32767 (NodePort services)
  - Port 10256 (proxy)
  - All ports between nodes

---

## **Setup (Run on Both Master and Worker)**

> ⚠️ **[BOTH SERVERS]** - Execute these steps on BOTH Master and Worker nodes

### **Step 1: Update System** [BOTH]
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### **Step 2: Disable Swap (Required for Kubernetes)** [BOTH]
```bash
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab
```

### **Step 3: Load Kernel Modules** [BOTH]
```bash
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter
```

### **Step 4: Set Kernel Parameters** [BOTH]
```bash
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF

sudo sysctl --system
```

### **Step 5: Install Docker** [BOTH]
```bash
sudo apt-get install -y curl gnupg2 lsb-release ubuntu-keyring

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### **Step 6: Install Kubeadm, Kubelet, and Kubectl** [BOTH]
```bash
# Create keyrings directory
sudo mkdir -p /etc/apt/keyrings

# Download and add Kubernetes GPG key
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# Add Kubernetes repository
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Update package list and install
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl

# Lock versions to prevent automatic updates
sudo apt-mark hold kubelet kubeadm kubectl

# Enable kubelet service
sudo systemctl enable --now kubelet

# Verify installation
kubelet --version
kubeadm version
```

### **Step 7: Configure Container Runtime (containerd)** [BOTH]
```bash
mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Edit the config to use systemd as cgroup driver
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# Restart containerd
sudo systemctl restart containerd
```

---

## **Master Node Only Setup**

> ⚠️ **[MASTER ONLY]** - Execute these steps ONLY on the Master/Control Plane node

### **Step 1: Initialize Kubernetes Cluster** [MASTER]
```bash
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --control-plane-endpoint=<MASTER_PRIVATE_IP>:6443
```

Replace `<MASTER_PRIVATE_IP>` with the private IP of your master node (e.g., `10.0.1.100`)

Example:
```bash
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --control-plane-endpoint=10.0.1.100:6443
```

### **Step 2: Configure kubectl** [MASTER]
```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### **Step 3: Verify Cluster** [MASTER]
```bash
kubectl cluster-info
kubectl get nodes
```

You should see the master node in `NotReady` status (waiting for network addon)

### **Step 4: Install Network Add-on (Flannel)** [MASTER]
```bash
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml

# Wait a minute and check status
kubectl get nodes
```

Master node should now be in `Ready` status.

### **Step 5: Save Join Command** [MASTER]
```bash
# Run this and copy the entire output
sudo kubeadm token create --print-join-command
```

Save this command - you'll need it for worker nodes!

---

## **Worker Node Only Setup**

> ⚠️ **[WORKER ONLY]** - Execute these steps ONLY on Worker node(s)

### **Step 1: Join Cluster** [WORKER]
```bash
# Use the join command from Step 5 of Master setup
sudo <PASTE_THE_FULL_JOIN_COMMAND_HERE>

# Example (your actual command will be different):
sudo kubeadm join 10.0.1.100:6443 --token abc123.def456 \
  --discovery-token-ca-cert-hash sha256:1234567890abcdef...
```

### **Step 2: Verify Worker Joined** [MASTER]
```bash
# Run this on MASTER node:
kubectl get nodes
```

Worker node should appear with `Ready` status.

---

## **Verify Cluster Setup** [MASTER]

On the **Master node**, run:

```bash
# Check all nodes
kubectl get nodes

# Check system pods
kubectl get pods -n kube-system

# Check cluster info
kubectl cluster-info

# Check events
kubectl get events -n kube-system
```

**Expected output:**
```
NAME            STATUS   ROLES                  AGE   VERSION
master-node     Ready    control-plane,master   5m    v1.28.0
worker-node     Ready    <none>                 2m    v1.28.0
```

---

## **Useful Commands** [ALL]

These commands can be run on Master or Worker nodes as needed:

### **View Join Command Again**
```bash
sudo kubeadm token create --print-join-command
```

### **Check Kubelet Status**
```bash
sudo systemctl status kubelet
sudo journalctl -u kubelet -f  # Follow logs
```

### **Check Docker Images**
```bash
docker images | grep -i kube
```

### **Reset Cluster (if needed)**
```bash
# Only on the node to reset
sudo kubeadm reset -f
sudo rm -rf /etc/cni /etc/kubernetes /var/lib/etcd /var/lib/kubelet
sudo systemctl restart docker kubelet
```

---

## **Copy Kubeconfig to Docker Server** [MASTER → DOCKER SERVER]

After cluster is ready, copy kubeconfig to your Docker server for Jenkins:

### **On Master node:** [MASTER]
```bash
cat ~/.kube/config
```

### **On Docker server:** [DOCKER SERVER]
```bash
mkdir -p ~/.kube
# Create/edit ~/.kube/config and paste the content
nano ~/.kube/config

# Set permissions
chmod 600 ~/.kube/config

# Verify connection
kubectl cluster-info
kubectl get nodes
```

---

## **Troubleshooting**

### **Nodes in NotReady status**
```bash
kubectl describe node <node-name>
kubectl logs -n kube-system -l component=kubelet
```

### **Pod networking issues**
```bash
kubectl get pods -n kube-system
kubectl logs -n kube-system -l app=flannel
```

### **High CPU/Memory usage**
```bash
# Check resource usage
kubectl top nodes
kubectl top pods -A
```

---

## **Security Group Rules (AWS)**

Add these inbound rules to your security group:

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 6443 | TCP | Master SG | API Server |
| 10250 | TCP | Node SG | Kubelet API |
| 10256 | TCP | Node SG | Proxy |
| 30000-32767 | TCP | 0.0.0.0/0 | NodePort services |
| All | All | Master SG | Inter-node communication |
| All | All | Node SG | Inter-node communication |

---

## **Next Steps**

1. Deploy your application manifests
2. Set up kubectl access from Docker server
3. Configure Jenkins with kubeconfig
4. Run the Jenkinsfile pipeline

---

**Created: January 15, 2026**
