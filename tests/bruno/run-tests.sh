#!/bin/bash

# PYHABOT Bruno Test Runner
# This script helps set up and run Bruno API tests for PYHABOT

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
BRUNO_COLLECTION_PATH="$(dirname "$0")"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-.env.docker}"

echo -e "${BLUE}🤖 PYHABOT Bruno Test Runner${NC}"
echo "=================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if API is running
check_api_health() {
    echo -e "${YELLOW}🔍 Checking API health...${NC}"
    if curl -s "$API_BASE_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is running at $API_BASE_URL${NC}"
        return 0
    else
        echo -e "${RED}❌ API is not responding at $API_BASE_URL${NC}"
        return 1
    fi
}

# Function to start PYHABOT API
start_pyhabot() {
    echo -e "${YELLOW}🚀 Starting PYHABOT API...${NC}"
    if [[ -f "$DOCKER_COMPOSE_FILE" ]]; then
        docker compose --env-file "$DOCKER_COMPOSE_FILE" up --build -d pyhabot
        echo -e "${GREEN}✅ PYHABOT started with Docker Compose${NC}"
        sleep 5  # Give it time to start
    else
        echo -e "${RED}❌ Docker compose file not found: $DOCKER_COMPOSE_FILE${NC}"
        echo "Please ensure you're in the PYHABOT project directory"
        exit 1
    fi
}

# Function to check Bruno installation
check_bruno() {
    if command_exists bruno; then
        echo -e "${GREEN}✅ Bruno is installed${NC}"
        return 0
    else
        echo -e "${RED}❌ Bruno is not installed${NC}"
        echo -e "${YELLOW}Please install Bruno from https://www.usebruno.com/downloads${NC}"
        echo ""
        echo "Installation options:"
        echo "  macOS: brew install --cask bruno"
        echo "  Ubuntu: Download .deb from website"
        echo "  Other: Download from https://www.usebruno.com/downloads"
        return 1
    fi
}

# Function to open Bruno collection
open_bruno() {
    echo -e "${YELLOW}📂 Opening Bruno collection...${NC}"
    
    # Try different methods to open Bruno
    if command_exists bruno; then
        # If Bruno CLI is available
        bruno open "$BRUNO_COLLECTION_PATH" 2>/dev/null || {
            echo -e "${YELLOW}Bruno CLI found, but couldn't open collection${NC}"
            echo -e "${YELLOW}Please open Bruno manually and import: $BRUNO_COLLECTION_PATH${NC}"
        }
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - try to open with default application
        open "$BRUNO_COLLECTION_PATH"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - try to open with xdg-open
        xdg-open "$BRUNO_COLLECTION_PATH" 2>/dev/null || {
            echo -e "${YELLOW}Please open Bruno manually and import: $BRUNO_COLLECTION_PATH${NC}"
        }
    else
        echo -e "${YELLOW}Please open Bruno manually and import: $BRUNO_COLLECTION_PATH${NC}"
    fi
}

# Function to show test instructions
show_instructions() {
    echo ""
    echo -e "${BLUE}📋 Test Instructions:${NC}"
    echo "1. Bruno should open with the PYHABOT collection imported"
    echo "2. Configure environment variables if needed:"
    echo "   - baseUrl: $API_BASE_URL"
    echo "   - Update webhook URLs with your actual endpoints"
    echo "3. Run tests individually or as a collection"
    echo "4. Check API documentation at: $API_BASE_URL/docs"
    echo ""
    echo -e "${BLUE}🧪 Test Categories:${NC}"
    echo "  • Health Checks - Basic connectivity"
    echo "  • Watch Management - CRUD operations"
    echo "  • Webhook Management - Configuration"
    echo "  • Webhook Testing - Send test notifications"
    echo "  • Job Management - Background jobs"
    echo "  • Error Handling - Edge cases"
    echo ""
    echo -e "${BLUE}📊 Useful Commands:${NC}"
    echo "  View API logs: docker compose --env-file $DOCKER_COMPOSE_FILE logs pyhabot"
    echo "  Check API health: curl $API_BASE_URL/health"
    echo "  API docs: $API_BASE_URL/docs"
}

# Main execution
main() {
    echo -e "${BLUE}Configuration:${NC}"
    echo "  API Base URL: $API_BASE_URL"
    echo "  Collection Path: $BRUNO_COLLECTION_PATH"
    echo "  Docker Compose: $DOCKER_COMPOSE_FILE"
    echo ""
    
    # Check Bruno installation
    if ! check_bruno; then
        exit 1
    fi
    
    # Check if API is running, start if needed
    if ! check_api_health; then
        echo -e "${YELLOW}🔄 Attempting to start PYHABOT API...${NC}"
        start_pyhabot
        
        # Check again after starting
        if ! check_api_health; then
            echo -e "${RED}❌ Failed to start API. Please check the logs:${NC}"
            echo "docker compose --env-file $DOCKER_COMPOSE_FILE logs pyhabot"
            exit 1
        fi
    fi
    
    # Open Bruno collection
    open_bruno
    
    # Show instructions
    show_instructions
    
    echo -e "${GREEN}🎉 Setup complete! Happy testing!${NC}"
}

# Handle command line arguments
case "${1:-}" in
    "health"|"check")
        check_api_health
        ;;
    "start")
        start_pyhabot
        ;;
    "open")
        open_bruno
        ;;
    "help"|"-h"|"--help")
        echo "PYHABOT Bruno Test Runner"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no args)  Full setup and run"
        echo "  health      Check API health"
        echo "  start       Start PYHABOT API"
        echo "  open        Open Bruno collection"
        echo "  help        Show this help"
        echo ""
        echo "Environment Variables:"
        echo "  API_BASE_URL     API base URL (default: http://localhost:8000)"
        echo "  DOCKER_COMPOSE_FILE  Docker compose env file (default: .env.docker)"
        ;;
    *)
        main
        ;;
esac