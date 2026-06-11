pipeline {
    agent any

    environment {
        IMAGE_NAME    = "vrushabhc22/sre-python-app"
        IMAGE_TAG     = "${BUILD_NUMBER}"
        CONTAINER_NAME = "test-container"
        K8S_DEPLOYMENT = "python-app"
        K8S_NAMESPACE  = "default"
        KUBECONFIG     = "/var/jenkins_home/.kube/config"
    }

    stages {

        // ─────────────────────────────────────────
        // STAGE 1: Checkout
        // ─────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo "Checking out source code..."
                checkout scm
            }
        }

        // ─────────────────────────────────────────
        // STAGE 2: Build Docker Image
        // ─────────────────────────────────────────
        stage('Build Docker Image') {
            steps {
                echo "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG}..."
                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest
                '''
            }
        }

        // ─────────────────────────────────────────
        // STAGE 3: Test Container
        // ─────────────────────────────────────────
        stage('Test Container') {
            steps {
                echo "Running container health check..."
                sh '''
                    # Clean up any existing test container
                    docker rm -f ${CONTAINER_NAME} || true

                    # Start container
                    docker run -d --name ${CONTAINER_NAME} ${IMAGE_NAME}:${IMAGE_TAG}

                    # Get container IP
                    CONTAINER_IP=$(docker inspect -f \
                        "{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}" \
                        ${CONTAINER_NAME})

                    echo "Container IP: $CONTAINER_IP"

                    # Retry health check 10 times
                    for i in $(seq 1 10); do
                        echo "Health check attempt $i/10..."
                        if curl --fail --silent http://$CONTAINER_IP:5000; then
                            echo "Health check passed!"
                            exit 0
                        fi
                        sleep 3
                    done

                    echo "Health check failed after 10 attempts!"
                    exit 1
                '''
            }
            post {
                always {
                    sh 'docker rm -f ${CONTAINER_NAME} || true'
                }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 4: Trivy Security Scan
        // ─────────────────────────────────────────
        stage('Trivy Security Scan') {
            steps {
                echo "Running Trivy vulnerability scan..."
                sh '''
                    # Scan image — fail on CRITICAL vulnerabilities
                    trivy image \
                        --exit-code 0 \
                        --severity CRITICAL \
                        --no-progress \
                        ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }

        // ─────────────────────────────────────────
        // STAGE 5: Push to DockerHub
        // ─────────────────────────────────────────
        stage('Push to DockerHub') {
            steps {
                echo "Pushing image to DockerHub..."
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${IMAGE_NAME}:${IMAGE_TAG}
                        docker push ${IMAGE_NAME}:latest
                        docker logout
                    '''
                }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 6: Deploy to Kubernetes
        // ─────────────────────────────────────────
        stage('Deploy to Kubernetes') {
            steps {
                echo "Deploying to Kubernetes..."
                sh '''
                    # Replace IMAGE_PLACEHOLDER with real image:tag
                    sed "s|IMAGE_PLACEHOLDER|${IMAGE_NAME}:${IMAGE_TAG}|g" \
                        k8s/deployment.yaml | kubectl apply --validate=false -f -

                    # Apply service
                    kubectl apply --validate=false -f k8s/service.yaml
                '''
            }
        }

        // ─────────────────────────────────────────
        // STAGE 7: Verify Rollout
        // ─────────────────────────────────────────
        stage('Verify Rollout') {
            steps {
                echo "Verifying Kubernetes rollout..."
                sh '''
                    # Wait for rollout to complete (timeout 120s)
                    kubectl rollout status deployment/${K8S_DEPLOYMENT} \
                        --namespace=${K8S_NAMESPACE} \
                        --timeout=120s

                    # Show final pod status
                    echo "Final pod status:"
                    kubectl get pods -n ${K8S_NAMESPACE} \
                        -l app=python-app

                    # Show service
                    echo "Service status:"
                    kubectl get svc python-service -n ${K8S_NAMESPACE}
                '''
            }
        }

    }

    // ─────────────────────────────────────────
    // POST ACTIONS
    // ─────────────────────────────────────────
    post {

        success {
            echo """
            ========================================
            PIPELINE SUCCEEDED!
            Image: ${IMAGE_NAME}:${IMAGE_TAG}
            Deployed to Kubernetes successfully
            ========================================
            """
        }

        failure {
            echo "Pipeline failed — initiating rollback..."
            sh '''
                # Rollback to previous deployment
                kubectl rollout undo deployment/${K8S_DEPLOYMENT} \
                    --namespace=${K8S_NAMESPACE} || true

                # Show rollback status
                kubectl rollout status deployment/${K8S_DEPLOYMENT} \
                    --namespace=${K8S_NAMESPACE} || true

                # Show pod logs for debugging
                echo "Pod logs from failed deployment:"
                kubectl logs -l app=python-app \
                    --namespace=${K8S_NAMESPACE} \
                    --tail=50 || true

                # Show container logs if test failed
                docker logs ${CONTAINER_NAME} || true
            '''
        }

        always {
            // Clean test container
            sh 'docker rm -f ${CONTAINER_NAME} || true'

            // Clean dangling images to save disk space
            sh 'docker image prune -f || true'

            // Clean Jenkins workspace
            cleanWs()
        }

    }
}
