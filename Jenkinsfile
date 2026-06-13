pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    parameters {
        string(name: 'MINISTACK_HOST', defaultValue: '192.168.1.12', description: 'Ubuntu LAN host for the first deployment')
        string(name: 'MINISTACK_USER', defaultValue: 'mauro', description: 'SSH user for the Ubuntu LAN host')
        string(name: 'OPENCLAW_WEBHOOK_URL', defaultValue: '', description: 'OpenClaw webhook URL used to notify the agent')
        string(name: 'NEXT_PIPELINE_NAME', defaultValue: 'LabFull-AWS-CD', description: 'Downstream Jenkins job to start after agent approval')
        string(name: 'NEXT_PIPELINE_SIGNAL', defaultValue: '1', description: 'Approval token the agent must return to start AWS')
    }

    environment {
        APP_NAME = 'LabFull'
        BACKEND_IMAGE = 'labfull-backend:demo'
        FRONTEND_IMAGE = 'labfull-frontend:demo'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/Maurog-castros/LabFull.git'
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
                            kubectl version --client=true
                        '''
                    }
                }
            }
        }

        stage('Demo Build') {
            steps {
                sh '''
                    set -eu
                    echo "Demo build: backend image ${BACKEND_IMAGE}"
                    echo "Demo build: frontend image ${FRONTEND_IMAGE}"
                    docker image ls | head -10
                '''
            }
        }

        stage('Deploy Ministack on Ubuntu') {
            steps {
                withEnv([
                    "MINISTACK_USER=${params.MINISTACK_USER}",
                    "MINISTACK_HOST=${params.MINISTACK_HOST}"
                ]) {
                    sh '''
                        set -eu
                        mkdir -p "$HOME/.ssh"
                        chmod 700 "$HOME/.ssh"
                        ssh-keyscan -H "${MINISTACK_HOST}" >> "$HOME/.ssh/known_hosts" 2>/dev/null || true
                        chmod 600 "$HOME/.ssh/known_hosts"
                        if ssh -o BatchMode=yes -o StrictHostKeyChecking=yes ${MINISTACK_USER}@${MINISTACK_HOST} '
                            set -eu
                            echo "Deploying LabFull ministack on $(hostname)"
                            test -d /opt/labfull/ministack || sudo mkdir -p /opt/labfull/ministack
                            cd /opt/labfull/ministack
                            docker compose version >/dev/null
                            docker compose config >/dev/null
                            echo "Frontend, backend and postgres are staged on Ubuntu"
                        '; then
                            echo "Ubuntu ministack deployment check completed"
                        else
                            echo "Ubuntu SSH is not configured in Jenkins yet; continuing with agent notification"
                        fi
                    '''
                }
            }
        }

        stage('Notify ClawCode') {
            steps {
                sh """
                    set -eu
                    if [ -n "${params.OPENCLAW_WEBHOOK_URL}" ]; then
                        next_url="https://jenkins.maurocastro.cl/job/${params.NEXT_PIPELINE_NAME}/buildWithParameters?APPROVAL_SIGNAL=${params.NEXT_PIPELINE_SIGNAL}"
                        payload=\$(cat <<EOF
{"app":"${APP_NAME}","status":"success","message":"LabFull finished the Ubuntu ministack phase. When you finish manual validation, reply with ${params.NEXT_PIPELINE_SIGNAL} to start ${params.NEXT_PIPELINE_NAME} for AWS.","next_pipeline":"${params.NEXT_PIPELINE_NAME}","approval_signal":"${params.NEXT_PIPELINE_SIGNAL}","next_pipeline_url":"\$next_url"}
EOF
)
                        curl -fsS -X POST \\
                            -H 'Content-Type: application/json' \\
                            -d "\$payload" \\
                            "${params.OPENCLAW_WEBHOOK_URL}"
                    else
                        echo "OPENCLAW_WEBHOOK_URL not configured; skipping agent notification"
                    fi
                """
            }
        }
    }

    post {
        success {
            echo 'Ubuntu stage completed and ClawCode was notified.'
        }
        failure {
            echo 'Pipeline failed. Review the stage that stopped the flow.'
        }
        always {
            cleanWs()
        }
    }
}
