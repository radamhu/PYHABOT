#!/bin/bash

# PYHABOT Docker Webhook Test Script
# This script tests Discord webhook functionality in Docker environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.test.yml"
CONTAINER_NAME="pyhabot-webhook-test"
WEBHOOK_SERVER_CONTAINER="webhook-test-server"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running or not accessible"
        exit 1
    fi
}

# Function to build and start test environment
setup_test_environment() {
    print_status "Setting up PYHABOT webhook test environment..."
    
    # Build the image
    print_status "Building PYHABOT Docker image..."
    docker compose -f $COMPOSE_FILE build
    
    # Start the main test container
    print_status "Starting PYHABOT test container..."
    docker compose -f $COMPOSE_FILE up -d pyhabot-webhook-test
    
    # Wait for container to be ready
    print_status "Waiting for container to be ready..."
    sleep 5
    
    # Check if container is running
    if docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}" | grep -q $CONTAINER_NAME; then
        print_success "Test container is running"
    else
        print_error "Failed to start test container"
        exit 1
    fi
}

# Function to start optional webhook test server
setup_webhook_server() {
    print_status "Starting webhook test server..."
    docker compose -f $COMPOSE_FILE --profile test-server up -d webhook-test-server
    
    # Wait for server to be ready
    sleep 3
    
    # Check if server is responding
    if curl -s http://localhost:8080/health > /dev/null; then
        print_success "Webhook test server is running on http://localhost:8080"
    else
        print_warning "Webhook test server may not be ready yet"
    fi
}

# Function to test webhook with local test server
test_local_webhook() {
    print_status "Testing webhook against local test server..."
    
    # Test basic connectivity
    print_status "Testing basic connectivity to local server..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ | grep -q "204"; then
        print_success "Local webhook server is responding"
    else
        print_error "Local webhook server is not responding properly"
        return 1
    fi
    
    # Test webhook through PYHABOT
    print_status "Testing webhook through PYHABOT container..."
    docker exec -it $CONTAINER_NAME python test_webhook.py \
        "http://webhook-test-server/" \
        --test-type basic \
        --connectivity
}

# Function to test Discord webhook
test_discord_webhook() {
    local webhook_url="$1"
    
    if [ -z "$webhook_url" ]; then
        print_warning "No Discord webhook URL provided. Skipping Discord tests."
        print_status "To test Discord webhook, run:"
        print_status "  $0 --discord YOUR_WEBHOOK_URL"
        return 0
    fi
    
    print_status "Testing Discord webhook..."
    
    # Test basic connectivity first
    print_status "Testing Discord webhook connectivity..."
    docker exec -it $CONTAINER_NAME python test_webhook.py \
        "$webhook_url" \
        --connectivity
    
    if [ $? -eq 0 ]; then
        print_success "Discord webhook connectivity test passed"
        
        # Test all message types
        print_status "Testing all Discord webhook message types..."
        docker exec -it $CONTAINER_NAME python test_webhook.py \
            "$webhook_url" \
            --test-type all
    else
        print_error "Discord webhook connectivity test failed"
        return 1
    fi
}

# Function to test CLI webhook command
test_cli_webhook_command() {
    local webhook_url="$1"
    
    if [ -z "$webhook_url" ]; then
        print_warning "No webhook URL provided. Using local test server..."
        webhook_url="http://webhook-test-server/"
    fi
    
    print_status "Testing CLI webhook command..."
    
    # Test the CLI command
    docker exec -it $CONTAINER_NAME python -m pyhabot.simple_cli test-webhook \
        "$webhook_url" \
        --test-type basic
}

# Function to cleanup test environment
cleanup() {
    print_status "Cleaning up test environment..."
    docker compose -f $COMPOSE_FILE down -v
    docker compose -f $COMPOSE_FILE --profile test-server down -v
    print_success "Cleanup completed"
}

# Function to show logs
show_logs() {
    print_status "Showing container logs..."
    docker logs -f $CONTAINER_NAME
}

# Function to show help
show_help() {
    echo "PYHABOT Docker Webhook Test Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --setup                    Setup test environment"
    echo "  --test-local               Test against local webhook server"
    echo "  --test-discord URL         Test against Discord webhook URL"
    echo "  --test-cli [URL]           Test CLI webhook command"
    echo "  --logs                     Show container logs"
    echo "  --cleanup                  Cleanup test environment"
    echo "  --help                     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --setup"
    echo "  $0 --test-local"
    echo "  $0 --test-discord https://discord.com/api/webhooks/..."
    echo "  $0 --test-cli"
    echo "  $0 --cleanup"
}

# Main script logic
main() {
    case "${1:-}" in
        --setup)
            check_docker
            setup_test_environment
            ;;
        --test-local)
            check_docker
            setup_webhook_server
            test_local_webhook
            ;;
        --test-discord)
            check_docker
            setup_test_environment
            test_discord_webhook "$2"
            ;;
        --test-cli)
            check_docker
            setup_test_environment
            test_cli_webhook_command "$2"
            ;;
        --logs)
            show_logs
            ;;
        --cleanup)
            cleanup
            ;;
        --help|"")
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"