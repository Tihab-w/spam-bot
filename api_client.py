"""
Spam Classifier AI - API Client for External Applications
SRS Section: 4.2 (System Integration Strategy)
Used by external apps to integrate spam classification
"""

import requests
import json
from typing import Dict, List, Optional

class SpamClassifierClient:
    """
    Client for integrating external applications with Spam Classifier AI
    
    Usage:
        client = SpamClassifierClient("http://localhost:5000")
        result = client.classify("Your message here")
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize client
        
        Args:
            base_url: URL of the Spam Classifier API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'SpamClassifier-Client/1.0'
        })
    
    def classify(self, message: str, detailed: bool = True) -> Dict:
        """
        Classify a single message
        
        Args:
            message: Text to classify
            detailed: Return detailed explanation
        
        Returns:
            dict: Classification result
        """
        try:
            payload = {
                'message': message,
                'return_details': detailed
            }
            
            response = self.session.post(
                f"{self.base_url}/api/classify",
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Cannot connect to Spam Classifier server',
                'code': 'CONNECTION_ERROR'
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timed out',
                'code': 'TIMEOUT'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'code': 'UNKNOWN_ERROR'
            }
    
    def batch_classify(self, messages: List[str]) -> Dict:
        """
        Classify multiple messages at once
        
        Args:
            messages: List of messages to classify
        
        Returns:
            dict: Batch classification results
        """
        try:
            payload = {'messages': messages}
            
            response = self.session.post(
                f"{self.base_url}/api/batch-classify",
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'code': 'BATCH_ERROR'
            }
    
    def submit_feedback(self, message: str, predicted: str, correct: str) -> Dict:
        """
        Submit feedback for model improvement (SRS Section 5.1)
        
        Args:
            message: Original message
            predicted: Model's prediction
            correct: Correct classification
        
        Returns:
            dict: Feedback submission result
        """
        try:
            payload = {
                'message': message,
                'predicted_label': predicted,
                'correct_label': correct
            }
            
            response = self.session.post(
                f"{self.base_url}/api/feedback",
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def health_check(self) -> Dict:
        """
        Check if the API server is running
        
        Returns:
            dict: Health status
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/health",
                timeout=5
            )
            return response.json()
        except:
            return {
                'status': 'unavailable',
                'error': 'Server not reachable'
            }
    
    def integrate_with_message(self, message: str, platform: str = "generic") -> Dict:
        """
        Complete integration method for messaging platforms
        SRS Section 4.2 - Integration Strategy
        
        Args:
            message: Incoming message
            platform: Platform name (telegram, email, etc.)
        
        Returns:
            dict: Action recommendation
        """
        # Step 1: Classify message
        classification = self.classify(message)
        
        if not classification.get('success'):
            # SRS Section 5.3 - Fallback Mechanism
            return {
                'action': 'deliver',
                'reason': 'Classification unavailable - message delivered as safe',
                'classification': classification
            }
        
        # Step 2: Determine action based on result and confidence
        result = classification['result']
        confidence = classification['confidence']
        
        if result == 'SPAM' and confidence > 80:
            action = 'block'
            reason = f"High confidence spam detected: {classification.get('explanation', '')}"
        elif result == 'SPAM' and confidence > 50:
            action = 'flag'
            reason = "Potential spam - flagged for review"
        else:
            action = 'deliver'
            reason = "Message appears legitimate"
        
        return {
            'action': action,
            'reason': reason,
            'classification': classification,
            'platform': platform
        }


# ==================== DEMONSTRATION ====================

if __name__ == "__main__":
    print("=" * 60)
    print("SPAM CLASSIFIER CLIENT - INTEGRATION DEMO")
    print("=" * 60)
    
    # Initialize client
    client = SpamClassifierClient("http://localhost:5000")
    
    # Check server health
    print("\n1. Checking server health...")
    health = client.health_check()
    print(f"   Status: {health.get('status', 'unknown')}")
    
    # Test single classification
    print("\n2. Classifying single message...")
    test_messages = [
        "Congratulations! You've won a free iPhone! Click here to claim your prize!",
        "Hey, are you coming to the meeting at 3pm?",
        "URGENT: Your bank account has been compromised! Send your password immediately!",
        "Don't forget to pick up milk on your way home"
    ]
    
    for msg in test_messages:
        result = client.classify(msg)
        if result.get('success'):
            print(f"\n   Message: {msg[:50]}...")
            print(f"   Result: {result['result']} (Confidence: {result['confidence']}%)")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Test batch classification
    print("\n3. Batch classifying messages...")
    batch_result = client.batch_classify(test_messages)
    if batch_result.get('success'):
        print(f"   Total: {batch_result['total_messages']}")
        print(f"   Spam: {batch_result['spam_count']}")
        print(f"   Legitimate: {batch_result['legitimate_count']}")
    
    # Test integration workflow
    print("\n4. Testing integration workflow...")
    for msg in test_messages:
        action = client.integrate_with_message(msg, platform="telegram")
        print(f"   Message: {msg[:40]}...")
        print(f"   Action: {action['action'].upper()}")
        print(f"   Reason: {action['reason']}\n")
    
    print("=" * 60)
    print("INTEGRATION DEMO COMPLETE")
    print("=" * 60)