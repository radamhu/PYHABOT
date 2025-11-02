#!/bin/bash

# PYHABOT API Test Script (curl-based)
# Simple API testing without requiring Bruno

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
API_VERSION="${API_VERSION:-api/v1}"
WATCH_ID="${WATCH_ID:-1}"

# Helper functions
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Test functions
test_health() {
    print_header "Health Checks"
    
    echo "Testing /health..."
    if response=$(curl -s -w "%{http_code}" "$BASE_URL/health"); then
        http_code="${response: -3}"
        body="${response%???}"
        if [[ "$http_code" == "200" ]]; then
            print_success "Health check passed"
            echo "Response: $body"
        else
            print_error "Health check failed (HTTP $http_code)"
        fi
    else
        print_error "Could not connect to API"
    fi
    
    echo "Testing /ping..."
    if response=$(curl -s -w "%{http_code}" "$BASE_URL/ping"); then
        http_code="${response: -3}"
        body="${response%???}"
        if [[ "$http_code" == "200" ]]; then
            print_success "Ping check passed"
            echo "Response: $body"
        else
            print_error "Ping check failed (HTTP $http_code)"
        fi
    fi
}

test_watch_crud() {
    print_header "Watch Management CRUD"
    
    # Create watch
    echo "Creating watch..."
    create_response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{
            "url": "https://hardverapro.hu/vegyseg/monitorok",
            "webhook_url": "https://discord.com/api/webhooks/123/test"
        }' \
        "$BASE_URL/$API_VERSION/watches")
    
    create_http_code="${create_response: -3}"
    create_body="${create_response%???}"
    
    if [[ "$create_http_code" == "201" ]]; then
        print_success "Watch created successfully"
        echo "Response: $create_body"
        
        # Extract watch ID from response (simple approach)
        WATCH_ID=$(echo "$create_body" | grep -o '"id":[0-9]*' | cut -d':' -f2)
        print_info "Using watch ID: $WATCH_ID"
        
        # Get watch
        echo "Getting watch $WATCH_ID..."
        get_response=$(curl -s -w "%{http_code}" "$BASE_URL/$API_VERSION/watches/$WATCH_ID")
        get_http_code="${get_response: -3}"
        get_body="${get_response%???}"
        
        if [[ "$get_http_code" == "200" ]]; then
            print_success "Watch retrieved successfully"
        else
            print_error "Failed to get watch (HTTP $get_http_code)"
        fi
        
        # List watches
        echo "Listing all watches..."
        list_response=$(curl -s -w "%{http_code}" "$BASE_URL/$API_VERSION/watches")
        list_http_code="${list_response: -3}"
        
        if [[ "$list_http_code" == "200" ]]; then
            print_success "Watches listed successfully"
        else
            print_error "Failed to list watches (HTTP $list_http_code)"
        fi
        
        # Delete watch
        echo "Deleting watch $WATCH_ID..."
        delete_response=$(curl -s -w "%{http_code}" -X DELETE "$BASE_URL/$API_VERSION/watches/$WATCH_ID")
        delete_http_code="${delete_response: -3}"
        
        if [[ "$delete_http_code" == "200" || "$delete_http_code" == "204" ]]; then
            print_success "Watch deleted successfully"
        else
            print_error "Failed to delete watch (HTTP $delete_http_code)"
        fi
        
    else
        print_error "Failed to create watch (HTTP $create_http_code)"
        echo "Response: $create_body"
    fi
}

test_webhook_testing() {
    print_header "Webhook Testing"
    
    echo "Testing webhook endpoint..."
    webhook_response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{
            "webhook_url": "https://httpbin.org/post",
            "webhook_type": "generic",
            "test_message": "Test from PYHABOT curl script"
        }' \
        "$BASE_URL/$API_VERSION/webhooks/test")
    
    webhook_http_code="${webhook_response: -3}"
    webhook_body="${webhook_response%???}"
    
    if [[ "$webhook_http_code" == "200" ]]; then
        print_success "Webhook test completed"
        echo "Response: $webhook_body"
    else
        print_error "Webhook test failed (HTTP $webhook_http_code)"
        echo "Response: $webhook_body"
    fi
    
    echo "Getting webhook types..."
    types_response=$(curl -s -w "%{http_code}" "$BASE_URL/$API_VERSION/webhooks/types")
    types_http_code="${types_response: -3}"
    
    if [[ "$types_http_code" == "200" ]]; then
        print_success "Webhook types retrieved"
    else
        print_error "Failed to get webhook types (HTTP $types_http_code)"
    fi
}

