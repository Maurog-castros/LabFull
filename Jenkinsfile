pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    parameters {
        string(name: 'MINIKUBE_HOST', defaultValue: '192.168.1.12', description: 'Ubuntu LAN host where Minikube runs')
        string(name: 'MINIKUBE_USER', defaultValue: 'mauro', description: 'SSH user for the Ubuntu LAN host')
        string(name: 'MINIKUBE_PROFILE', defaultValue: 'labfull', description: 'Minikube profile used on the Ubuntu host')
        string(name: 'PUBLIC_URL', defaultValue: 'https://labfull.maurocastro.cl', description: 'Public URL exposed by the reverse proxy')
        string(name: 'OPENCLAW_WEBHOOK_URL', defaultValue: '', description: 'OpenClaw webhook URL used to notify the agent')
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
                    env.PIPELINE_BRANCH = env.BRANCH_NAME ?: 'main'
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
                sh 'git rev-parse --short HEAD'
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
                branch 'minikube-deploy'
            }
            steps {
                withEnv([
                    "MINIKUBE_USER=${params.MINIKUBE_USER}",
                    "MINIKUBE_HOST=${params.MINIKUBE_HOST}",
                    "MINIKUBE_PROFILE=${params.MINIKUBE_PROFILE}",
                    "PUBLIC_URL=${params.PUBLIC_URL}"
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
                branch 'minikube-deploy'
            }
            steps {
                sh '''
                    set -eu
                    echo "Checking public URL: ${PUBLIC_URL}"
                    curl -fkSs "${PUBLIC_URL}" | grep -qi "LabFull"
                    curl -fkSs "${PUBLIC_URL}/api/health" | grep -qi '"status":"healthy"'
                '''
            }
        }

        stage('Notify ClawCode for AWS') {
            when {
                branch 'minikube-deploy'
            }
            steps {
                script {
                    if (params.OPENCLAW_WEBHOOK_URL) {
                        sh """
                            set -eu
                            response_file=\"${env.WORKSPACE}/.openclaw-response-minikube.txt\"
                            rm -f \"\$response_file\"
                            payload=\$(cat <<EOF
{"app":"${APP_NAME}","status":"success","message":"LabFull is now live at ${params.PUBLIC_URL}. When validation passes, reply with ${params.NEXT_PIPELINE_SIGNAL} and promote branch ${params.NEXT_BRANCH_NAME} for AWS.","next_branch":"${params.NEXT_BRANCH_NAME}","approval_signal":"${params.NEXT_PIPELINE_SIGNAL}","public_url":"${params.PUBLIC_URL}"}
EOF
)
                            http_code=\$(curl -sS -o \"\$response_file\" -w \"%{http_code}\" -X POST \\
                                -H 'Content-Type: application/json' \\
                                -d "\$payload" \\
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
                        echo "OPENCLAW_WEBHOOK_URL not configured; skipping agent notification"
                        env.OPENCLAW_STATUS = 'skipped'
                    }
                }
            }
        }

        stage('Approve AWS Deployment') {
            when {
                branch 'aws-deploy'
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
                branch 'aws-deploy'
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
                branch 'aws-deploy'
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
                branch 'aws-deploy'
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
                branch 'aws-deploy'
            }
            steps {
                script {
                    if (params.OPENCLAW_WEBHOOK_URL) {
                        sh """
                            set -eu
                            response_file=\"${env.WORKSPACE}/.openclaw-response-aws.txt\"
                            rm -f \"\$response_file\"
                            payload=\$(cat <<EOF
{"app":"${APP_NAME}","status":"success","message":"AWS deployment finished for branch aws-deploy: FE, BE and BD on RDS."}
EOF
)
                            http_code=\$(curl -sS -o \"\$response_file\" -w \"%{http_code}\" -X POST \\
                                -H 'Content-Type: application/json' \\
                                -d "\$payload" \\
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
                        echo "OPENCLAW_WEBHOOK_URL not configured; skipping notification"
                        env.OPENCLAW_STATUS = 'skipped'
                    }
                }
            }
        }

        stage('Main Branch Summary') {
            when {
                branch 'main'
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
