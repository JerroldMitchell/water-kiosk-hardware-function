import json
import os
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error
import random

# Configuration Constants - Environment Variables with Fallbacks (UNIFIED SCHEMA)
APPWRITE_PROJECT_ID = os.environ.get('APPWRITE_PROJECT_ID', '689107c288885e90c039')
APPWRITE_DATABASE_ID = os.environ.get('APPWRITE_DATABASE_ID', '6864aed388d20c69a461')
APPWRITE_API_KEY = os.environ.get('APPWRITE_API_KEY', '0f3a08c2c4fc98480980cbe59cd2db6b8522734081f42db3480ab2e7a8ffd7c46e8476a62257e429ff11c1d6616e814ae8753fb07e7058d1b669c641012941092ddcd585df802eb2313bfba49bf3ec3f776f529c09a7f5efef2988e4b4821244bbd25b3cd16669885c173ac023b5b8a90e4801f3584eef607506362c6ae01c94')
CUSTOMERS_COLLECTION_ID = os.environ.get('CUSTOMERS_COLLECTION_ID', 'customers')
APPWRITE_ENDPOINT = os.environ.get('APPWRITE_ENDPOINT', 'http://appwrite/v1')

def main(context):
    """
    Water Kiosk Hardware Server - Appwrite Function Version
    Converted from Flask to Appwrite Function for better scalability
    Handles kiosk hardware requests for user verification and database operations
    """
    try:
        # Handle payload parsing - same as SMS function
        raw_body = context.req.body or {}
        method = context.req.method
        
        # Parse body if it's a JSON string
        if isinstance(raw_body, str):
            try:
                body = json.loads(raw_body)
            except json.JSONDecodeError:
                body = {}
        else:
            body = raw_body
        
        # Debug logging
        context.log(f"Method: {method}")
        context.log(f"Raw body: {raw_body}")
        context.log(f"Body type: {type(raw_body)}")
        context.log(f"Parsed body: {body}")
        
        if method == 'GET':
            return context.res.json({
                'status': 'Water Kiosk Hardware Server Active',
                'message': 'Appwrite Function for kiosk hardware integration',
                'version': '2.0',
                'timestamp': datetime.now().isoformat(),
                'features': ['dispense_verification', 'database_query', 'database_create', 'database_update'],
                'endpoints': {
                    'status': 'GET / - This status page',
                    'dispense_verification': 'POST {"action": "dispense_verification", "kiosk_id": "...", "user_id": "...", "pin": "..."}',
                    'database_query': 'POST {"action": "database_query", "collection": "...", "queries": [...]}',
                    'database_create': 'POST {"action": "database_create", "collection": "...", "document_data": {...}}',
                    'database_update': 'POST {"action": "database_update", "collection": "...", "document_id": "...", "document_data": {...}}',
                    'test_database': 'POST {"action": "test_database"}'
                }
            })
        
        elif method == 'POST':
            action = body.get('action')
            
            if action == 'dispense_verification':
                return context.res.json(handle_dispense_verification(context, body))
            
            elif action == 'database_query':
                return context.res.json(handle_database_query(context, body))
            
            elif action == 'database_create':
                return context.res.json(handle_database_create(context, body))
            
            elif action == 'database_update':
                return context.res.json(handle_database_update(context, body))
            
            elif action == 'test_database':
                return context.res.json(test_database_connection(context))
            
            else:
                return context.res.json({
                    'error': 'Invalid action',
                    'received': body,
                    'available_actions': ['dispense_verification', 'database_query', 'database_create', 'database_update', 'test_database']
                }, 400)
        
        else:
            return context.res.json({'error': f'Method {method} not allowed'}, 405)
        
    except Exception as e:
        context.error(f'Function error: {str(e)}')
        return context.res.json({
            'error': str(e),
            'type': 'server_error',
            'timestamp': datetime.now().isoformat()
        }, 500)


