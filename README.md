Water Kiosk Hardware Function - Setup & Testing Guide
This guide provides step-by-step instructions to clone, deploy, and test the Water Kiosk Hardware Function using Appwrite Functions.
Table of Contents
    1. Prerequisites 
    2. System Overview 
    3. Clone and Setup 
    4. Function Deployment 
    5. Local Testing (On Server) 
    6. Remote Testing (Internet) 
    7. Kiosk Integration Examples 
    8. Customer Management 
    9. Troubleshooting 
Prerequisites
Server Requirements
    • Ubuntu/Linux server with Docker installed 
    • Appwrite 1.4.14+ running via Docker Compose 
    • Internet connection and external IP address (47.208.219.96) 
    • Firewall configured for HTTP/HTTPS access 
Database Requirements
Your Appwrite database should have a customers collection with these attributes:
# Required attributes for customers collection:
- phone_number (string, required, 20 chars)
- created_at (string, required, 50 chars)
- registration_state (string, required, 50 chars)
- is_registered (boolean, required)
- credits (integer, required)
- full_name (string, optional, 100 chars)
- location (string, optional, 100 chars)
- account_id (string, optional, 20 chars)
- active (boolean, optional)
- pin (string, optional, 4 chars)
Tools Required
    • git (for cloning repository) 
    • curl (for testing) 
    • jq (optional, for JSON formatting: brew install jq) 
    • Appwrite CLI 
System Overview
Kiosk Hardware → Internet → Server (47.208.219.96) → Appwrite Function → Database
                                     ↓
Kiosk Hardware ← Response ← Server ← Customer Verification ← Database Query
Main Function Features:
    • Dispense Verification: Verify customer credentials for water dispensing 
    • Database Operations: Query, create, and update customer records 
    • Unified Schema: Shares customer database with SMS registration system 
    • Fallback Logic: 90% approval rate if database is unavailable 
Clone and Setup
1. Clone the Repository
# Clone the repository
git clone https://github.com/JerroldMitchell/water-kiosk-hardware-function.git
cd water-kiosk-hardware-function
2. Review Configuration
The function uses environment variables with fallbacks in src/main.py:
# Update these values with your actual configuration
APPWRITE_PROJECT_ID = os.environ.get('APPWRITE_PROJECT_ID', 'YOUR_PROJECT_ID')
APPWRITE_DATABASE_ID = os.environ.get('APPWRITE_DATABASE_ID', 'YOUR_DATABASE_ID')
APPWRITE_API_KEY = os.environ.get('APPWRITE_API_KEY', 'YOUR_API_KEY')
CUSTOMERS_COLLECTION_ID = os.environ.get('CUSTOMERS_COLLECTION_ID', 'customers')
APPWRITE_ENDPOINT = os.environ.get('APPWRITE_ENDPOINT', 'http://appwrite/v1')
Important: Update the fallback values with your actual Appwrite configuration.
Function Deployment
1. Create Function
# Create the function in Appwrite
appwrite functions create \
  --function-id water-kiosk-hardware \
  --name "Water Kiosk Hardware" \
  --runtime python-3.9 \
  --execute any \
  --timeout 15
2. Deploy Function
# Deploy the function code
appwrite functions create-deployment \
  --function-id water-kiosk-hardware \
  --entrypoint src/main.py \
  --code . \
  --activate true
3. Verify Deployment
# Check function status
appwrite functions get --function-id water-kiosk-hardware
Local Testing (On Server)
1. Basic Function Tests
# Test function status (GET request)
appwrite functions create-execution \
  --function-id water-kiosk-hardware \
  --method GET

# Expected response: Function status page with endpoints
2. Database Connection Test
# Test database connectivity
appwrite functions create-execution \
  --function-id water-kiosk-hardware \
  --method POST \
  --body '{"action": "test_database"}'

# Expected response: {"status": "DATABASE_SUCCESS", "collections_found": 1}
3. Customer Lookup Test
# Test customer verification (replace with actual customer phone/PIN)
appwrite functions create-execution \
  --function-id water-kiosk-hardware \
  --method POST \
  --body '{"action": "dispense_verification", "kiosk_id": "KIOSK001", "user_id": "+254700000102", "pin": "1234", "volume_ml": 500}'

# Expected response: Dispense approval/denial with customer data
4. Database Operations
# Query customers
appwrite functions create-execution \
  --function-id water-kiosk-hardware \
  --method POST \
  --body '{"action": "database_query", "collection": "customers", "queries": ["limit(5)"]}'

