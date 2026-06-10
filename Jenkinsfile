pipeline {
    agent any

    environment {
        IMAGE_NAME = "sre-python-app"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                '''
            }
        }

        stage('Verify Docker Image') {
            steps {
                sh '''
                docker images
                '''
            }
        }

        stage('Run Container Test') {
            steps {
                sh '''
                docker rm -f test-container || true

                docker run -d \
                --name test-container \
                -p 5000:5000 \
                ${IMAGE_NAME}:${IMAGE_TAG}

                sleep 10

                curl --fail http://localhost:5000

                docker stop test-container
                docker rm test-container
                '''
            }
        }

    }

    post {
        always {
            cleanWs()
        }
    }
}
