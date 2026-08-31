---
title: Kubernetes - app web
sidebar_position: 4
---

# App web en k3s

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whoami
spec:
  replicas: 2
  selector:
    matchLabels:
      app: whoami
  template:
    metadata:
      labels:
        app: whoami
    spec:
      containers:
        - name: whoami
          image: traefik/whoami:v1.11.0
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 20m
              memory: 32Mi
            limits:
              memory: 128Mi
---
apiVersion: v1
kind: Service
metadata:
  name: whoami
spec:
  selector:
    app: whoami
  ports:
    - port: 80
      targetPort: 80
```

## Pruebas

```bash
kubectl get deploy,pods,svc
kubectl scale deployment whoami --replicas=3
kubectl rollout status deployment/whoami
```

Luego migrar el manifest al repo GitOps y dejar de escalar manualmente.
