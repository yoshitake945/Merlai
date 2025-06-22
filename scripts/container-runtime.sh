#!/bin/bash

# Merlai Container Runtime Abstraction Script
# Supports Docker, containerd, and Podman

set -euo pipefail

# Configuration
RUNTIME=${CONTAINER_RUNTIME:-"docker"}
COMPOSE_FILE=${COMPOSE_FILE:-"docker-compose.yml"}
PROJECT_NAME=${PROJECT_NAME:-"merlai"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if runtime is available
check_runtime() {
    case $RUNTIME in
        "docker")
            if ! command -v docker &> /dev/null; then
                log_error "Docker is not installed or not in PATH"
                exit 1
            fi
            if ! docker info &> /dev/null; then
                log_error "Docker daemon is not running"
                exit 1
            fi
            ;;
        "podman")
            if ! command -v podman &> /dev/null; then
                log_error "Podman is not installed or not in PATH"
                exit 1
            fi
            ;;
        "containerd")
            if ! command -v ctr &> /dev/null; then
                log_error "containerd CLI (ctr) is not installed or not in PATH"
                exit 1
            fi
            ;;
        *)
            log_error "Unsupported runtime: $RUNTIME"
            log_info "Supported runtimes: docker, podman, containerd"
            exit 1
            ;;
    esac
    log_success "Using runtime: $RUNTIME"
}

# Build image
build_image() {
    local dockerfile=$1
    local tag=$2
    local target=${3:-""}
    
    log_info "Building image: $tag"
    
    case $RUNTIME in
        "docker")
            if [ -n "$target" ]; then
                docker build -f "$dockerfile" --target "$target" -t "$tag" .
            else
                docker build -f "$dockerfile" -t "$tag" .
            fi
            ;;
        "podman")
            if [ -n "$target" ]; then
                podman build -f "$dockerfile" --target "$target" -t "$tag" .
            else
                podman build -f "$dockerfile" -t "$tag" .
            fi
            ;;
        "containerd")
            log_warning "containerd build not implemented yet, using docker build"
            if [ -n "$target" ]; then
                docker build -f "$dockerfile" --target "$target" -t "$tag" .
            else
                docker build -f "$dockerfile" -t "$tag" .
            fi
            ;;
    esac
    
    log_success "Image built successfully: $tag"
}

# Run container
run_container() {
    local image=$1
    local name=$2
    shift 2
    local args=("$@")
    
    log_info "Running container: $name"
    
    case $RUNTIME in
        "docker")
            docker run --name "$name" "${args[@]}" "$image"
            ;;
        "podman")
            podman run --name "$name" "${args[@]}" "$image"
            ;;
        "containerd")
            log_warning "containerd run not implemented yet, using docker run"
            docker run --name "$name" "${args[@]}" "$image"
            ;;
    esac
}

# Compose commands
compose_up() {
    log_info "Starting services with $RUNTIME"
    
    case $RUNTIME in
        "docker")
            docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
            ;;
        "podman")
            podman compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
            ;;
        "containerd")
            log_warning "containerd compose not implemented yet, using docker compose"
            docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
            ;;
    esac
    
    log_success "Services started successfully"
}

compose_down() {
    log_info "Stopping services"
    
    case $RUNTIME in
        "docker")
            docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
            ;;
        "podman")
            podman compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
            ;;
        "containerd")
            log_warning "containerd compose not implemented yet, using docker compose"
            docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
            ;;
    esac
    
    log_success "Services stopped successfully"
}

compose_logs() {
    local service=${1:-""}
    
    case $RUNTIME in
        "docker")
            if [ -n "$service" ]; then
                docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f "$service"
            else
                docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
            fi
            ;;
        "podman")
            if [ -n "$service" ]; then
                podman compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f "$service"
            else
                podman compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
            fi
            ;;
        "containerd")
            log_warning "containerd compose not implemented yet, using docker compose"
            if [ -n "$service" ]; then
                docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f "$service"
            else
                docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
            fi
            ;;
    esac
}

# Health check
health_check() {
    log_info "Performing health check"
    
    # Check if API is responding
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Health check passed"
            return 0
        fi
        
        log_info "Health check attempt $attempt/$max_attempts failed, retrying in 2 seconds..."
        sleep 2
        ((attempt++))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Main function
main() {
    local command=${1:-"help"}
    
    case $command in
        "build")
            check_runtime
            build_image "docker/Dockerfile.cpu" "merlai:latest" "development"
            ;;
        "up")
            check_runtime
            compose_up
            health_check
            ;;
        "down")
            check_runtime
            compose_down
            ;;
        "logs")
            check_runtime
            compose_logs "${2:-}"
            ;;
        "restart")
            check_runtime
            compose_down
            sleep 2
            compose_up
            health_check
            ;;
        "clean")
            log_info "Cleaning up containers and images"
            case $RUNTIME in
                "docker")
                    docker system prune -f
                    ;;
                "podman")
                    podman system prune -f
                    ;;
                "containerd")
                    log_warning "containerd cleanup not implemented yet"
                    ;;
            esac
            log_success "Cleanup completed"
            ;;
        "help"|*)
            echo "Merlai Container Runtime Management"
            echo ""
            echo "Usage: $0 [COMMAND] [OPTIONS]"
            echo ""
            echo "Commands:"
            echo "  build     Build the Merlai image"
            echo "  up        Start all services"
            echo "  down      Stop all services"
            echo "  logs      Show service logs"
            echo "  restart   Restart all services"
            echo "  clean     Clean up containers and images"
            echo "  help      Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  CONTAINER_RUNTIME  Runtime to use (docker, podman, containerd)"
            echo "  COMPOSE_FILE       Compose file to use"
            echo "  PROJECT_NAME       Project name for compose"
            echo ""
            echo "Examples:"
            echo "  CONTAINER_RUNTIME=podman $0 up"
            echo "  $0 logs merlai-api"
            ;;
    esac
}

# Run main function with all arguments
main "$@" 