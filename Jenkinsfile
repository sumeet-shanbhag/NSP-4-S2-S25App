pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = 'nsp-4-s2-s25app'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/sumeet-shanbhag/NSP-4-S2-S25App.git'
            }
        }

        stage('Build') {
            steps {
                sh 'docker-compose build'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker-compose down || true'
                sh 'docker-compose up -d'
            }
        }

        stage('Health Check') {
            steps {
                sh 'sleep 10 && curl -f http://localhost:8000/ || exit 1'
            }
        }
    }

    post {
        failure {
            sh 'docker-compose logs'
        }
    }
}