# Update customer (make active for testing)
appwrite functions create-execution \
  --function-id water-kiosk-hardware \
  --method POST \
  --body '{"action": "database_update", "collection": "customers", "document_id": "CUSTOMER_ID", "document_data": {"active": true, "pin": "1234"}}'
Remote Testing (Internet)
1. Basic Connectivity
From a remote computer:
# Test server connectivity
ping 47.208.219.96

# Test Appwrite health
curl http://47.208.219.96/v1/health/version
# Expected: {"version":"1.4.14"}
2. Function Status Test
# Test function status page
curl -X POST http://47.208.219.96/v1/functions/water-kiosk-hardware/executions \
  -H "Content-Type: application/json" \
  -H "X-Appwrite-Project: YOUR_PROJECT_ID" \
  -d '{"method": "GET"}' | jq '.'
3. Database Connection Test
# Test database connection remotely
curl -X POST http://47.208.219.96/v1/functions/water-kiosk-hardware/executions \
  -H "Content-Type: application/json" \
  -H "X-Appwrite-Project: YOUR_PROJECT_ID" \
  -d '{"body": "{\"action\": \"test_database\"}", "method": "POST"}' | jq '.'
4. Dispense Verification Test
# Test customer verification
curl -X POST http://47.208.219.96/v1/functions/water-kiosk-hardware/executions \
  -H "Content-Type: application/json" \
  -H "X-Appwrite-Project: YOUR_PROJECT_ID" \
  -d '{"body": "{\"action\": \"dispense_verification\", \"kiosk_id\": \"KIOSK001\", \"user_id\": \"+254700000102\", \"pin\": \"1234\", \"volume_ml\": 500}", "method": "POST"}' | jq '.'
Kiosk Integration Examples
1. Standard Kiosk Verification Request
{
  "body": "{
    \"action\": \"dispense_verification\",
    \"kiosk_id\": \"KIOSK001\",
    \"user_id\": \"+254700000102\",
    \"pin\": \"1234\",
    \"volume_ml\": 500,
    \"timestamp\": \"2025-08-10T22:32:38Z\",
    \"request_id\": \"req_12345\"
  }",
  "method": "POST"
}
2. Expected Approval Response
{
  "type": "dispense_response",
  "request_id": "req_12345",
  "user_id": "+254700000102",
  "pin": "1234",
  "volume_ml": 500,
  "approved": true,
  "reason": "Customer verified in database",
  "timestamp": "2025-08-10T22:32:38.230006",
  "kiosk_id": "KIOSK001",
  "user_data": {
    "phone_number": "+254700000102",
    "account_id": "TSFD536DB",
    "full_name": "Jane Smith",
    "active": true,
    "credits": 0
  }
}
3. Expected Denial Response
{
  "type": "dispense_response",
  "request_id": "req_12345",
  "user_id": "+254700000102",
  "pin": "1234",
  "volume_ml": 500,
  "approved": false,
  "reason": "Subscription inactive",
  "timestamp": "2025-08-10T22:32:38.230006",
  "kiosk_id": "KIOSK001"
}
4. Kiosk Implementation Example
import requests
import json

