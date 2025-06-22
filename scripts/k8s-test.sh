#!/bin/bash

# Kubernetes cluster test script for Merlai
# AI-generated script - verification required before production use

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Merlai Kubernetes cluster test..."

# Check required tools
check_requirements() {
    echo "📋 Checking required tools..."
    
    if ! command -v kubectl &> /dev/null; then
        echo "❌ kubectl not found. Please install it."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo "❌ docker not found. Please install it."
        exit 1
    fi
    
    echo "✅ Required tools verified"
}

# Check cluster connection
check_cluster() {
    echo "🔍 Checking Kubernetes cluster connection..."
    
    if ! kubectl cluster-info &> /dev/null; then
        echo "❌ Cannot connect to Kubernetes cluster."
        echo "   - Run 'minikube start' or 'kind create cluster'"
        exit 1
    fi
    
    echo "✅ Cluster connection verified"
}

# Build and push image
build_and_push_image() {
    echo "🏗️  Building Docker image..."
    
    cd "$PROJECT_ROOT"
    
    # Build CPU-only image
    docker build -f docker/Dockerfile.cpu -t merlai:latest --target production .
    
    # Tag for local cluster
    if kubectl config current-context | grep -q "minikube"; then
        echo "📦 Detected minikube environment - loading image to minikube..."
        minikube image load merlai:latest
    elif kubectl config current-context | grep -q "kind"; then
        echo "📦 Detected kind environment - loading image to kind..."
        kind load docker-image merlai:latest
    else
        echo "⚠️  Local cluster environment not detected. Please push image manually."
    fi
    
    echo "✅ Image build completed"
}

# Deploy Kubernetes resources
deploy_to_k8s() {
    echo "🚀 Deploying Kubernetes resources..."
    
    cd "$PROJECT_ROOT/k8s"
    
    # Create namespace
    kubectl apply -f namespace.yaml
    
    # Create ConfigMap
    kubectl apply -f configmap.yaml
    
    # Create deployment
    kubectl apply -f merlai-deployment.yaml
    
    # Create Ingress (optional)
    if [ -f "merlai-ingress.yaml" ]; then
        kubectl apply -f merlai-ingress.yaml
    fi
    
    echo "✅ Kubernetes resources deployed"
}

# Check deployment status
check_deployment() {
    echo "🔍 Checking deployment status..."
    
    # Check pod status
    echo "📊 Pod status:"
    kubectl get pods -n merlai -w &
    POD_WATCH_PID=$!
    
    # Wait 30 seconds
    sleep 30
    
    # Stop pod monitoring
    kill $POD_WATCH_PID 2>/dev/null || true
    
    # Detailed status check
    echo ""
    echo "📋 Pod details:"
    kubectl get pods -n merlai -o wide
    
    echo ""
    echo "📋 Service status:"
    kubectl get services -n merlai
    
    echo ""
    echo "📋 Deployment status:"
    kubectl get deployments -n merlai
}

# API testing
test_api() {
    echo "🧪 Running API tests..."
    
    # Start port forwarding
    echo "🔗 Starting port forwarding..."
    kubectl port-forward -n merlai svc/merlai-service 8000:8000 &
    PORT_FORWARD_PID=$!
    
    # Wait for port forwarding to be ready
    sleep 10
    
    # Health check
    echo "🏥 Health check:"
    curl -s http://localhost:8000/health | jq . || echo "Health check failed"
    
    # Readiness check
    echo "✅ Readiness check:"
    curl -s http://localhost:8000/ready | jq . || echo "Readiness check failed"
    
    # Music generation test
    echo "🎵 Music generation test:"
    curl -s -X POST http://localhost:8000/generate \
        -H "Content-Type: application/json" \
        -d '{"melody": [{"note": "C4", "duration": 1.0}, {"note": "E4", "duration": 1.0}], "style": "pop"}' \
        | jq . || echo "Music generation test failed"
    
    # Stop port forwarding
    kill $PORT_FORWARD_PID 2>/dev/null || true
}

# Check logs
check_logs() {
    echo "📝 Checking logs..."
    
    POD_NAME=$(kubectl get pods -n merlai -l app=merlai -o jsonpath='{.items[0].metadata.name}')
    
    if [ -n "$POD_NAME" ]; then
        echo "📋 Pod logs:"
        kubectl logs -n merlai "$POD_NAME" --tail=50
    else
        echo "❌ Pod not found"
    fi
}

# Cleanup
cleanup() {
    echo "🧹 Running cleanup..."
    
    cd "$PROJECT_ROOT/k8s"
    
    # Delete resources
    kubectl delete -f merlai-ingress.yaml --ignore-not-found=true
    kubectl delete -f merlai-deployment.yaml --ignore-not-found=true
    kubectl delete -f configmap.yaml --ignore-not-found=true
    kubectl delete -f namespace.yaml --ignore-not-found=true
    
    echo "✅ Cleanup completed"
}

# Main execution
main() {
    case "${1:-deploy}" in
        "deploy")
            check_requirements
            check_cluster
            build_and_push_image
            deploy_to_k8s
            check_deployment
            ;;
        "test")
            test_api
            ;;
        "logs")
            check_logs
            ;;
        "cleanup")
            cleanup
            ;;
        "full")
            check_requirements
            check_cluster
            build_and_push_image
            deploy_to_k8s
            check_deployment
            sleep 10
            test_api
            ;;
        *)
            echo "Usage: $0 [deploy|test|logs|cleanup|full]"
            echo "  deploy  - Deploy only"
            echo "  test    - API test only"
            echo "  logs    - Log check only"
            echo "  cleanup - Cleanup"
            echo "  full    - Full test (deploy + test)"
            exit 1
            ;;
    esac
}

main "$@" 