# Mini-projet 2 — Gestionnaire de tâches 3-tiers sur k3s

## Architecture

Utilisateur → Ingress (app.k3s.local) → frontend (nginx) → api (FastAPI) → db (PostgreSQL)

## Prérequis

- Cluster k3s 3 nœuds
- kubectl configuré
- Docker installé
- Entrée `app.k3s.local` dans le fichier hosts de Windows

## Déploiement

```bash
kubectl apply -f k8s/00-namespace/
kubectl apply -f k8s/10-config/
kubectl apply -f k8s/20-db/
kubectl apply -f k8s/30-app/
kubectl apply -f k8s/40-security/
kubectl apply -f k8s/50-backup/