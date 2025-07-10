"""
Test the Perplexity API function with real Instagram profile data
"""

import asyncio
import json
import os
import logging
from unittest.mock import Mock, patch
import httpx
import pytest
from main import call_perplexity_api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data based on the provided Instagram profile
TEST_PROFILE_DATA = {
    "username": "azaliah.alchemy",
    "hashtag": "vitalpilze",
    "full_name": "Azaliah",
    "biography": "Supreme Mushroom Extracts. Awaken your mind, body, and spirit 𓂀",
    "email": "",
    "phone": "",
    "website": "http://azaliah.at",
    "follower_count": 130,
    "following_count": 121,
    "media_count": 45,
    "is_verified": False,
    "profile_pic_url": "https://scontent-iad3-2.cdninstagram.com/v/t51.2885-19/422523908_408506208259662_2311375772848532570_n.jpg?stp=dst-jpg_s150x150_tt6&_nc_ht=scontent-iad3-2.cdninstagram.com&_nc_cat=106&_nc_oc=Q6cZ2QFmiFquaiuFQyU8ZcWIXqD39At_7mSyIpLtLaUGDGKYd73RWLs14eqtvwG6NvTVFDg&_nc_ohc=EWQgLLeD1JoQ7kNvwE34zSd&_nc_gid=irGzOyMFYlcUwq3FUNiuyw&edm=AEF8tYYBAAAA&ccb=7-5&oh=00_AfS6Vq2WR2wH_zqe-fG0dCWp_i9W6tg44Ux2tUhS-FpBHg&oe=68756FF0&_nc_sid=1e20d2"
}

# Mock successful API response
MOCK_SUCCESS_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": '{"email": "info@azaliah.at", "phone": "+43 123 456 789", "website": "https://azaliah.at"}'
            }
        }
    ]
}

# Mock partial API response (missing some fields)
MOCK_PARTIAL_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": '{"email": "contact@azaliah.at", "phone": "", "website": "https://azaliah.at"}'
            }
        }
    ]
}

# Mock invalid JSON response
MOCK_INVALID_JSON_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": "I found some information but couldn't format it as JSON properly"
            }
        }
    ]
}


