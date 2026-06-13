# LabFull Multibranch Pipeline

## Branch map

| Branch | Role |
|--------|------|
| `main` | Shared validation and merge hygiene |
| `minikube-deploy` | Deploy on Ubuntu Minikube and validate the reverse proxy |
| `aws-deploy` | Promote FE, BE and BD to AWS |

## Jenkins setup

1. Create a **Multibranch Pipeline** job.
2. Point it at the GitHub repo.
3. Keep `Jenkinsfile` at the repo root.
4. Make sure Jenkins discovers these branches.

## GitHub Actions bridge

The workflow `.github/workflows/trigger-jenkins-minikube.yml` expects these GitHub secrets:

| Secret | Meaning |
|--------|---------|
| `JENKINS_URL` | Base Jenkins URL |
| `JENKINS_USER` | Jenkins user with API token access |
| `JENKINS_API_TOKEN` | Jenkins API token |
| `JENKINS_JOB_PATH` | Multibranch branch job path, for example `job/LabFull-Multibranch/job/minikube-deploy` |

## Expected flow

1. `minikube-deploy` builds and deploys to the Ubuntu host.
2. The pipeline validates the public URL and notifies OpenClaw.
3. After manual approval, `aws-deploy` runs the AWS promotion stages.

## Required runtime tools

| Tool | Purpose |
|------|---------|
| `ssh` | Sync and execute on Ubuntu |
| `docker` | Build local images on Minikube host |
| `kubectl` | Apply and verify Kubernetes resources |
| `minikube` | Run the cluster on Ubuntu |
