pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    parameters {
        string(name: 'gitBranch', defaultValue: '', description: 'Branch requested by GitHub Actions when this job is not multibranch')
        string(name: 'gitCommit', defaultValue: '', description: 'Commit requested by GitHub Actions when this job is not multibranch')
        string(name: 'MINIKUBE_HOST', defaultValue: '192.168.1.12', description: 'Ubuntu LAN host where Minikube runs')
        string(name: 'MINIKUBE_USER', defaultValue: 'mauro', description: 'SSH user for the Ubuntu LAN host')
        string(name: 'MINIKUBE_PROFILE', defaultValue: 'labfull', description: 'Minikube profile used on the Ubuntu host')
        string(name: 'PUBLIC_URL', defaultValue: 'https://labfull.maurocastro.cl', description: 'Public URL exposed by the reverse proxy')
        string(name: 'PUBLIC_DASHBOARD_URL', defaultValue: 'https://ministack.maurocastro.cl', description: 'Public Minikube dashboard URL exposed by the reverse proxy')
        booleanParam(name: 'APPLY_PUBLIC_PROXY', defaultValue: true, description: 'Create or refresh the public Nginx route for the Minikube dashboard')
        string(name: 'OPENCLAW_WEBHOOK_URL', defaultValue: 'http://192.168.1.12:18789/hooks/agent', description: 'OpenClaw hook endpoint used to notify the agent')
        string(name: 'OPENCLAW_WEBHOOK_TOKEN', defaultValue: '', description: 'Bearer token for the OpenClaw hook endpoint')
        string(name: 'NEXT_BRANCH_NAME', defaultValue: 'aws-deploy', description: 'Branch to promote after manual validation')
        string(name: 'NEXT_PIPELINE_SIGNAL', defaultValue: '1', description: 'Approval token the agent must return to start AWS')
        string(name: 'AWS_REGION', defaultValue: 'us-east-1', description: 'AWS region for the AWS deployment')
        string(name: 'AWS_RDS_HOST', defaultValue: '', description: 'RDS endpoint or CNAME used by backend and DB migration')
    }

    environment {
        APP_NAME = 'LabFull'
        BACKEND_IMAGE = 'labfull-backend:demo'
        FRONTEND_IMAGE = 'labfull-frontend:demo'
    }

    stages {
        stage('Resolve Branch') {
            steps {
                script {
                    def requestedBranch = params.gitBranch?.trim()
                    if (!requestedBranch && env.JOB_NAME == 'LabFull-platform-smoke') {
                        requestedBranch = 'minikube-deploy'
                    }
                    env.PIPELINE_BRANCH = env.BRANCH_NAME ?: (requestedBranch ?: 'main')
                    env.PIPELINE_COMMIT = params.gitCommit?.trim() ?: ''
                    def allowedBranches = ['main', 'minikube-deploy', 'aws-deploy']
                    if (!allowedBranches.contains(env.PIPELINE_BRANCH)) {
                        error("Unsupported branch for this multibranch pipeline: ${env.PIPELINE_BRANCH}")
                    }
                    currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.PIPELINE_BRANCH}"
                    echo "Running multibranch flow for ${env.PIPELINE_BRANCH}"
                }
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
                sh '''
                    set -eu
                    if [ -z "${BRANCH_NAME:-}" ]; then
                        git fetch origin "${PIPELINE_BRANCH}"
                        git checkout -B "${PIPELINE_BRANCH}" "origin/${PIPELINE_BRANCH}"
                    fi
                    if [ -n "${PIPELINE_COMMIT:-}" ]; then
                        git checkout "${PIPELINE_COMMIT}"
                    fi
                    git rev-parse --short HEAD
                '''
            }
        }

        stage('Summarize Changes') {
            steps {
                script {
                    env.LAST_COMMITS_SUMMARY = sh(
                        returnStdout: true,
                        script: '''
                            set -eu
                            git log --no-merges --pretty=format:'%s (%h)' -n 3
                        '''
                    ).trim().split('\n').findAll { it?.trim() }.join(' | ')
                    env.MINIKUBE_ROUTE = params.PUBLIC_URL?.trim() ?: 'https://labfull.maurocastro.cl'
                }
            }
        }

        stage('Validate Dependencies') {
            parallel {
                stage('Terraform') {
                    steps {
                        sh '''
                            set -eu
                            terraform version | head -1
                            aws --version
                        '''
                    }
                }
                stage('Platform Tools') {
                    steps {
                        sh '''
                            set -eu
                            git rev-parse --short HEAD
                            docker --version
                            ssh -V
                            kubectl version --client=true
                            curl --version | head -1
                        '''
                    }
                }
            }
        }

        stage('Build Inputs') {
            steps {
                sh '''
                    set -eu
                    echo "Backend image target: ${BACKEND_IMAGE}"
                    echo "Frontend image target: ${FRONTEND_IMAGE}"
                    echo "Kubernetes manifests:"
                    find k8s -maxdepth 1 -type f | sort
                '''
            }
        }

        stage('Deploy Minikube on Ubuntu') {
            when {
                expression { env.PIPELINE_BRANCH == 'minikube-deploy' }
            }
            steps {
                withEnv([
                    "MINIKUBE_USER=${params.MINIKUBE_USER}",
                    "MINIKUBE_HOST=${params.MINIKUBE_HOST}",
                    "MINIKUBE_PROFILE=${params.MINIKUBE_PROFILE}",
                    "PUBLIC_URL=${params.PUBLIC_URL}",
                    "PUBLIC_DASHBOARD_URL=${params.PUBLIC_DASHBOARD_URL}",
                    "APPLY_PUBLIC_PROXY=${params.APPLY_PUBLIC_PROXY ? '1' : '0'}"
                ]) {
                    sh '''
                        set -eu
                        bash ./scripts/deploy_minikube_labfull.sh
                    '''
                }
            }
        }

        stage('Validate Reverse Proxy') {
            when {
                expression { env.PIPELINE_BRANCH == 'minikube-deploy' }
            }
            steps {
                sh '''
                    set -eu
                    echo "Checking public URL: ${PUBLIC_URL}"
                    curl -fkSs "${PUBLIC_URL}" | grep -qi "LabFull"
                    curl -fkSs "${PUBLIC_URL}/api/health" | grep -qi '"status":"healthy"'
                    echo "Checking dashboard URL: ${PUBLIC_DASHBOARD_URL}"
                    curl -fkSs "${PUBLIC_DASHBOARD_URL}" | grep -Eqi "kubernetes|dashboard|login"
                '''
            }
        }

        stage('Notify ClawCode for Minikube') {
            when {
                expression { env.PIPELINE_BRANCH == 'minikube-deploy' }
            }
            steps {
                script {
                    if (params.OPENCLAW_WEBHOOK_URL && params.OPENCLAW_WEBHOOK_TOKEN) {
                        def changeSummary = env.LAST_COMMITS_SUMMARY ?: 'Sin commits recientes detectados.'
                        def publicRoute = env.MINIKUBE_ROUTE ?: params.PUBLIC_URL
                        def notificationText = """LabFull ya quedó arriba en ${publicRoute}.
Ruta publicada en Minikube: ${publicRoute}
Resumen ejecutivo: ${changeSummary}
Cuando termines la validación manual, responde ${params.NEXT_PIPELINE_SIGNAL} para iniciar ${params.NEXT_BRANCH_NAME}."""
                        def payload = groovy.json.JsonOutput.toJson([
                            agentId: 'jenki',
                            name: 'Jenki',
                            deliver: true,
                            channel: 'whatsapp',
                            to: '+56929683524',
                            message: notificationText,
                        ])
                        sh """
                            set -eu
                            response_file=\"${env.WORKSPACE}/.openclaw-response-minikube.txt\"
                            rm -f \"\$response_file\"
                            payload='${payload.replace("'", "'\"'\"'")}'
                            http_code=\$(curl -sS -o \"\$response_file\" -w \"%{http_code}\" -X POST \\
                                -H \"Authorization: Bearer ${params.OPENCLAW_WEBHOOK_TOKEN}\" \\
                                -H 'Content-Type: application/json' \\
                                -d \"\$payload\" \\
                                \"${params.OPENCLAW_WEBHOOK_URL}\")
                            echo "OPENCLAW_HTTP_CODE=\$http_code"
                            if [ -f \"\$response_file\" ]; then
                                echo "--- OPENCLAW_RESPONSE ---"
                                cat \"\$response_file\"
                                echo
                                echo "--- END OPENCLAW_RESPONSE ---"
                            fi
                            if [ \"\$http_code\" -lt 200 ] || [ \"\$http_code\" -ge 300 ]; then
                                echo "OpenClaw webhook returned non-2xx status: \$http_code" >&2
                                exit 1
                            fi
                        """
                        env.OPENCLAW_STATUS = 'sent'
                    } else {
                        echo "OPENCLAW_WEBHOOK_URL or OPENCLAW_WEBHOOK_TOKEN not configured; skipping agent notification"
                        env.OPENCLAW_STATUS = 'skipped'
                    }
                }
            }
        }

        stage('Approve AWS Deployment') {
            when {
                expression { env.PIPELINE_BRANCH == 'aws-deploy' }
            }
            steps {
                script {
                    if (params.NEXT_PIPELINE_SIGNAL != '1') {
                        error('AWS deployment not approved. The agent must send 1.')
                    }
                }
            }
        }

        stage('Deploy FE') {
            when {
                expression { env.PIPELINE_BRANCH == 'aws-deploy' }
            }
            steps {
                sh '''
                    set -eu
                    echo "Deploying frontend to AWS target"
                    echo "Frontend image will be published and routed through AWS"
                '''
            }
        }

        stage('Deploy BE') {
            when {
                expression { env.PIPELINE_BRANCH == 'aws-deploy' }
            }
            steps {
                sh """
                    AWS_REGION_VALUE='${params.AWS_REGION}'
                    AWS_RDS_HOST_VALUE='${params.AWS_RDS_HOST}'
                    set -eu
                    echo "Deploying backend to AWS target in \$AWS_REGION_VALUE"
                    if [ -n "\$AWS_RDS_HOST_VALUE" ]; then
                        echo "Backend will connect to RDS at \$AWS_RDS_HOST_VALUE"
                    else
                        echo "RDS endpoint not configured yet; using demo placeholder"
                    fi
                """
            }
        }

        stage('Deploy BD') {
            when {
                expression { env.PIPELINE_BRANCH == 'aws-deploy' }
            }
            steps {
                sh '''
                    set -eu
                    echo "Promoting database layer to AWS RDS"
                    echo "In a real run this stage would manage schema, migrations and connection strings"
                '''
            }
        }

        stage('Notify ClawCode on AWS') {
            when {
                expression { env.PIPELINE_BRANCH == 'aws-deploy' }
            }
            steps {
                script {
                    if (params.OPENCLAW_WEBHOOK_URL && params.OPENCLAW_WEBHOOK_TOKEN) {
                        def changeSummary = env.LAST_COMMITS_SUMMARY ?: 'Sin commits recientes detectados.'
                        def publicRoute = env.MINIKUBE_ROUTE ?: 'https://labfull.maurocastro.cl'
                        def notificationText = """AWS deployment terminado para LabFull: FE, BE y BD/RDS listos.
Ruta publicada en Minikube: ${publicRoute}
Resumen ejecutivo: ${changeSummary}"""
                        def payload = groovy.json.JsonOutput.toJson([
                            agentId: 'jenki',
                            name: 'Jenki',
                            deliver: true,
                            channel: 'whatsapp',
                            to: '+56929683524',
                            message: notificationText,
                        ])
                        sh """
                            set -eu
                            response_file=\"${env.WORKSPACE}/.openclaw-response-aws.txt\"
                            rm -f \"\$response_file\"
                            payload='${payload.replace("'", "'\"'\"'")}'
                            http_code=\$(curl -sS -o \"\$response_file\" -w \"%{http_code}\" -X POST \\
                                -H \"Authorization: Bearer ${params.OPENCLAW_WEBHOOK_TOKEN}\" \\
                                -H 'Content-Type: application/json' \\
                                -d \"\$payload\" \\
                                "${params.OPENCLAW_WEBHOOK_URL}")
                            echo "OPENCLAW_HTTP_CODE=\$http_code"
                            if [ -f \"\$response_file\" ]; then
                                echo "--- OPENCLAW_RESPONSE ---"
                                cat \"\$response_file\"
                                echo
                                echo "--- END OPENCLAW_RESPONSE ---"
                            fi
                            if [ \"\$http_code\" -lt 200 ] || [ \"\$http_code\" -ge 300 ]; then
                                echo "OpenClaw webhook returned non-2xx status: \$http_code" >&2
                                exit 1
                            fi
                        """
                        env.OPENCLAW_STATUS = 'sent'
                    } else {
                        echo "OPENCLAW_WEBHOOK_URL or OPENCLAW_WEBHOOK_TOKEN not configured; skipping notification"
                        env.OPENCLAW_STATUS = 'skipped'
                    }
                }
            }
        }

        stage('Main Branch Summary') {
            when {
                expression { env.PIPELINE_BRANCH == 'main' }
            }
            steps {
                sh '''
                    set -eu
                    echo "main branch is reserved for shared validation and merge hygiene"
                '''
            }
        }
    }

    post {
        success {
            script {
                def branch = env.PIPELINE_BRANCH ?: (env.BRANCH_NAME ?: 'main')
                def openclaw = env.OPENCLAW_STATUS ?: 'unknown'
                def result = currentBuild.currentResult ?: 'SUCCESS'
                currentBuild.description = "branch=${branch}; openclaw=${openclaw}; result=${result}"
            }
            echo "Multibranch flow completed for ${env.BRANCH_NAME ?: 'main'}."
        }
        failure {
            script {
                def branch = env.PIPELINE_BRANCH ?: (env.BRANCH_NAME ?: 'main')
                def openclaw = env.OPENCLAW_STATUS ?: 'unknown'
                def result = currentBuild.currentResult ?: 'FAILURE'
                currentBuild.description = "branch=${branch}; openclaw=${openclaw}; result=${result}"
            }
            echo 'Pipeline failed. Review the stage that stopped the flow.'
        }
        always {
            cleanWs()
        }
    }
}
