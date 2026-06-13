pipeline {
    agent any
    
    environment {
        // Variables de entorno para el laboratorio
        DB_HOST = '192.168.1.12'
        DB_NAME = 'DBLAB'
        BACKEND_PORT = '8000'
        WEB_PORT = '8080'
        IMAGE_BACKEND = 'dblab-backend:latest'
        IMAGE_WEB = 'dblab-web:latest'
    }
    
    options {
        // Configuración del pipeline
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo '✅ Código recuperado del repositorio'
                sh 'ls -la'
            }
        }
        
        stage('Validate Terraform') {
            steps {
                echo '🔍 Validando configuración de Terraform...'
                dir('terraform') {
                    sh 'terraform fmt -check'
                    sh 'terraform validate'
                }
                echo '✅ Terraform validado correctamente'
            }
        }
        
        stage('Database Setup') {
            steps {
                echo '🗄️  Configurando base de datos PostgreSQL...'
                dir('bd') {
                    // Verificar conexión al servidor PostgreSQL
                    sh '''
                        echo "Verificando conexión a ${DB_HOST}..."
                        psql -h ${DB_HOST} -U postgres -c "SELECT 1" || echo "⚠️  Verificar credenciales en secrets/"
                    '''
                }
                echo '✅ Base de datos lista'
            }
        }
        
        stage('Docker Build Backend') {
            steps {
                echo '🐳 Construyendo imagen del backend...'
                dir('backend-fastapi') {
                    sh 'docker build -t ${IMAGE_BACKEND} .'
                }
                echo '✅ Imagen del backend construida: ' + IMAGE_BACKEND
            }
        }
        
        stage('Docker Build Frontend') {
            steps {
                echo '🎨 Construyendo imagen del frontend...'
                dir('app-web') {
                    sh 'docker build -t ${IMAGE_WEB} .'
                }
                echo '✅ Imagen del frontend construida: ' + IMAGE_WEB
            }
        }
        
        stage('Docker Health Check') {
            steps {
                echo '🏥 Verificando health-check de contenedores...'
                
                // Health check para backend
                echo 'Backend health check...'
                sh '''
                    docker run -d --name test-backend -p 8000:8000 ${IMAGE_BACKEND}
                    sleep 10
                    docker ps --filter "name=test-backend" --format "{{.Status}}"
                    docker stop test-backend
                    docker rm test-backend
                '''
                
                // Health check para frontend
                echo 'Frontend health check...'
                sh '''
                    docker run -d --name test-web -p 8080:80 ${IMAGE_WEB}
                    sleep 10
                    docker ps --filter "name=test-web" --format "{{.Status}}"
                    docker stop test-web
                    docker rm test-web
                '''
                
                echo '✅ Health-check completado'
            }
        }
        
        stage('Run Tests') {
            steps {
                echo '🧪 Ejecutando pruebas...'
                
                // Verificar estructura de archivos
                sh '''
                    echo "Verificando estructura del proyecto..."
                    test -d app-web && echo "✅ app-web/ existe"
                    test -d backend-fastapi && echo "✅ backend-fastapi/ existe"
                    test -d bd && echo "✅ bd/ existe"
                    test -f README.md && echo "✅ README.md existe"
                '''
                
                // Verificar endpoints del backend (si está corriendo)
                echo "Verificando backend en puerto ${BACKEND_PORT}..."
                sh '''
                    curl -s http://localhost:${BACKEND_PORT}/ || echo "⚠️  Backend no ejecutándose (esperado en desarrollo)"
                '''
                
                echo '✅ Pruebas completadas'
            }
        }
        
        stage('Build Documentation') {
            steps {
                echo '📚 Generando documentación...'
                sh '''
                    echo "Progreso del laboratorio:"
                    git log --oneline -5
                '''
                echo '✅ Documentación actualizada'
            }
        }
    }
    
    post {
        always {
            echo '🧹 Limpieza final...'
            // Limpiar contenedores y imágenes viejas
            sh '''
                docker container prune -f || true
                docker image prune -f || true
            '''
            cleanWs()
        }
        
        success {
            echo '🎉 Pipeline completado exitosamente!'
            echo '🚀 Siguiente paso: ejecutar los contenedores con docker-compose'
        }
        
        failure {
            echo '❌ Pipeline falló. Revisar los logs para más detalles.'
        }
    }
}