def handle_dispense_verification(context, data):
    """Main endpoint for kiosk hardware - verify user credentials for water dispensing"""
    try:
        context.log(f"🔍 Processing dispense verification: {data}")
        
        # Extract required fields (user_id is phone_number)
        kiosk_id = data.get('kiosk_id')
        phone_number = data.get('user_id')  # Kiosk sends user_id, but it's phone_number
        pin = data.get('pin')
        volume_ml = data.get('volume_ml')
        timestamp = data.get('timestamp')
        request_id = data.get('request_id')
        
        if not all([kiosk_id, phone_number, pin]):
            return {
                'type': 'dispense_response',
                'request_id': request_id,
                'error': 'Missing required fields: kiosk_id, user_id (phone_number), pin',
                'approved': False,
                'reason': 'Invalid request format',
                'timestamp': datetime.now().isoformat()
            }
        
        approved = False
        reason = ''
        user_data = None
        
        try:
            # Verify user in the database (UNIFIED SCHEMA)
            context.log('📡 Checking user credentials in database...')
            user_lookup = lookup_customer_by_phone(context, phone_number, pin)
            
            if user_lookup['found']:
                if not user_lookup['is_registered']:
                    approved = False
                    reason = 'Customer not fully registered'
                    context.log(f"❌ Customer {phone_number} not fully registered")
                elif not user_lookup['active']:
                    approved = False
                    reason = 'Subscription inactive'
                    context.log(f"❌ Customer {phone_number} subscription inactive")
                elif not user_lookup['valid_pin']:
                    approved = False
                    reason = 'Invalid PIN'
                    context.log(f"❌ Invalid PIN for customer {phone_number}")
                else:
                    approved = True
                    reason = 'Customer verified in database'
                    user_data = user_lookup['customer_data']
                    context.log(f"✅ Customer {phone_number} verified successfully")
            else:
                approved = False
                reason = 'Customer not found in database'
                context.log(f"❌ Customer {phone_number} not found in database")
                
        except Exception as error:
            context.error(f"❌ Database lookup failed: {str(error)}")
            context.log('🔄 Falling back to random approval logic...')
            
            # Fall back to 90% approval rate if database is unavailable
            approved = random.random() < 0.9
            reason = ('Database unavailable - approved by fallback (90% chance)' if approved 
                     else 'Database unavailable - denied by fallback (10% chance)')
        
        # Prepare response (same format as Flask version)
        response = {
            'type': 'dispense_response',
            'request_id': request_id,
            'user_id': phone_number,  # Kiosk expects user_id field
            'pin': pin,
            'volume_ml': volume_ml,
            'approved': approved,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'kiosk_id': kiosk_id
        }
        
        # Add user data if available
        if user_data:
            response['user_data'] = user_data
        
        context.log(f"📤 Sent response: {'✅ APPROVED' if approved else '❌ DENIED'} - {reason}")
        
        return response
        
    except Exception as e:
        context.error(f'Dispense verification error: {str(e)}')
        return {
            'error': str(e),
            'type': 'server_error',
            'approved': False,
            'reason': 'Server error occurred',
            'timestamp': datetime.now().isoformat()
        }


