pipeline {
    agent any
    
    environment {
        // ECR Configuration - using IAM role on EC2
        AWS_REGION = 'us-east-1'
        AWS_ACCOUNT_ID = credentials('aws-account-id')  
        ECR_REGISTRY = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        BACKEND_IMAGE = "${ECR_REGISTRY}/blog-backend"
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
            when {
                expression { fileExists('/usr/bin/trivy') }
            }
            steps {
                echo '========== Scanning images for vulnerabilities =========='
                sh '''
                    trivy image --severity HIGH,CRITICAL ${BACKEND_IMAGE}:${IMAGE_TAG} || true
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
                    
                    # Push backend
                    docker push ${BACKEND_IMAGE}:${IMAGE_TAG}
                    docker push ${BACKEND_IMAGE}:latest
                    
                    # Push frontend
                    docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}
                    docker push ${FRONTEND_IMAGE}:latest
                    
                    echo "Images pushed to ECR successfully!"
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
