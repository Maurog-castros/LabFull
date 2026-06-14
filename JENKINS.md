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
5. Expose the last completed build through `/lastCompletedBuild/api/json` and `/lastCompletedBuild/wfapi/describe` so the UI can render the dashboard.

## GitHub Actions bridge

The workflows `.github/workflows/trigger-jenkins-minikube.yml` and `.github/workflows/trigger-jenkins-aws.yml` expect these GitHub secrets:

| Secret | Meaning |
|--------|---------|
| `JENKINS_URL` | Base Jenkins URL |
| `JENKINS_JOB_NAME` | Jenkins job name triggered by GitHub Actions, for example `LabFull-AWS-CD` |
| `JENKINS_USER` | Jenkins user with API token access |
| `JENKINS_API_TOKEN` | Jenkins API token |
| `OPENCLAW_WEBHOOK_URL` | OpenClaw hook endpoint, for example `http://192.168.1.12:18789/hooks/agent` |
| `OPENCLAW_WEBHOOK_TOKEN` | Bearer token accepted by the OpenClaw hook endpoint |

## Expected flow

1. `minikube-deploy` builds and deploys to the Ubuntu host.
2. The pipeline validates the public URL and notifies OpenClaw.
3. After manual approval, `aws-deploy` runs the AWS promotion stages.
4. `GET /api/pipeline/latest` reads Jenkins and shows the latest status inside the web app.
5. `GET /api/containers/status` shows the runtime inventory in the web app.

## Required runtime tools

| Tool | Purpose |
|------|---------|
| `ssh` | Sync and execute on Ubuntu |
| `docker` | Build local images on Minikube host |
| `kubectl` | Apply and verify Kubernetes resources |
| `minikube` | Run the cluster on Ubuntu |