def handle_database_query(context, data):
    """Handle database query requests"""
    try:
        context.log(f'🔍 Processing database query: {data}')
        
        database = data.get('database', APPWRITE_DATABASE_ID)
        collection = data.get('collection')
        queries = data.get('queries', [])
        request_id = data.get('request_id')
        
        if not collection:
            return {
                'type': 'query_response',
                'request_id': request_id,
                'success': False,
                'error': 'Collection ID is required',
                'timestamp': datetime.now().isoformat()
            }
        
        # Build query path
        path = f'/databases/{database}/collections/{collection}/documents'
        if queries:
            query_params = '&'.join([f'queries[]={urllib.parse.quote(q)}' for q in queries])
            path += f'?{query_params}'
        
        result = make_appwrite_request(context, 'GET', path)
        
        response = {
            'type': 'query_response',
            'request_id': request_id,
            'success': True,
            'data': result['data'],
            'total': result['data'].get('total', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        context.log(f"✅ Database query successful: {result['data'].get('total', 0)} documents")
        return response
        
    except Exception as error:
        context.error(f"❌ Database query failed: {str(error)}")
        return {
            'type': 'query_response',
            'request_id': data.get('request_id'),
            'success': False,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        }


def handle_database_create(context, data):
    """Handle database document creation"""
    try:
        context.log(f'🔍 Processing database create: {data}')
        
        database = data.get('database', APPWRITE_DATABASE_ID)
        collection = data.get('collection')
        document_id = data.get('document_id', 'unique()')
        document_data = data.get('document_data')
        request_id = data.get('request_id')
        
        if not collection or not document_data:
            return {
                'type': 'create_response',
                'request_id': request_id,
                'success': False,
                'error': 'Collection ID and document_data are required',
                'timestamp': datetime.now().isoformat()
            }
        
        path = f'/databases/{database}/collections/{collection}/documents'
        body = {
            'documentId': document_id,
            'data': document_data
        }
        
        result = make_appwrite_request(context, 'POST', path, body)
        
        response = {
            'type': 'create_response',
            'request_id': request_id,
            'success': True,
            'data': result['data'],
            'timestamp': datetime.now().isoformat()
        }
        
        context.log(f"✅ Document created successfully: {result['data']['$id']}")
        return response
        
    except Exception as error:
        context.error(f"❌ Document creation failed: {str(error)}")
        return {
            'type': 'create_response',
            'request_id': data.get('request_id'),
            'success': False,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        }


def handle_database_update(context, data):
    """Handle database document updates"""
    try:
        context.log(f'🔍 Processing database update: {data}')
        
        database = data.get('database', APPWRITE_DATABASE_ID)
        collection = data.get('collection')
        document_id = data.get('document_id')
        document_data = data.get('document_data')
        request_id = data.get('request_id')
        
        if not all([collection, document_id, document_data]):
            return {
                'type': 'update_response',
                'request_id': request_id,
                'success': False,
                'error': 'Collection ID, document_id, and document_data are required',
                'timestamp': datetime.now().isoformat()
            }
        
        path = f'/databases/{database}/collections/{collection}/documents/{document_id}'
        body = {'data': document_data}
        
        result = make_appwrite_request(context, 'PATCH', path, body)
        
        response = {
            'type': 'update_response',
            'request_id': request_id,
            'success': True,
            'data': result['data'],
            'timestamp': datetime.now().isoformat()
        }
        
        context.log(f"✅ Document updated successfully: {document_id}")
        return response
        
    except Exception as error:
        context.error(f"❌ Document update failed: {str(error)}")
        return {
            'type': 'update_response',
            'request_id': data.get('request_id'),
            'success': False,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        }


def test_database_connection(context):
    """Test database connection"""
    try:
        # Test listing collections
        url = f'{APPWRITE_ENDPOINT}/databases/{APPWRITE_DATABASE_ID}/collections'
        
        headers = {
            'X-Appwrite-Project': APPWRITE_PROJECT_ID,
            'X-Appwrite-Key': APPWRITE_API_KEY,
            'Content-Type': 'application/json'
        }
        
        request_obj = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(request_obj, timeout=10)
        data = json.loads(response.read().decode('utf-8'))
        
        context.log(f"✅ Database connected! Found {data['total']} collections")
        
        collection_names = [col['name'] for col in data.get('collections', [])]
        
        return {
            'status': 'DATABASE_SUCCESS',
            'success': True,
            'message': 'Database connection working via HTTP!',
            'collections_found': data['total'],
            'collection_names': collection_names,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        context.error(f"❌ Database test failed: {str(e)}")
        return {
            'status': 'DATABASE_ERROR',
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def lookup_customer_by_phone(context, phone_number, pin):
    """Look up customer in unified customers collection - same as SMS function"""
    try:
        context.log(f"🔍 Looking up customer {phone_number} in customers database...")
        
        # Try multiple phone number formats (same logic as SMS server)
        phone_variants = [
            phone_number,
            phone_number.replace('+254', '0'),
            phone_number.replace('+254', '254'),
            phone_number.replace('+254', ''),
            f"+254{phone_number.lstrip('0')}" if not phone_number.startswith('+') else phone_number
        ]
        
        for variant in phone_variants:
            query = f'equal("phone_number","{variant}")'
            url = f'{APPWRITE_ENDPOINT}/databases/{APPWRITE_DATABASE_ID}/collections/{CUSTOMERS_COLLECTION_ID}/documents?queries[]={urllib.parse.quote(query)}'
            
            headers = {
                'X-Appwrite-Project': APPWRITE_PROJECT_ID,
                'X-Appwrite-Key': APPWRITE_API_KEY,
                'Content-Type': 'application/json'
            }
            
            request_obj = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(request_obj, timeout=5)
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('documents') and len(data['documents']) > 0:
                customer = data['documents'][0]
                pin_match = customer.get('pin') == pin
                is_registered = customer.get('is_registered') == True
                active = customer.get('active') == True
                
                context.log(f"👤 Found customer: {variant}, registered: {is_registered}, active: {active}, PIN match: {pin_match}")
                
                return {
                    'found': True,
                    'valid_pin': pin_match,
                    'is_registered': is_registered,
                    'active': active,
                    'customer_data': {
                        'phone_number': customer.get('phone_number'),
                        'account_id': customer.get('account_id'),
                        'full_name': customer.get('full_name'),
                        'active': customer.get('active'),
                        'credits': customer.get('credits', 0)
                    }
                }
        
        context.log(f"❌ Customer {phone_number} not found in database")
        return {
            'found': False,
            'valid_pin': False,
            'is_registered': False,
            'active': False
        }
            
    except Exception as e:
        context.error(f"❌ Database connection error: {str(e)}")
        raise e


def make_appwrite_request(context, method, path, body=None):
    """Generic Appwrite API request function"""
    try:
        body_string = json.dumps(body).encode('utf-8') if body else None
        
        headers = {
            'X-Appwrite-Project': APPWRITE_PROJECT_ID,
            'X-Appwrite-Key': APPWRITE_API_KEY,
            'Content-Type': 'application/json'
        }
        
        url = f'{APPWRITE_ENDPOINT}{path}'
        request_obj = urllib.request.Request(url, data=body_string, headers=headers, method=method)
        response = urllib.request.urlopen(request_obj, timeout=10)
        
        response_data = json.loads(response.read().decode('utf-8'))
        
        if 200 <= response.status < 300:
            return {'status': response.status, 'data': response_data}
        else:
            raise Exception(f"HTTP {response.status}: {response_data.get('message', 'Unknown error')}")
            
    except Exception as e:
        context.error(f"Appwrite request failed: {str(e)}")
        raise e