def verify_customer(kiosk_id, phone_number, pin, volume_ml):
    """Verify customer for water dispensing"""
    url = "http://47.208.219.96/v1/functions/water-kiosk-hardware/executions"
    
    headers = {
        'Content-Type': 'application/json',
        'X-Appwrite-Project': 'YOUR_PROJECT_ID'
    }
    
    payload = {
        "body": json.dumps({
            "action": "dispense_verification",
            "kiosk_id": kiosk_id,
            "user_id": phone_number,
            "pin": pin,
            "volume_ml": volume_ml,
            "timestamp": datetime.now().isoformat(),
            "request_id": f"req_{int(time.time())}"
        }),
        "method": "POST"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        
        # Parse the response body (it's JSON string in responseBody)
        response_data = json.loads(result['responseBody'])
        
        return {
            'approved': response_data.get('approved', False),
            'reason': response_data.get('reason', 'Unknown'),
            'user_data': response_data.get('user_data', {}),
            'customer_name': response_data.get('user_data', {}).get('full_name', 'Unknown')
        }
        
    except Exception as e:
        print(f"Verification failed: {e}")
        return {'approved': False, 'reason': 'Connection error'}

# Usage example
result = verify_customer("KIOSK001", "+254700000102", "1234", 500)
if result['approved']:
    print(f"✅ Approved for {result['customer_name']}")
    # Dispense water
else:
    print(f"❌ Denied: {result['reason']}")
Customer Management
1. Check Customer Status
# Query specific customer
curl -X POST http://47.208.219.96/v1/functions/water-kiosk-hardware/executions \
  -H "Content-Type: application/json" \
  -H "X-Appwrite-Project: YOUR_PROJECT_ID" \
  -d '{"body": "{\"action\": \"database_query\", \"collection\": \"customers\", \"queries\": [\"equal(\\\"phone_number\\\", \\\"+254700000102\\\")\"]}",  "method": "POST"}'
2. Activate Customer Subscription
# Make customer active with PIN
curl -X POST http://47.208.219.96/v1/functions/water-kiosk-hardware/executions \
  -H "Content-Type: application/json" \
  -H "X-Appwrite-Project: YOUR_PROJECT_ID" \
  -d '{"body": "{\"action\": \"database_update\", \"collection\": \"customers\", \"document_id\": \"CUSTOMER_DOC_ID\", \"document_data\": {\"active\": true, \"pin\": \"1234\"}}",  "method": "POST"}'
3. Add Customer Credits
# Update customer credits
curl -X POST http://47.208.219.96/v1/functions/water-kiosk-hardware/executions \
  -H "Content-Type: application/json" \
  -H "X-Appwrite-Project: YOUR_PROJECT_ID" \
  -d '{"body": "{\"action\": \"database_update\", \"collection\": \"customers\", \"document_id\": \"CUSTOMER_DOC_ID\", \"document_data\": {\"credits\": 1000}}",  "method": "POST"}'
Troubleshooting
Common Issues
1. Function Returns "Invalid action"
Problem: Wrong action parameter or missing action.
Solution: Ensure action is one of:
    • dispense_verification 
    • database_query 
    • database_create 
    • database_update 
    • test_database 
2. "Customer not found in database"
Problem: Phone number format mismatch or customer doesn't exist.
Solution: The function tries multiple formats:
    • +254700000102 
    • 0700000102 
    • 254700000102 
    • 700000102 
3. "Subscription inactive"
Problem: Customer exists but active field is false or null.
Solution: Update customer record:
{"action": "database_update", "collection": "customers", "document_id": "ID", "document_data": {"active": true}}
4. Remote Connection Timeout
Problem: Can't reach server from internet.
Solutions:
    • Check firewall: sudo ufw status 
    • Verify port forwarding on router 
    • Test with: ping 47.208.219.96 
5. Database Connection Errors
Problem: Function can't connect to Appwrite database.
Solutions:
    • Check Appwrite is running: docker ps | grep appwrite 
    • Verify project ID and API key in function code 
    • Test locally: curl http://localhost/v1/health/version 
Debugging Commands
# Check function logs
appwrite functions list-executions --function-id water-kiosk-hardware --limit 5

# Check specific execution
appwrite functions get-execution --function-id water-kiosk-hardware --execution-id EXECUTION_ID

# Test database directly
curl http://47.208.219.96/v1/databases/YOUR_DATABASE_ID/collections \
  -H "X-Appwrite-Project: YOUR_PROJECT_ID" \
  -H "X-Appwrite-Key: YOUR_API_KEY"
Success Indicators
✅ Function Working:
    • GET request returns status page 
    • Database test returns "collections_found": 1 
    • Dispense verification returns proper approval/denial 
✅ Remote Access Working:
    • Can ping 47.208.219.96 
    • Health endpoint returns version info 
    • Function executions work from internet 
✅ Customer Integration Working:
    • Customers registered via SMS are found by hardware function 
    • PIN verification works correctly 
    • Active customers get approved for dispensing 
Configuration Summary
Replace these values with your actual configuration:
# Function Configuration
SERVER_IP="47.208.219.96"
PROJECT_ID="689107c288885e90c039"
DATABASE_ID="6864aed388d20c69a461"
API_KEY="your_actual_api_key_here"
FUNCTION_ID="water-kiosk-hardware"

# Function URL for kiosks
FUNCTION_URL="http://47.208.219.96/v1/functions/water-kiosk-hardware/executions"

# Required Headers
HEADERS="Content-Type: application/json, X-Appwrite-Project: PROJECT_ID"


