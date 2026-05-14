"""
Integration Testing Script
SRS Section: 5.3 (Deployment Considerations - Phased Rollout)
Tests all components and their integration
"""

import sys
import os
import json
import time
import requests
from typing import Dict, List, Tuple

# Test configuration
API_BASE_URL = "http://localhost:5000"
TEST_MESSAGES = {
    'spam_obvious': "CONGRATULATIONS! You've won a FREE iPhone 15 Pro Max! Click here to claim your prize now! Limited time offer!!!",
    'spam_phishing': "URGENT: Your PayPal account has been limited! Verify your identity immediately by sending your password!",
    'spam_advertisement': "Buy cheap Viagra now! Best prices guaranteed! Free worldwide shipping! Order today!",
    'ham_personal': "Hey, are you free for lunch tomorrow? Let me know what time works for you.",
    'ham_work': "The quarterly report is due by Friday. Please submit your sections by Thursday afternoon.",
    'ham_meeting': "Reminder: Team standup meeting at 9:30am in Conference Room B.",
    'edge_case_short': "OK",
    'edge_case_numbers': "1234567890",
    'edge_case_empty': "",
    'edge_case_long': "This is a very long message that discusses normal everyday topics like going to the store buying groceries meeting friends for coffee and discussing the weather forecast for the upcoming weekend.",
    'mixed_urgent': "Important meeting tomorrow! Don't forget to bring the documents we discussed.",
    'mixed_offer': "Special offer for valued customers: 20% off on all products this week only!"
}

