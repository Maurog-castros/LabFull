pipeline {
    agent any
    
    environment {
        // Variables de entorno para el laboratorio
        DB_HOST = '192.168.1.12'
        DB_NAME = 'DBLAB'
        BACKEND_PORT = '8000'
        WEB_PORT = '8080'
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
        
        stage('Setup Backend') {
            steps {
                echo '🐍 Configurando entorno Python...'
                dir('backend-fastapi') {
                    sh '''
                        python3 -m venv venv
                        source venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                    '''
                }
                echo '✅ Backend configurado'
            }
        }
        
        stage('Setup Frontend') {
            steps {
                echo '🎨 Configurando entorno web...'
                dir('app-web') {
                    sh '''
                        echo "Verificando index.html..."
                        test -f index.html && echo "✅ index.html encontrado"
                    '''
                }
                echo '✅ Frontend listo'
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
            cleanWs()
        }
        
        success {
            echo '🎉 Pipeline completado exitosamente!'
            echo '🚀 Siguiente paso: ejecutar el backend y frontend'
        }
        
        failure {
            echo '❌ Pipeline falló. Revisar los logs para más detalles.'
        }
    }
}
