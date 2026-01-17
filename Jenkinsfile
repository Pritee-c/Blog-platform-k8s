pipeline {
    agent any
    
    environment {
        // ECR Configuration - using IAM role on EC2
        AWS_REGION = 'us-east-1'
        AWS_ACCOUNT_ID = credentials('aws-account-id')  
        ECR_REGISTRY = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        
        // Microservice Images
        AUTH_SERVICE_IMAGE = "${ECR_REGISTRY}/blog-auth"
        POST_SERVICE_IMAGE = "${ECR_REGISTRY}/blog-post"
        COMMENT_SERVICE_IMAGE = "${ECR_REGISTRY}/blog-comment"
        GATEWAY_IMAGE = "${ECR_REGISTRY}/blog-gateway"
        FRONTEND_IMAGE = "${ECR_REGISTRY}/blog-frontend"
        
        IMAGE_TAG = "${BUILD_NUMBER}"
        
        // Kubernetes
        K8S_NAMESPACE = 'blog-app'
        K8S_CLUSTER = 'blog-eks'
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

                stage('Build Auth Service Image') {
                    steps {
                        sh '''
                            cd services/auth
                            docker build -t ${AUTH_SERVICE_IMAGE}:${IMAGE_TAG} .
                            docker tag ${AUTH_SERVICE_IMAGE}:${IMAGE_TAG} ${AUTH_SERVICE_IMAGE}:latest
                        '''
                    }
                }

                stage('Build Post Service Image') {
                    steps {
                        sh '''
                            cd services/post
                            docker build -t ${POST_SERVICE_IMAGE}:${IMAGE_TAG} .
                            docker tag ${POST_SERVICE_IMAGE}:${IMAGE_TAG} ${POST_SERVICE_IMAGE}:latest
                        '''
                    }
                }

                stage('Build Comment Service Image') {
                    steps {
                        sh '''
                            cd services/comment
                            docker build -t ${COMMENT_SERVICE_IMAGE}:${IMAGE_TAG} .
                            docker tag ${COMMENT_SERVICE_IMAGE}:${IMAGE_TAG} ${COMMENT_SERVICE_IMAGE}:latest
                        '''
                    }
                }

                stage('Build API Gateway Image') {
                    steps {
                        sh '''
                            cd gateway
                            docker build -t ${GATEWAY_IMAGE}:${IMAGE_TAG} .
                            docker tag ${GATEWAY_IMAGE}:${IMAGE_TAG} ${GATEWAY_IMAGE}:latest
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
            when {
                expression { fileExists('/usr/bin/trivy') }
            }
            steps {
                echo '========== Scanning images for vulnerabilities =========='
                sh '''
                    trivy image --severity HIGH,CRITICAL ${AUTH_SERVICE_IMAGE}:${IMAGE_TAG} || true
                    trivy image --severity HIGH,CRITICAL ${POST_SERVICE_IMAGE}:${IMAGE_TAG} || true
                    trivy image --severity HIGH,CRITICAL ${COMMENT_SERVICE_IMAGE}:${IMAGE_TAG} || true
                    trivy image --severity HIGH,CRITICAL ${GATEWAY_IMAGE}:${IMAGE_TAG} || true
                    trivy image --severity HIGH,CRITICAL ${FRONTEND_IMAGE}:${IMAGE_TAG} || true
                '''
            }
        }
        stage('Push Images to ECR') {
            steps {
                echo '========== Pushing images to ECR =========='
                sh '''
                    # Login to ECR
                    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                    
                    # Push all microservice images
                    docker push ${AUTH_SERVICE_IMAGE}:${IMAGE_TAG}
                    docker push ${AUTH_SERVICE_IMAGE}:latest
                    
                    docker push ${POST_SERVICE_IMAGE}:${IMAGE_TAG}
                    docker push ${POST_SERVICE_IMAGE}:latest
                    
                    docker push ${COMMENT_SERVICE_IMAGE}:${IMAGE_TAG}
                    docker push ${COMMENT_SERVICE_IMAGE}:latest
                    
                    docker push ${GATEWAY_IMAGE}:${IMAGE_TAG}
                    docker push ${GATEWAY_IMAGE}:latest
                    
                    # Push frontend
                    docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}
                    docker push ${FRONTEND_IMAGE}:latest
                    
                    echo "All images pushed to ECR successfully!"
                '''
            }
        }
        
        stage('K8s Precheck') {
            steps {
                echo '========== Verifying EKS cluster access =========='
                sh '''
                    # Update kubeconfig for EKS
                    aws eks update-kubeconfig --name ${K8S_CLUSTER} --region ${AWS_REGION}
                    
                    # Verify cluster access
                    kubectl cluster-info
                    
                    # Create namespace if it doesn't exist
                    kubectl get ns ${K8S_NAMESPACE} || kubectl create ns ${K8S_NAMESPACE}
                '''
            }
        }
        stage('Deploy Microservices') {
            steps {
                echo '========== Deploying microservices to Kubernetes =========='
                script {
                    sh '''
                        # Apply microservices manifest
                        kubectl apply -f k8s/microservices.yaml -n ${K8S_NAMESPACE}
                        
                        # Update images
                        kubectl set image deployment/auth-service auth-service=${AUTH_SERVICE_IMAGE}:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        kubectl set image deployment/post-service post-service=${POST_SERVICE_IMAGE}:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        kubectl set image deployment/comment-service comment-service=${COMMENT_SERVICE_IMAGE}:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        kubectl set image deployment/api-gateway api-gateway=${GATEWAY_IMAGE}:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        
                        echo "Waiting for microservices rollout..."
                        kubectl rollout status deployment/auth-service -n ${K8S_NAMESPACE} --timeout=5m
                        kubectl rollout status deployment/post-service -n ${K8S_NAMESPACE} --timeout=5m
                        kubectl rollout status deployment/comment-service -n ${K8S_NAMESPACE} --timeout=5m
                        kubectl rollout status deployment/api-gateway -n ${K8S_NAMESPACE} --timeout=5m
                    '''
                }
            }
        }

        stage('Deploy Frontend') {
            steps {
                echo '========== Deploying frontend to Kubernetes =========='
                script {
                    sh '''
                        # Update frontend deployment with new image
                        kubectl set image deployment/frontend frontend=${FRONTEND_IMAGE}:${IMAGE_TAG} -n ${K8S_NAMESPACE}
                        
                        echo "Waiting for frontend rollout to complete..."
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
                        echo "=== All Pods Status ==="
                        kubectl get pods -n ${K8S_NAMESPACE}
                        
                        echo "=== All Services ==="
                        kubectl get svc -n ${K8S_NAMESPACE}
                        
                        echo "=== Microservices Endpoints ==="
                        kubectl get endpoints -n ${K8S_NAMESPACE}
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '========== ✅ Deployment Successful =========='
            echo "Auth Service Image: ${AUTH_SERVICE_IMAGE}:${IMAGE_TAG}"
            echo "Post Service Image: ${POST_SERVICE_IMAGE}:${IMAGE_TAG}"
            echo "Comment Service Image: ${COMMENT_SERVICE_IMAGE}:${IMAGE_TAG}"
            echo "API Gateway Image: ${GATEWAY_IMAGE}:${IMAGE_TAG}"
            echo "Frontend Image: ${FRONTEND_IMAGE}:${IMAGE_TAG}"
            echo 'Access app via LoadBalancer DNS'
        }
        failure {
            echo '========== ❌ Deployment Failed. Rolling back =========='
            sh '''
                kubectl rollout undo deployment/auth-service -n ${K8S_NAMESPACE} || true
                kubectl rollout undo deployment/post-service -n ${K8S_NAMESPACE} || true
                kubectl rollout undo deployment/comment-service -n ${K8S_NAMESPACE} || true
                kubectl rollout undo deployment/api-gateway -n ${K8S_NAMESPACE} || true
                kubectl rollout undo deployment/frontend -n ${K8S_NAMESPACE} || true
            '''
        }
        always {
            echo '========== Cleaning up =========='
            sh 'docker image prune -f || true'
        }
    }
}