class TestPerplexityAPI:
    """Test cases for the Perplexity API function"""
    
    def setup_method(self):
        """Set up test environment"""
        self.api_key = "test_api_key"
        self.profile_data = TEST_PROFILE_DATA.copy()
    
    @pytest.mark.asyncio
    async def test_successful_api_call(self):
        """Test successful API call with valid JSON response"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = MOCK_SUCCESS_RESPONSE
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Call the function
            result = await call_perplexity_api(self.profile_data, self.api_key)
            
            # Verify the result
            assert result == {
                "email": "info@azaliah.at",
                "phone": "+43 123 456 789",
                "website": "https://azaliah.at"
            }
            
            # Verify the API was called with correct parameters
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Check URL and headers
            assert call_args[1]['headers']['Authorization'] == f'Bearer {self.api_key}'
            assert call_args[1]['headers']['Content-Type'] == 'application/json'
            
            # Check request data
            request_data = call_args[1]['json']
            assert request_data['model'] == 'sonar'
            assert len(request_data['messages']) == 2
            assert request_data['messages'][0]['role'] == 'system'
            assert request_data['messages'][1]['role'] == 'user'
            
            # Check that profile information is included in the user message
            user_message = request_data['messages'][1]['content']
            assert 'azaliah.alchemy' in user_message
            assert 'Azaliah' in user_message
            assert 'Supreme Mushroom Extracts' in user_message
            assert '130' in user_message  # followers
            assert '121' in user_message  # following
            assert '45' in user_message   # posts
    
    @pytest.mark.asyncio
    async def test_partial_response(self):
        """Test API call with partial information in response"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock partial response
            mock_response = Mock()
            mock_response.json.return_value = MOCK_PARTIAL_RESPONSE
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Call the function
            result = await call_perplexity_api(self.profile_data, self.api_key)
            
            # Verify the result includes partial data
            assert result == {
                "email": "contact@azaliah.at",
                "phone": "",
                "website": "https://azaliah.at"
            }
    
    @pytest.mark.asyncio
    async def test_invalid_json_response(self):
        """Test API call with invalid JSON response"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock invalid JSON response
            mock_response = Mock()
            mock_response.json.return_value = MOCK_INVALID_JSON_RESPONSE
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Call the function
            result = await call_perplexity_api(self.profile_data, self.api_key)
            
            # Verify fallback response is returned
            assert result == {"email": "", "phone": "", "website": ""}
    
    @pytest.mark.asyncio
    async def test_http_error_response(self):
        """Test API call with HTTP error"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock HTTP error
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_post.side_effect = httpx.HTTPStatusError(
                "Unauthorized", 
                request=Mock(), 
                response=mock_response
            )
            
            # Call the function
            result = await call_perplexity_api(self.profile_data, self.api_key)
            
            # Verify fallback response is returned
            assert result == {"email": "", "phone": "", "website": ""}
    
    @pytest.mark.asyncio
    async def test_network_error(self):
        """Test API call with network error"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock network error
            mock_post.side_effect = httpx.ConnectError("Network error")
            
            # Call the function
            result = await call_perplexity_api(self.profile_data, self.api_key)
            
            # Verify fallback response is returned
            assert result == {"email": "", "phone": "", "website": ""}
    
    @pytest.mark.asyncio
    async def test_missing_profile_fields(self):
        """Test API call with missing profile fields"""
        # Create profile data with missing fields
        minimal_profile = {
            "username": "test_user",
            "full_name": "",
            "biography": "",
            "follower_count": 0,
            "following_count": 0,
            "media_count": 0,
            "is_verified": False
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = MOCK_SUCCESS_RESPONSE
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Call the function
            result = await call_perplexity_api(minimal_profile, self.api_key)
            
            # Verify the function handles missing fields gracefully
            assert isinstance(result, dict)
            assert 'email' in result
            assert 'phone' in result
            assert 'website' in result
            
            # Check that the API was called with the minimal profile data
            call_args = mock_post.call_args
            user_message = call_args[1]['json']['messages'][1]['content']
            assert 'test_user' in user_message
    
    @pytest.mark.asyncio
    async def test_german_system_message(self):
        """Test that the system message is in German"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = MOCK_SUCCESS_RESPONSE
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Call the function
            await call_perplexity_api(self.profile_data, self.api_key)
            
            # Check that the system message is in German
            call_args = mock_post.call_args
            system_message = call_args[1]['json']['messages'][0]['content']
            assert 'hilfreicher Recherche-Assistent' in system_message
            assert 'Kontaktinfos' in system_message
    
    @pytest.mark.asyncio
    async def test_profile_description_format(self):
        """Test that profile description is properly formatted"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = MOCK_SUCCESS_RESPONSE
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Call the function
            await call_perplexity_api(self.profile_data, self.api_key)
            
            # Check that profile description contains all expected fields
            call_args = mock_post.call_args
            user_message = call_args[1]['json']['messages'][1]['content']
            
            # Check for profile information structure
            assert 'Instagram Profile Information:' in user_message
            assert '- Username: azaliah.alchemy' in user_message
            assert '- Full Name: Azaliah' in user_message
            assert '- Biography: Supreme Mushroom Extracts' in user_message
            assert '- Followers: 130' in user_message
            assert '- Following: 121' in user_message
            assert '- Posts: 45' in user_message
            assert '- Verified: False' in user_message


async def test_with_real_api():
    """
    Test with real Perplexity API (requires PERPLEXITY_API_KEY environment variable)
    This test is skipped if no API key is provided
    """
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        logger.info("Skipping real API test - no PERPLEXITY_API_KEY provided")
        return
    
    logger.info("Testing with real Perplexity API...")
    
    # Use the test profile data
    result = await call_perplexity_api(TEST_PROFILE_DATA, api_key)
    
    logger.info(f"Real API result: {result}")
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert 'email' in result
    assert 'phone' in result
    assert 'website' in result
    
    # Log the results for manual verification
    logger.info("=== REAL API TEST RESULTS ===")
    logger.info(f"Profile: {TEST_PROFILE_DATA['username']} ({TEST_PROFILE_DATA['full_name']})")
    logger.info(f"Biography: {TEST_PROFILE_DATA['biography']}")
    logger.info(f"Known website: {TEST_PROFILE_DATA['website']}")
    logger.info(f"API found email: {result.get('email', 'Not found')}")
    logger.info(f"API found phone: {result.get('phone', 'Not found')}")
    logger.info(f"API found website: {result.get('website', 'Not found')}")
    logger.info("=" * 50)


if __name__ == "__main__":
    # Run the tests
    logger.info("Running Perplexity API tests...")
    
    # Run async test with real API if available
    asyncio.run(test_with_real_api())
    
    logger.info("Test completed. Run with 'python -m pytest test_perplexity_api.py -v' for full test suite.")