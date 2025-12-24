from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from .models import ChatSessions, ChatMessages
from . import db
from .chatbot_service import ChatbotService
from .intent_classifier import ConversationEngine
from .genai_analyzer import GeminiAnalyzer

chat_message = Blueprint('chat_message', __name__)

chatbot_service = ChatbotService(model_path="app/model/")
conversation_engine = ConversationEngine()
gemini_analyzer = GeminiAnalyzer()

@chat_message.route('/<int:session_id>/read')
@login_required
def read_messages(session_id):
    session = ChatSessions.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()

    messages = ChatMessages.query.filter_by(session_id=session.id).order_by(ChatMessages.created_at).all()

    messages_data = [{
        "id": msg.id,
        "sender": msg.sender,
        "content": msg.content,
        "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for msg in messages]

    return jsonify(messages_data)

# Send Message for both User and Bot
@chat_message.route('/<int:session_id>/send', methods=['POST'])
@login_required
def send_message(session_id):
    session = ChatSessions.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()

    content = request.form.get('message')
    sender = request.form.get('sender')

    user_msg = ChatMessages(
        session_id=session.id,
        sender=sender,
        content=content
    )
    
    db.session.add(user_msg)

    bot_reply = conversation_engine.respond(content)

    # Save bot message
    bot_msg = ChatMessages(
        session_id=session_id,
        sender="bot",
        content=bot_reply
    )
    db.session.add(bot_msg)
    db.session.commit()

    return jsonify({
        "user": content,
        "bot": bot_reply
    })

def generate_reply(text):
    text = text.lower()

    if "hello" in text:
        return "Hello! How can I help you?"
    elif "bye" in text:
        return "Goodbye! 👋"
    else:
        return "I understand. Tell me more."


@chat_message.route('/<int:session_id>/analyze', methods=['POST'])
@login_required
def analyze_conversation(session_id):
    """Analisis percakapan menggunakan IndoBERT + Gemini"""
    
    session = ChatSessions.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()

    # Ambil semua pesan user
    messages = ChatMessages.query.filter_by(
        session_id=session.id,
        sender="user"
    ).order_by(ChatMessages.created_at).all()

    if not messages:
        return jsonify({"error": "Belum ada percakapan"}), 400

    # Gabungkan semua pesan user
    conversation_text = "\n".join([msg.content for msg in messages])

    # 1. Analisis dengan IndoBERT (attachment style prediction)
    bert_result = chatbot_service.predict(conversation_text)

    # 2. Extract frasa kunci dari semua pesan
    all_phrases = []
    phrase_scores = {}
    
    for msg in messages:
        clean_text = chatbot_service.preprocess_text(msg.content)
        phrases = chatbot_service.extract_phrases(clean_text)
        all_phrases.extend(phrases)
        
        # Hitung frekuensi frasa
        for phrase in phrases:
            phrase_scores[phrase] = phrase_scores.get(phrase, 0) + 1

    # Sort frasa by frequency
    sorted_phrases = sorted(
        phrase_scores.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:20]

    # 3. Buat rule-based scores dari probabilities
    rule_scores = {
        "secure": bert_result["probabilities"].get("secure", 0),
        "anxious": bert_result["probabilities"].get("anxious", 0),
        "avoidant": bert_result["probabilities"].get("avoidant", 0)
    }

    # 4. Generate summary dengan Gemini
    key_phrases_text = [phrase for phrase, _ in sorted_phrases]
    
    summary = gemini_analyzer.summarize_conversation(
        conversation_text=conversation_text,
        key_phrases=key_phrases_text,
        rule_scores=rule_scores
    )

    # 5. Update session status
    session.status = 'analyzed'
    db.session.commit()

    return jsonify({
        "attachment_style": bert_result["prediction"],
        "confidence": bert_result["confidence"],
        "probabilities": bert_result["probabilities"],
        "key_phrases": [
            {"phrase": phrase, "score": score} 
            for phrase, score in sorted_phrases
        ],
        "rule_scores": rule_scores,
        "summary": summary,
        "total_messages": len(messages)
    })


@chat_message.route('/<int:session_id>/explain-phrase', methods=['POST'])
@login_required
def explain_phrase(session_id):
    """Jelaskan frasa tertentu dengan Gemini"""
    
    session = ChatSessions.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()

    phrase = request.json.get('phrase')
    if not phrase:
        return jsonify({"error": "Phrase required"}), 400

    # Ambil konteks percakapan
    messages = ChatMessages.query.filter_by(
        session_id=session.id,
        sender="user"
    ).order_by(ChatMessages.created_at).all()

    context = "\n".join([msg.content for msg in messages])
    
    # Predict attachment style
    bert_result = chatbot_service.predict(context)
    attachment_style = bert_result["prediction"]

    # Explain dengan Gemini
    explanation = gemini_analyzer.explain_phrase(
        phrase=phrase,
        context=context,
        attachment_style=attachment_style
    )

    return jsonify({
        "phrase": phrase,
        "attachment_style": attachment_style,
        "explanation": explanation
    })