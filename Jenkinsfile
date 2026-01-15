pipeline {
    agent any
    
    environment {
        DOCKER_HUB_REPO = 'priteecha'
        BACKEND_IMAGE = "${DOCKER_HUB_REPO}/blog-backend"
        FRONTEND_IMAGE = "${DOCKER_HUB_REPO}/blog-frontend"
        IMAGE_TAG = "${BUILD_NUMBER}"
        K8S_NAMESPACE = 'blog-app'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '========== Checking out code =========='
                checkout scm
            }
        }
        
        stage('Build Images') {
            parallel {

                stage('Build Backend Image') {
                    steps {
                        sh '''
                            cd backend
                            docker build -t ${BACKEND_IMAGE}:${IMAGE_TAG} .
                            docker tag ${BACKEND_IMAGE}:${IMAGE_TAG} ${BACKEND_IMAGE}:latest
                        '''
                    }
                }

                stage('Build Frontend Image') {
                    steps {
                        sh '''
                            cd frontend
                            docker build -t ${FRONTEND_IMAGE}:${IMAGE_TAG} .
                            docker tag ${FRONTEND_IMAGE}:${IMAGE_TAG} ${FRONTEND_IMAGE}:latest
                        '''
                    }
                }
            }
        }

        stage('Image Security Scan') {
            steps {
                sh '''
                    trivy image --severity HIGH,CRITICAL --exit-code 1 ${BACKEND_IMAGE}:${IMAGE_TAG}
                    trivy image --severity HIGH,CRITICAL --exit-code 1 ${FRONTEND_IMAGE}:${IMAGE_TAG}
                '''
            }
        }
        stage('Push Images to Docker Hub') {
            steps {
                echo '========== Pushing images to Docker Hub =========='
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', 
                                                 usernameVariable: 'DOCKER_USER', 
                                                 passwordVariable: 'DOCKER_PASS')]) {
                    sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
                    sh "docker push ${BACKEND_IMAGE}:${IMAGE_TAG}"
                    sh "docker push ${BACKEND_IMAGE}:latest"
                    sh "docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}"
                    sh "docker push ${FRONTEND_IMAGE}:latest"
                    sh "docker logout"
                }
            }
        }
        
        stage('K8s Precheck') {
            steps {
                sh '''
                    kubectl get ns ${K8S_NAMESPACE} || kubectl create ns ${K8S_NAMESPACE}
                '''
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
                echo '========== Deploying to Kubernetes =========='
                script {
                    sh '''
                        # Update backend deployment with new image
                        kubectl set image deployment/backend backend=${BACKEND_IMAGE}:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        
                        # Update frontend deployment with new image
                        kubectl set image deployment/frontend frontend=${FRONTEND_IMAGE}:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        
                        echo "Waiting for rollout to complete..."
                        kubectl rollout status deployment/backend -n ${K8S_NAMESPACE} --timeout=5m
                        kubectl rollout status deployment/frontend -n ${K8S_NAMESPACE} --timeout=5m
                    '''
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                echo '========== Verifying Deployment =========='
                script {
                    sh '''
                        echo "=== Pods Status ==="
                        kubectl get pods -n ${K8S_NAMESPACE}
                        
                        echo "=== Services ==="
                        kubectl get svc -n ${K8S_NAMESPACE}
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '========== ✅ Deployment Successful =========='
            echo "Backend Image: ${BACKEND_IMAGE}:${IMAGE_TAG}"
            echo "Frontend Image: ${FRONTEND_IMAGE}:${IMAGE_TAG}"
            echo 'Access app via NodePort or LoadBalancer'
        }
        failure {
            echo '========== ❌ Deployment Failed. Rolling back =========='
            sh '''
                kubectl rollout undo deployment/backend -n ${K8S_NAMESPACE} || true
                kubectl rollout undo deployment/frontend -n ${K8S_NAMESPACE} || true
            '''
        }
        always {
            echo '========== Cleaning up =========='
            sh 'docker image prune -f || true'
        }
    }
}
