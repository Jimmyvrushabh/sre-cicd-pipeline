pipeline {
    agent any

    environment {
        IMAGE_NAME = "sre-python-app"
        IMAGE_TAG  = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .'
            }
        }

        stage('Verify Docker Image') {
            steps {
                sh 'docker images | grep ${IMAGE_NAME}'
            }
        }

        stage('Run Container Test') {
            steps {
                sh '''
                    # Clean up any existing container
                    docker rm -f test-container || true

                    # Start the container (no -p needed, we use container IP)
                    docker run -d --name test-container ${IMAGE_NAME}:${IMAGE_TAG}

                    # Get container IP directly (bypasses localhost networking issue)
                    CONTAINER_IP=$(docker inspect -f \
                        '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
                        test-container)

                    echo "Container IP: $CONTAINER_IP"

                    # Retry curl up to 10 times (handles slow startup)
                    for i in $(seq 1 10); do
                        echo "Health check attempt $i/10..."
                        curl --fail http://$CONTAINER_IP:5000 && echo "Health check passed!" && break
                        sleep 3
                    done
                '''
            }
        }

        stage('Tag for Registry') {
            steps {
                sh '''
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest
                    echo "Tagged ${IMAGE_NAME}:${IMAGE_TAG} as latest"
                '''
            }
        }

    }

    post {
        always {
            sh 'docker rm -f test-container || true'
            cleanWs()
        }
        success {
            echo "Pipeline passed! Image: ${IMAGE_NAME}:${IMAGE_TAG}"
        }
        failure {
            echo "Pipeline failed! Check logs above."
            sh 'docker logs test-container || true'
        }
    }
}
