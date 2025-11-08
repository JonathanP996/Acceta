#!/bin/bash
# Test all Accenta API endpoints

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Testing Accenta API Endpoints"
echo "=========================================="
echo ""

# Test 1: Root endpoint
echo "1. Testing GET /"
echo "   Command: curl $BASE_URL/"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" $BASE_URL/)
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
body=$(echo "$response" | grep -v "HTTP_CODE")
echo "   Response: $body"
echo "   Status: $http_code"
echo ""

# Test 2: Health endpoint
echo "2. Testing GET /health"
echo "   Command: curl $BASE_URL/health"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" $BASE_URL/health)
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
body=$(echo "$response" | grep -v "HTTP_CODE")
echo "   Response: $body"
echo "   Status: $http_code"
echo ""

# Test 3: API docs
echo "3. Testing GET /docs"
echo "   Command: curl -I $BASE_URL/docs"
curl -s -I $BASE_URL/docs | head -5
echo ""

# Test 4: Analyze accent endpoint (without file - should fail gracefully)
echo "4. Testing POST /api/analyze_accent (without file)"
echo "   Command: curl -X POST $BASE_URL/api/analyze_accent"
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST $BASE_URL/api/analyze_accent)
http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
body=$(echo "$response" | grep -v "HTTP_CODE" | head -5)
echo "   Response: $body"
echo "   Status: $http_code"
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="

