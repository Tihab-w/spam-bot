"""
Spam Classifier AI - Flask Application
SRS Section: 4.2 (API-first approach), 5.1 (Simple Interface)
Provides both Web UI and REST API endpoints
"""

from flask import Flask, render_template, request, jsonify
from model import SpamClassifier
import os
import json
from datetime import datetime

app = Flask(__name__)
classifier = SpamClassifier()

def initialize_model():
    """Initialize the AI model at server startup"""
    print("\n" + "=" * 60)
    print("SPAM CLASSIFIER AI - INITIALIZATION")
    print("=" * 60)
    
    if os.path.exists("spam_model.joblib"):
        print("\n[INFO] Loading pre-trained model...")
        if classifier.load_model():
            print("[SUCCESS] Model loaded successfully!")
            return True
    
    print("\n[INFO] No pre-trained model found. Training new model...")
    metrics = classifier.train()
    print(f"\n[SUCCESS] Model trained with accuracy: {metrics['accuracy']:.2%}")
    return True

@app.route("/", methods=["GET", "POST"])
def home():
    """Main web interface"""
    result_data = None
    
    if request.method == "POST":
        message = request.form.get("message", "")
        
        if message and message.strip():
            prediction = classifier.predict(message)
            top_words = classifier.get_feature_importance(message, top_n=5)
            
            result_data = {
                'message': message[:100] + ('...' if len(message) > 100 else ''),
                'result': prediction['result'],
                'confidence': prediction['confidence'],
                'explanation': prediction['explanation'],
                'top_words': top_words,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            print(f"[{result_data['timestamp']}] Classified as {prediction['result']} "
                  f"(Confidence: {prediction['confidence']}%)")
    
    return render_template("index.html", result=result_data)

@app.route("/about")
def about():
    return jsonify({
        'name': 'Spam Classifier AI',
        'version': '1.0.0',
        'model': 'Naive Bayes',
        'status': 'running'
    })

@app.route("/api/classify", methods=["POST"])
def api_classify():
    """REST API Endpoint for classification"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'No message provided',
                'code': 'MISSING_MESSAGE'
            }), 400
        
        message = data['message']
        return_details = data.get('return_details', True)
        prediction = classifier.predict(message)
        
        response = {
            'success': True,
            'result': str(prediction['result']),
            'confidence': float(prediction['confidence']),
            'timestamp': str(datetime.now().isoformat())
        }
        
        if return_details:
            response['explanation'] = str(prediction.get('explanation', ''))
            response['raw_score'] = float(prediction.get('raw_score', 0.0))
            
            top_indicators = classifier.get_feature_importance(message, top_n=5)
            serializable_indicators = []
            for indicator in top_indicators:
                serializable_indicators.append({
                    'word': str(indicator.get('word', '')),
                    'importance': float(indicator.get('importance', 0.0)),
                    'indicates_spam': bool(indicator.get('indicates_spam', False))
                })
            response['top_indicators'] = serializable_indicators
        
        return jsonify(response), 200
    
    except Exception as e:
        import traceback
        print(f"API Error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route("/api/batch-classify", methods=["POST"])
def api_batch_classify():
    """Batch Classification Endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'messages' not in data:
            return jsonify({
                'success': False,
                'error': 'No messages provided',
                'code': 'MISSING_MESSAGES'
            }), 400
        
        messages = data['messages']
        
        if not isinstance(messages, list):
            return jsonify({
                'success': False,
                'error': 'Messages must be a list',
                'code': 'INVALID_FORMAT'
            }), 400
        
        results = []
        for msg in messages:
            prediction = classifier.predict(msg)
            results.append({
                'message': str(msg[:50] + ('...' if len(msg) > 50 else '')),
                'result': str(prediction['result']),
                'confidence': float(prediction['confidence'])
            })
        
        spam_count = sum(1 for r in results if r['result'] == 'SPAM')
        ham_count = sum(1 for r in results if r['result'] == 'HAM')
        
        return jsonify({
            'success': True,
            'total_messages': int(len(messages)),
            'spam_count': int(spam_count),
            'ham_count': int(ham_count),
            'results': results
        }), 200
    
    except Exception as e:
        import traceback
        print(f"Batch API Error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': True if classifier.is_trained else False,
        'timestamp': str(datetime.now().isoformat()),
        'version': '1.0.0'
    }), 200

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data or 'correct_label' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        feedback_entry = {
            'message': str(data['message']),
            'predicted': str(data.get('predicted_label', 'unknown')),
            'correct': str(data['correct_label']),
            'timestamp': str(datetime.now().isoformat())
        }
        
        with open('feedback_log.json', 'a') as f:
            f.write(json.dumps(feedback_entry) + '\n')
        
        return jsonify({
            'success': True,
            'message': 'Feedback recorded. Thank you!'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'code': 'NOT_FOUND'
    }), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500

if __name__ == "__main__":
    import os
    
    print("\n" + "=" * 60)
    print("SPAM CLASSIFIER AI - PRODUCTION SERVER")
    print("=" * 60)
    
    initialize_model()
    
    print("\n" + "=" * 60)
    print("AVAILABLE ENDPOINTS:")
    print("=" * 60)
    print("Web Interface: http://127.0.0.1:5000/")
    print("POST /api/classify")
    print("POST /api/batch-classify")
    print("POST /api/feedback")
    print("GET  /api/health")
    print("=" * 60)
    
    # Use PORT from environment (for Render), default to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)