class IntegrationTester:
    """
    Comprehensive Integration Testing Suite
    """
    
    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url.rstrip('/')
        self.results = []
        self.passed = 0
        self.failed = 0
        self.total_time = 0
        
    def print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70)
    
    def print_result(self, test_name: str, passed: bool, message: str = ""):
        """Print test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} | {test_name}")
        if message and not passed:
            print(f"         {message}")
    
    def test_health_endpoint(self) -> bool:
        """Test API health check endpoint"""
        self.print_header("TEST 1: API Health Check")
        
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                assert 'status' in data, "Missing 'status' field"
                assert data['status'] == 'healthy', f"Status is {data['status']}, expected 'healthy'"
                assert 'model_loaded' in data, "Missing 'model_loaded' field"
                assert data['model_loaded'] == True, "Model not loaded"
                
                self.print_result("Health endpoint returns 200", True)
                self.print_result("Response contains 'status' field", True)
                self.print_result("Status is 'healthy'", True)
                self.print_result("Model is loaded", True)
                self.passed += 4
                return True
            else:
                self.print_result("Health endpoint", False, f"Status code: {response.status_code}")
                self.failed += 1
                return False
                
        except requests.exceptions.ConnectionError:
            self.print_result("Health endpoint", False, "Cannot connect to server. Is app.py running?")
            self.failed += 1
            return False
        except Exception as e:
            self.print_result("Health endpoint", False, str(e))
            self.failed += 1
            return False
    
    def test_classify_endpoint(self) -> bool:
        """Test single message classification endpoint"""
        self.print_header("TEST 2: Single Classification Endpoint")
        
        all_passed = True
        
        for name, message in TEST_MESSAGES.items():
            try:
                payload = {
                    'message': message,
                    'return_details': True
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{self.api_url}/api/classify",
                    json=payload,
                    timeout=10
                )
                elapsed_time = time.time() - start_time
                
                # Check status code
                if response.status_code != 200:
                    self.print_result(f"Classify '{name}'", False, f"Status: {response.status_code}")
                    self.failed += 1
                    all_passed = False
                    continue
                
                data = response.json()
                
                # Verify response structure
                checks = []
                
                # Check 'success' field
                if 'success' in data and data['success'] == True:
                    checks.append(True)
                else:
                    checks.append(False)
                    self.print_result(f"Response success for '{name}'", False, f"Data: {data}")
                
                # Check 'result' field
                if 'result' in data:
                    if data['result'] in ['SPAM', 'LEGITIMATE']:
                        checks.append(True)
                    else:
                        checks.append(False)
                else:
                    checks.append(False)
                
                # Check 'confidence' field
                if 'confidence' in data:
                    if isinstance(data['confidence'], (int, float)):
                        checks.append(True)
                    else:
                        checks.append(False)
                else:
                    checks.append(False)
                
                # Check response time
                if elapsed_time < 5:
                    checks.append(True)
                else:
                    checks.append(False)
                
                if all(checks):
                    self.print_result(
                        f"Classify '{name}'",
                        True,
                        f"Result: {data['result']}, Confidence: {data['confidence']}%, Time: {elapsed_time:.3f}s"
                    )
                    self.passed += 1
                else:
                    self.print_result(f"Classify '{name}'", False)
                    self.failed += 1
                    all_passed = False
                
                self.total_time += elapsed_time
                
            except Exception as e:
                self.print_result(f"Classify '{name}'", False, str(e))
                self.failed += 1
                all_passed = False
        
        return all_passed
    
    def test_batch_classify(self) -> bool:
        """Test batch classification endpoint"""
        self.print_header("TEST 3: Batch Classification Endpoint")
        
        try:
            messages = list(TEST_MESSAGES.values())[:5]
            
            payload = {'messages': messages}
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/api/batch-classify",
                json=payload,
                timeout=15
            )
            elapsed_time = time.time() - start_time
            
            if response.status_code != 200:
                self.print_result("Batch classify", False, f"Status: {response.status_code}")
                self.failed += 1
                return False
            
            data = response.json()
            
            # Verify structure
            checks = [
                ('success' in data and data['success'] == True, "Success field"),
                ('total_messages' in data and data['total_messages'] == len(messages), "Total messages count"),
                ('spam_count' in data, "Spam count field"),
                ('legitimate_count' in data, "Legitimate count field"),
                ('results' in data and len(data['results']) == len(messages), "Results length matches"),
                (data['spam_count'] + data['legitimate_count'] == len(messages), "Count sum matches total")
            ]
            
            for passed, check_name in checks:
                self.print_result(f"Batch - {check_name}", passed)
                if passed:
                    self.passed += 1
                else:
                    self.failed += 1
            
            self.print_result(
                "Batch response time",
                elapsed_time < 10,
                f"Time: {elapsed_time:.3f}s for {len(messages)} messages"
            )
            if elapsed_time < 10:
                self.passed += 1
            else:
                self.failed += 1
            
            return all(c[0] for c in checks)
            
        except Exception as e:
            self.print_result("Batch classify", False, str(e))
            self.failed += 1
            return False
    
    def test_feedback_endpoint(self) -> bool:
        """Test feedback submission endpoint"""
        self.print_header("TEST 4: Feedback Endpoint")
        
        try:
            payload = {
                'message': 'Test message for feedback',
                'predicted_label': 'SPAM',
                'correct_label': 'LEGITIMATE'
            }
            
            response = requests.post(
                f"{self.api_url}/api/feedback",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    self.print_result("Feedback submission", True)
                    self.passed += 1
                    return True
                else:
                    self.print_result("Feedback submission", False, f"Response: {data}")
                    self.failed += 1
                    return False
            else:
                self.print_result("Feedback submission", False, f"Status: {response.status_code}")
                self.failed += 1
                return False
                
        except Exception as e:
            self.print_result("Feedback submission", False, str(e))
            self.failed += 1
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling"""
        self.print_header("TEST 5: Error Handling")
        
        tests = [
            {
                'name': 'Missing message field',
                'payload': {},
                'expected_status': 400
            },
            {
                'name': 'Empty message',
                'payload': {'message': ''},
                'expected_status': 200  # Should handle empty gracefully
            },
            {
                'name': 'Invalid JSON',
                'endpoint': '/api/classify',
                'data': 'invalid json',
                'content_type': 'application/json',
                'expected_status': 500
            }
        ]
        
        all_passed = True
        
        for test in tests:
            try:
                endpoint = test.get('endpoint', '/api/classify')
                content_type = test.get('content_type', 'application/json')
                
                if content_type == 'application/json':
                    response = requests.post(
                        f"{self.api_url}{endpoint}",
                        json=test.get('payload', test.get('data', {})),
                        timeout=5
                    )
                else:
                    response = requests.post(
                        f"{self.api_url}{endpoint}",
                        data=test.get('data', ''),
                        timeout=5
                    )
                
                expected = test.get('expected_status', 200)
                
                if response.status_code == expected:
                    self.print_result(f"Error handling - {test['name']}", True)
                    self.passed += 1
                else:
                    self.print_result(
                        f"Error handling - {test['name']}",
                        False,
                        f"Expected status {expected}, got {response.status_code}"
                    )
                    self.failed += 1
                    all_passed = False
                    
            except Exception as e:
                self.print_result(f"Error handling - {test['name']}", False, str(e))
                self.failed += 1
                all_passed = False
        
        return all_passed
    
    def test_spam_detection_accuracy(self) -> bool:
        """Test spam detection on known examples"""
        self.print_header("TEST 6: Spam Detection Accuracy")
        
        # Expected results
        expected_spam = [
            'spam_obvious', 'spam_phishing', 'spam_advertisement'
        ]
        expected_ham = [
            'ham_personal', 'ham_work', 'ham_meeting'
        ]
        
        all_passed = True
        
        # Test spam detection
        for name in expected_spam:
            try:
                response = requests.post(
                    f"{self.api_url}/api/classify",
                    json={'message': TEST_MESSAGES[name]},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get('result', '')
                    
                    if result == 'SPAM':
                        self.print_result(f"Spam detection - {name}", True)
                        self.passed += 1
                    else:
                        self.print_result(
                            f"Spam detection - {name}",
                            False,
                            f"Expected SPAM, got {result}"
                        )
                        self.failed += 1
                        all_passed = False
                        
            except Exception as e:
                self.print_result(f"Spam detection - {name}", False, str(e))
                self.failed += 1
                all_passed = False
        
        # Test ham detection
        for name in expected_ham:
            try:
                response = requests.post(
                    f"{self.api_url}/api/classify",
                    json={'message': TEST_MESSAGES[name]},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = data.get('result', '')
                    
                    if result == 'LEGITIMATE':
                        self.print_result(f"Ham detection - {name}", True)
                        self.passed += 1
                    else:
                        self.print_result(
                            f"Ham detection - {name}",
                            False,
                            f"Expected LEGITIMATE, got {result}"
                        )
                        self.failed += 1
                        all_passed = False
                        
            except Exception as e:
                self.print_result(f"Ham detection - {name}", False, str(e))
                self.failed += 1
                all_passed = False
        
        return all_passed
    
    def test_performance(self) -> bool:
        """Test API performance under load"""
        self.print_header("TEST 7: Performance Testing")
        
        all_passed = True
        iterations = 10
        
        print(f"  Sending {iterations} requests...")
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                response = requests.post(
                    f"{self.api_url}/api/classify",
                    json={'message': TEST_MESSAGES['spam_obvious']},
                    timeout=10
                )
                
                if response.status_code != 200:
                    self.print_result(f"Performance - Request {i+1}", False, f"Status: {response.status_code}")
                    self.failed += 1
                    all_passed = False
                    
            except Exception as e:
                self.print_result(f"Performance - Request {i+1}", False, str(e))
                self.failed += 1
                all_passed = False
        
        total_time = time.time() - start_time
        avg_time = total_time / iterations
        req_per_second = iterations / total_time
        
        self.print_result(
            f"Average response time: {avg_time:.3f}s",
            avg_time < 2.0,
            f"Target: < 2.0s"
        )
        if avg_time < 2.0:
            self.passed += 1
        else:
            self.failed += 1
        
        self.print_result(
            f"Requests per second: {req_per_second:.2f}",
            req_per_second > 0.5,
            f"Target: > 0.5 req/s"
        )
        if req_per_second > 0.5:
            self.passed += 1
        else:
            self.failed += 1
        
        return all_passed
    
    def test_model_import(self) -> bool:
        """Test that model.py can be imported and used directly"""
        self.print_header("TEST 8: Model Direct Import")
        
        try:
            # Try importing the model
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from model import SpamClassifier
            
            self.print_result("Import SpamClassifier", True)
            self.passed += 1
            
            # Try creating instance
            classifier = SpamClassifier()
            self.print_result("Create SpamClassifier instance", True)
            self.passed += 1
            
            # Check if methods exist
            methods = ['train', 'predict', 'preprocess_text', 'load_model', 'get_feature_importance']
            for method in methods:
                has_method = hasattr(classifier, method) and callable(getattr(classifier, method))
                self.print_result(f"Method '{method}' exists", has_method)
                if has_method:
                    self.passed += 1
                else:
                    self.failed += 1
            
            return True
            
        except Exception as e:
            self.print_result("Model import", False, str(e))
            self.failed += 1
            return False
    
    def test_api_client_module(self) -> bool:
        """Test the API client module"""
        self.print_header("TEST 9: API Client Module")
        
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from api_client import SpamClassifierClient
            
            self.print_result("Import SpamClassifierClient", True)
            self.passed += 1
            
            # Create client
            client = SpamClassifierClient(self.api_url)
            self.print_result("Create client instance", True)
            self.passed += 1
            
            # Test health check
            health = client.health_check()
            self.print_result(
                "Client health check",
                health.get('status') == 'healthy',
                f"Status: {health.get('status')}"
            )
            if health.get('status') == 'healthy':
                self.passed += 1
            else:
                self.failed += 1
            
            # Test classify
            result = client.classify(TEST_MESSAGES['spam_obvious'])
            self.print_result(
                "Client classify method",
                result.get('success') == True,
                f"Result: {result.get('result', 'N/A')}"
            )
            if result.get('success'):
                self.passed += 1
            else:
                self.failed += 1
            
            # Test integration method
            action = client.integrate_with_message(TEST_MESSAGES['spam_obvious'])
            self.print_result(
                "Client integration method",
                'action' in action,
                f"Action: {action.get('action', 'N/A')}"
            )
            if 'action' in action:
                self.passed += 1
            else:
                self.failed += 1
            
            return True
            
        except Exception as e:
            self.print_result("API Client module", False, str(e))
            self.failed += 1
            return False
    
    def run_all_tests(self) -> Dict:
        """Run all integration tests"""
        print("=" * 70)
        print("  SPAM CLASSIFIER AI - INTEGRATION TEST SUITE")
        print("  SRS Section 5.3 - Phased Rollout Testing")
        print("=" * 70)
        print(f"  API URL: {self.api_url}")
        print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_start = time.time()
        
        # Run all tests
        tests = [
            ("API Health Check", self.test_health_endpoint),
            ("Single Classification", self.test_classify_endpoint),
            ("Batch Classification", self.test_batch_classify),
            ("Feedback Endpoint", self.test_feedback_endpoint),
            ("Error Handling", self.test_error_handling),
            ("Spam Detection Accuracy", self.test_spam_detection_accuracy),
            ("Performance Testing", self.test_performance),
            ("Model Direct Import", self.test_model_import),
            ("API Client Module", self.test_api_client_module),
        ]
        
        test_results = {}
        
        for test_name, test_func in tests:
            test_results[test_name] = test_func()
        
        total_time = time.time() - total_start
        
        # Print summary
        self.print_header("TEST SUMMARY")
        print(f"  Total Tests: {self.passed + self.failed}")
        print(f"  Passed: {self.passed} ✅")
        print(f"  Failed: {self.failed} ❌")
        print(f"  Pass Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")
        print(f"  Total Time: {total_time:.2f}s")
        print("=" * 70)
        
        return {
            'total': self.passed + self.failed,
            'passed': self.passed,
            'failed': self.failed,
            'pass_rate': (self.passed/(self.passed+self.failed)*100),
            'total_time': total_time,
            'test_results': test_results
        }


if __name__ == "__main__":
    tester = IntegrationTester(API_BASE_URL)
    results = tester.run_all_tests()
    
    # Save results to file
    with open('integration_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: integration_test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results['failed'] == 0 else 1)