test_job_management() {
    print_header "Job Management"
    
    echo "Listing jobs..."
    jobs_response=$(curl -s -w "%{http_code}" "$BASE_URL/$API_VERSION/jobs")
    jobs_http_code="${jobs_response: -3}"
    
    if [[ "$jobs_http_code" == "200" ]]; then
        print_success "Jobs listed successfully"
    else
        print_error "Failed to list jobs (HTTP $jobs_http_code)"
    fi
    
    # Note: We can't test rescrape without a valid watch ID
    print_info "Skipping rescrape test (requires valid watch ID)"
}

test_error_handling() {
    print_header "Error Handling"
    
    echo "Testing invalid watch ID..."
    invalid_response=$(curl -s -w "%{http_code}" "$BASE_URL/$API_VERSION/watches/99999")
    invalid_http_code="${invalid_response: -3}"
    
    if [[ "$invalid_http_code" == "404" ]]; then
        print_success "Invalid watch ID correctly returns 404"
    else
        print_error "Expected 404 for invalid watch ID, got $invalid_http_code"
    fi
    
    echo "Testing invalid JSON..."
    invalid_json_response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{ invalid json }' \
        "$BASE_URL/$API_VERSION/watches")
    invalid_json_http_code="${invalid_json_response: -3}"
    
    if [[ "$invalid_json_http_code" == "422" ]]; then
        print_success "Invalid JSON correctly returns 422"
    else
        print_error "Expected 422 for invalid JSON, got $invalid_json_http_code"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🤖 PYHABOT API Test Script (curl-based)${NC}"
    echo "======================================"
    echo "Base URL: $BASE_URL"
    echo "API Version: $API_VERSION"
    echo ""
    
    # Check if API is running
    print_info "Checking API connectivity..."
    if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
        print_error "API is not responding at $BASE_URL"
        echo "Please ensure PYHABOT is running:"
        echo "  docker compose --env-file .env.docker up --build -d pyhabot"
        exit 1
    fi
    
    print_success "API is responding"
    
    # Run tests
    test_health
    test_watch_crud
    test_webhook_testing
    test_job_management
    test_error_handling
    
    print_header "Test Summary"
    print_success "All tests completed!"
    echo ""
    echo -e "${BLUE}📚 Additional Resources:${NC}"
    echo "  API Documentation: $BASE_URL/docs"
    echo "  API Version: $BASE_URL/version"
    echo "  Health Check: $BASE_URL/health"
    echo ""
    echo -e "${BLUE}🧪 For more comprehensive testing, use Bruno:${NC}"
    echo "  ./bruno/run-tests.sh"
}

# Handle command line arguments
case "${1:-}" in
    "health")
        test_health
        ;;
    "watches")
        test_watch_crud
        ;;
    "webhooks")
        test_webhook_testing
        ;;
    "jobs")
        test_job_management
        ;;
    "errors")
        test_error_handling
        ;;
    "help"|"-h"|"--help")
        echo "PYHABOT API Test Script"
        echo ""
        echo "Usage: $0 [test_category]"
        echo ""
        echo "Test Categories:"
        echo "  (no args)  Run all tests"
        echo "  health      Health checks only"
        echo "  watches     Watch CRUD tests"
        echo "  webhooks    Webhook testing"
        echo "  jobs        Job management"
        echo "  errors      Error handling"
        echo "  help        Show this help"
        echo ""
        echo "Environment Variables:"
        echo "  BASE_URL     API base URL (default: http://localhost:8000)"
        echo "  API_VERSION  API version (default: api/v1)"
        ;;
    *)
        main
        ;;
esac