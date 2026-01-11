from flask import Blueprint, request, jsonify
from ..genai_analyzer import GeminiAnalyzer
from ..chatbot_service import ChatbotService
import os
from dotenv import load_dotenv

load_dotenv()

api = Blueprint('api', __name__)

# Initialize services
# gemini_analyzer = GeminiAnalyzer()
# chatbot_service = ChatbotService()

def get_gemini_analyzer():
    """Lazy loading of GeminiAnalyzer"""
    if not hasattr(get_gemini_analyzer, '_instance'):
        get_gemini_analyzer._instance = GeminiAnalyzer()
    return get_gemini_analyzer._instance

def get_chatbot_service():
    """Lazy loading of ChatbotService"""
    if not hasattr(get_chatbot_service, '_instance'):
        get_chatbot_service._instance = ChatbotService()
    return get_chatbot_service._instance

@api.route('/explain_phrase', methods=['POST'])
def explain_phrase():
    """API endpoint to explain a specific phrase in attachment theory context"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        phrase = data.get('phrase', '')
        context = data.get('context', '')
        attachment_style = data.get('attachment_style', 'unknown')

        if not phrase or not context:
            return jsonify({'error': 'Phrase and context are required'}), 400

        explanation = get_gemini_analyzer().explain_phrase(
            phrase=phrase,
            context=context,
            attachment_style=attachment_style
        )

        return jsonify({
            'phrase': phrase,
            'explanation': explanation,
            'attachment_style': attachment_style
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/analyze_conversation', methods=['POST'])
def analyze_conversation():
    """API endpoint to analyze full conversation"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        conversation_text = data.get('conversation_text', '')

        if not conversation_text:
            return jsonify({'error': 'Conversation text is required'}), 400

        # Get ML prediction
        prediction_result = get_chatbot_service().predict(conversation_text)

        # Get AI summary
        key_phrases = get_chatbot_service().extract_phrases(
            get_chatbot_service().preprocess_text(conversation_text)
        )

        rule_scores = {
            'secure': prediction_result.get('rule_scores', {}).get('secure', 0),
            'anxious': prediction_result.get('rule_scores', {}).get('anxious', 0),
            'avoidant': prediction_result.get('rule_scores', {}).get('avoidant', 0)
        }

        summary = get_gemini_analyzer().summarize_conversation(
            conversation_text=conversation_text,
            key_phrases=key_phrases,
            rule_scores=rule_scores
        )

        return jsonify({
            'prediction': prediction_result,
            'summary': summary,
            'key_phrases': key_phrases[:10]  # Limit to top 10
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500