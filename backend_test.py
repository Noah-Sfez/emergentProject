#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Multi-Family Office Platform
Tests all API endpoints with authentication, role-based access, and data persistence
"""

import asyncio
import aiohttp
import json
import base64
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = None
        self.admin_token = None
        self.member_token = None
        self.test_results = []
        self.family_office_id = None
        self.family_id = None
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    async def make_request(self, method: str, endpoint: str, data: Dict = None, 
                          token: str = None, files: Dict = None) -> Dict[str, Any]:
        """Make HTTP request with proper headers"""
        url = f"{API_BASE}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers) as response:
                    return {
                        "status": response.status,
                        "data": await response.json() if response.content_type == 'application/json' else await response.text()
                    }
            elif method.upper() == "POST":
                if files:
                    # For file uploads, don't set content-type header
                    headers.pop("Content-Type", None)
                    form_data = aiohttp.FormData()
                    for key, value in data.items():
                        form_data.add_field(key, str(value))
                    for key, file_data in files.items():
                        form_data.add_field(key, file_data['content'], filename=file_data['filename'])
                    
                    async with self.session.post(url, headers=headers, data=form_data) as response:
                        return {
                            "status": response.status,
                            "data": await response.json() if response.content_type == 'application/json' else await response.text()
                        }
                else:
                    async with self.session.post(url, headers=headers, json=data) as response:
                        return {
                            "status": response.status,
                            "data": await response.json() if response.content_type == 'application/json' else await response.text()
                        }
        except Exception as e:
            return {"status": 0, "data": f"Request failed: {str(e)}"}
            
    async def test_health_check(self):
        """Test health check endpoint"""
        response = await self.make_request("GET", "/health")
        success = response["status"] == 200 and "healthy" in str(response["data"])
        self.log_test("Health Check", success, f"Status: {response['status']}")
        return success
        
    async def test_admin_login(self):
        """Test admin login"""
        login_data = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        
        response = await self.make_request("POST", "/auth/login", login_data)
        success = response["status"] == 200
        
        if success and isinstance(response["data"], dict):
            self.admin_token = response["data"].get("access_token")
            user_data = response["data"].get("user", {})
            success = success and user_data.get("role") == "admin"
            self.log_test("Admin Login", success, f"Token received: {bool(self.admin_token)}")
        else:
            self.log_test("Admin Login", False, f"Status: {response['status']}, Data: {response['data']}")
            
        return success
        
    async def test_member_login(self):
        """Test family member login"""
        login_data = {
            "email": "member@demo.com",
            "password": "member123"
        }
        
        response = await self.make_request("POST", "/auth/login", login_data)
        success = response["status"] == 200
        
        if success and isinstance(response["data"], dict):
            self.member_token = response["data"].get("access_token")
            user_data = response["data"].get("user", {})
            success = success and user_data.get("role") == "family_member"
            self.family_id = user_data.get("family_id")
            self.log_test("Family Member Login", success, f"Token received: {bool(self.member_token)}")
        else:
            self.log_test("Family Member Login", False, f"Status: {response['status']}, Data: {response['data']}")
            
        return success
        
    async def test_invalid_login(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "invalid@demo.com",
            "password": "wrongpassword"
        }
        
        response = await self.make_request("POST", "/auth/login", login_data)
        success = response["status"] == 401
        self.log_test("Invalid Login (Should Fail)", success, f"Status: {response['status']}")
        return success
        
    async def test_token_validation(self):
        """Test token validation with /auth/me"""
        if not self.admin_token:
            self.log_test("Token Validation", False, "No admin token available")
            return False
            
        response = await self.make_request("GET", "/auth/me", token=self.admin_token)
        success = response["status"] == 200
        
        if success and isinstance(response["data"], dict):
            user_data = response["data"]
            success = success and user_data.get("email") == "admin@demo.com"
            
        self.log_test("Token Validation", success, f"Status: {response['status']}")
        return success
        
    async def test_get_family_offices(self):
        """Test retrieving family offices"""
        if not self.admin_token:
            self.log_test("Get Family Offices", False, "No admin token available")
            return False
            
        response = await self.make_request("GET", "/family-offices", token=self.admin_token)
        success = response["status"] == 200
        
        if success and isinstance(response["data"], list):
            family_offices = response["data"]
            success = len(family_offices) > 0
            if success and family_offices:
                self.family_office_id = family_offices[0].get("id")
                
        self.log_test("Get Family Offices", success, f"Found {len(response['data']) if isinstance(response['data'], list) else 0} family offices")
        return success
        
    async def test_create_family_office(self):
        """Test creating a new family office (admin only)"""
        if not self.admin_token:
            self.log_test("Create Family Office", False, "No admin token available")
            return False
            
        family_office_data = {
            "name": "Test Family Office",
            "description": "Test family office for API testing"
        }
        
        response = await self.make_request("POST", "/family-offices", family_office_data, token=self.admin_token)
        success = response["status"] == 200
        
        if success and isinstance(response["data"], dict):
            created_fo = response["data"]
            success = created_fo.get("name") == family_office_data["name"]
            
        self.log_test("Create Family Office", success, f"Status: {response['status']}")
        return success
        
    async def test_member_cannot_create_family_office(self):
        """Test that family member cannot create family office"""
        if not self.member_token:
            self.log_test("Member Cannot Create Family Office", False, "No member token available")
            return False
            
        family_office_data = {
            "name": "Unauthorized Family Office",
            "description": "This should fail"
        }
        
        response = await self.make_request("POST", "/family-offices", family_office_data, token=self.member_token)
        success = response["status"] == 403  # Should be forbidden
        
        self.log_test("Member Cannot Create Family Office (Should Fail)", success, f"Status: {response['status']}")
        return success
        
    async def test_get_families(self):
        """Test retrieving families"""
        if not self.admin_token:
            self.log_test("Get Families", False, "No admin token available")
            return False
            
        response = await self.make_request("GET", "/families", token=self.admin_token)
        success = response["status"] == 200
        
        if success and isinstance(response["data"], list):
            families = response["data"]
            success = len(families) > 0
            if success and families and not self.family_id:
                self.family_id = families[0].get("id")
                
        self.log_test("Get Families", success, f"Found {len(response['data']) if isinstance(response['data'], list) else 0} families")
        return success
        
    async def test_create_family(self):
        """Test creating a new family"""
        if not self.admin_token or not self.family_office_id:
            self.log_test("Create Family", False, "Missing admin token or family office ID")
            return False
            
        family_data = {
            "name": "Test Family",
            "family_office_id": self.family_office_id
        }
        
        response = await self.make_request("POST", "/families", family_data, token=self.admin_token)
        success = response["status"] == 200
        
        if success and isinstance(response["data"], dict):
            created_family = response["data"]
            success = created_family.get("name") == family_data["name"]
            
        self.log_test("Create Family", success, f"Status: {response['status']}")
        return success
        
    async def test_get_documents(self):
        """Test retrieving documents"""
        if not self.member_token:
            self.log_test("Get Documents", False, "No member token available")
            return False
            
        response = await self.make_request("GET", "/documents", token=self.member_token)
        success = response["status"] == 200
        
        self.log_test("Get Documents", success, f"Status: {response['status']}")
        return success
        
    async def test_upload_document(self):
        """Test document upload functionality"""
        if not self.member_token:
            self.log_test("Upload Document", False, "Missing member token")
            return False
            
        # Get family_id from member user info if not available
        if not self.family_id:
            user_response = await self.make_request("GET", "/auth/me", token=self.member_token)
            if user_response["status"] == 200 and isinstance(user_response["data"], dict):
                self.family_id = user_response["data"].get("family_id")
                
        if not self.family_id:
            self.log_test("Upload Document", False, "Could not get family ID")
            return False
            
        # Create a test file content
        test_content = "This is a test document for API testing"
        test_file_data = {
            'content': test_content.encode(),
            'filename': 'test_document.txt'
        }
        
        form_data = {
            'document_type': 'other',
            'family_id': self.family_id,
            'description': 'Test document upload',
            'tags': 'test,api'
        }
        
        response = await self.make_request("POST", "/documents/upload", 
                                         data=form_data, 
                                         token=self.member_token,
                                         files={'file': test_file_data})
        
        success = response["status"] == 200
        
        if success and isinstance(response["data"], dict):
            doc_data = response["data"]
            success = doc_data.get("filename") == "test_document.txt"
        else:
            # Log the error details for debugging
            self.log_test("Upload Document", success, f"Status: {response['status']}, Data: {response['data']}")
            return success
            
        self.log_test("Upload Document", success, f"Status: {response['status']}")
        return success
        
    async def test_get_meetings(self):
        """Test retrieving meetings"""
        if not self.member_token:
            self.log_test("Get Meetings", False, "No member token available")
            return False
            
        response = await self.make_request("GET", "/meetings", token=self.member_token)
        success = response["status"] == 200
        
        self.log_test("Get Meetings", success, f"Status: {response['status']}")
        return success
        
    async def test_create_meeting(self):
        """Test creating a meeting"""
        if not self.admin_token or not self.family_id:
            self.log_test("Create Meeting", False, "Missing admin token or family ID")
            return False
            
        # Create meeting for tomorrow
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        meeting_data = {
            "title": "Test Meeting",
            "description": "API test meeting",
            "start_time": start_time.isoformat() + "Z",
            "end_time": end_time.isoformat() + "Z",
            "family_id": self.family_id,
            "advisor_id": "test-advisor-id",
            "attendees": [],
            "meeting_link": "https://zoom.us/test"
        }
        
        response = await self.make_request("POST", "/meetings", meeting_data, token=self.admin_token)
        success = response["status"] == 200
        
        if success and isinstance(response["data"], dict):
            meeting = response["data"]
            success = meeting.get("title") == meeting_data["title"]
            
        self.log_test("Create Meeting", success, f"Status: {response['status']}")
        return success
        
    async def test_get_messages(self):
        """Test retrieving messages"""
        if not self.member_token:
            self.log_test("Get Messages", False, "No member token available")
            return False
            
        response = await self.make_request("GET", "/messages", token=self.member_token)
        success = response["status"] == 200
        
        self.log_test("Get Messages", success, f"Status: {response['status']}")
        return success
        
    async def test_send_message(self):
        """Test sending a message"""
        if not self.member_token or not self.family_id:
            self.log_test("Send Message", False, "Missing member token or family ID")
            return False
            
        message_data = {
            "content": "Test message from API testing",
            "message_type": "text",
            "recipient_id": "test-recipient-id",
            "family_id": self.family_id
        }
        
        response = await self.make_request("POST", "/messages", message_data, token=self.member_token)
        success = response["status"] == 200
        
        if success and isinstance(response["data"], dict):
            message = response["data"]
            success = message.get("content") == message_data["content"]
            
        self.log_test("Send Message", success, f"Status: {response['status']}")
        return success
        
    async def test_cors_headers(self):
        """Test CORS headers are properly set"""
        try:
            async with self.session.options(f"{API_BASE}/health") as response:
                cors_headers = {
                    'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
                    'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
                    'access-control-allow-headers': response.headers.get('access-control-allow-headers')
                }
                success = any(cors_headers.values())
                self.log_test("CORS Headers", success, f"Headers present: {bool(cors_headers)}")
                return success
        except Exception as e:
            self.log_test("CORS Headers", False, f"Error: {str(e)}")
            return False
            
    async def test_unauthorized_access(self):
        """Test that protected endpoints require authentication"""
        response = await self.make_request("GET", "/auth/me")  # No token
        success = response["status"] == 401 or response["status"] == 403
        
        self.log_test("Unauthorized Access (Should Fail)", success, f"Status: {response['status']}")
        return success
        
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Multi-Family Office Platform Backend API Tests")
        print(f"📍 Testing against: {BACKEND_URL}")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Basic connectivity tests
            await self.test_health_check()
            
            # Authentication tests
            await self.test_admin_login()
            await self.test_member_login()
            await self.test_invalid_login()
            await self.test_token_validation()
            await self.test_unauthorized_access()
            
            # Family Office tests
            await self.test_get_family_offices()
            await self.test_create_family_office()
            await self.test_member_cannot_create_family_office()
            
            # Family tests
            await self.test_get_families()
            await self.test_create_family()
            
            # Document tests
            await self.test_get_documents()
            await self.test_upload_document()
            
            # Meeting tests
            await self.test_get_meetings()
            await self.test_create_meeting()
            
            # Message tests
            await self.test_get_messages()
            await self.test_send_message()
            
            # Infrastructure tests
            await self.test_cors_headers()
            
        finally:
            await self.cleanup_session()
            
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if total - passed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['details']}")
                    
        print(f"\n🎯 Success Rate: {(passed/total)*100:.1f}%")
        
        return passed, total

async def main():
    """Main test runner"""
    tester = BackendTester()
    passed, total = await tester.run_all_tests()
    
    # Exit with error code if tests failed
    if passed < total:
        exit(1)
    else:
        print("\n🎉 All tests passed!")
        exit(0)

if __name__ == "__main__":
    asyncio.run(main())