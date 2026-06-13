# Kubernetes Configuration for LabFull

This directory contains Kubernetes manifests for deploying the application.

## Prerequisites

- Kubernetes cluster (minikube, EKS, GKE, AKS, or local)
- `kubectl` configured to access your cluster
- Docker image built locally in the Minikube daemon or pushed to a registry

## Quick Start

1. **Apply the ConfigMap first:**
   ```bash
   kubectl apply -f configmap.yaml
   ```

2. **Create secrets (copy and edit the example):**
   ```bash
   cp secret.example.yaml secret.yaml
   # Edit secret.yaml with your actual database credentials
   kubectl apply -f secret.yaml
   ```

3. **Apply all resources:**
   ```bash
   # Apply in order (database first)
   kubectl apply -f postgres-deployment.yaml
   kubectl apply -f postgres-service.yaml
   
   # Wait for PostgreSQL to be ready (check status)
   kubectl get pods -w
   
   # Then apply the rest
   kubectl apply -f backend-deployment.yaml
   kubectl apply -f backend-service.yaml
   kubectl apply -f frontend-deployment.yaml
   kubectl apply -f frontend-service.yaml
   kubectl apply -f ingress.yaml
   ```

4. **Check deployment status:**
   ```bash
   kubectl get all -l app=postgres
   kubectl get all -l app=backend
   kubectl get all -l app=frontend
   
   # Check logs
   kubectl logs -l app=backend -f
   ```

5. **Access the application:**
   ```bash
   kubectl get ingress labfull-ingress
   curl -H 'Host: LabFull.maurocastro.cl' http://<minikube-ip>/
   ```

## Directory Structure

```
k8s/
├── configmap.yaml          # Application configuration
├── secret.example.yaml     # Example secrets (copy and edit)
├── postgres-deployment.yaml
├── postgres-service.yaml
├── backend-deployment.yaml
├── backend-service.yaml
├── frontend-deployment.yaml
├── frontend-service.yaml
└── ingress.yaml
```

## Customization

- Update `secret.yaml` with your actual PostgreSQL credentials
- Modify replica counts in deployments based on load requirements
- Adjust resource requests/limits as needed
- For production, consider using PersistentVolumeClaims instead of `emptyDir`

## Troubleshooting

```bash
# Check pod status
kubectl get pods

# Describe problematic pods
kubectl describe pod <pod-name>

# Check service endpoints
kubectl get endpoints

# Port-forward for debugging
kubectl port-forward svc/frontend-service 8080:80
```
