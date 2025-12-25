from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from .models import ChatSessions, ChatMessages, SessionAnalysis
from . import db
from .chatbot_service import ChatbotService
from .intent_classifier import ConversationEngine
from .genai_analyzer import GeminiAnalyzer
import json


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


@chat_message.route('/<int:session_id>/analyze', methods=['POST'])
@login_required
def analyze_conversation(session_id):
    
    session = ChatSessions.query.filter_by(
        id=session_id,
        user_id=current_user.id
    ).first_or_404()


    existing_analysis = SessionAnalysis.query.filter_by(session_id=session_id).first()
    
    if existing_analysis:
        # Return cached analysis!
        print(f"[INFO] Returning cached analysis for session {session_id}")
        return jsonify({
            "cached": True,
            "analyzed_at": existing_analysis.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "attachment_style": {
                "prediction": existing_analysis.attachment_style,
                "confidence": round(existing_analysis.confidence * 100, 1),
                "probabilities": json.loads(existing_analysis.probabilities)
            },
            "phrase_analysis": json.loads(existing_analysis.phrase_analysis),
            "emotion_analysis": json.loads(existing_analysis.emotion_analysis),
            "bert_features": json.loads(existing_analysis.bert_features),
            "text_statistics": json.loads(existing_analysis.text_statistics),
            "timeline": json.loads(existing_analysis.timeline_data),
            "ai_insights": existing_analysis.ai_insights,
            "rule_scores": json.loads(existing_analysis.rule_scores)
        })

    # ===== IF NOT ANALYZED YET, RUN ANALYSIS =====
    print(f"[INFO] Running fresh analysis for session {session_id}")

    # Get all user messages
    messages = ChatMessages.query.filter_by(
        session_id=session.id,
        sender="user"
    ).order_by(ChatMessages.created_at).all()

    if not messages:
        return jsonify({"error": "Belum ada percakapan untuk dianalisis"}), 400

    if len(messages) < 5:
        return jsonify({
            "error": "Percakapan terlalu singkat. Minimal 5 pesan untuk analisis yang akurat."
        }), 400

    # ===== 1. PREPARE FULL CONVERSATION TEXT =====
    conversation_text = "\n".join([msg.content for msg in messages])

    # ===== 2. RUN MAIN MODEL PREDICTION (IndoBERT + All Features) =====
    try:
        bert_result = chatbot_service.predict(conversation_text)
        
        if "error" in bert_result:
            return jsonify({
                "error": f"Model prediction failed: {bert_result['error']}"
            }), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

    # ===== 3. EXTRACT & SCORE PHRASES FROM INDIVIDUAL MESSAGES =====
    all_phrases = []
    phrase_frequency = {}
    message_details = []
    
    for msg in messages:
        clean_text = chatbot_service.preprocess_text(msg.content)
        phrases = chatbot_service.extract_phrases(clean_text)
        
        for phrase in phrases:
            phrase_frequency[phrase] = phrase_frequency.get(phrase, 0) + 1
            all_phrases.append(phrase)
        
        msg_phrases_with_scores = []
        if phrases and bert_result.get("phrase_scores"):
            for phrase in phrases:
                score = bert_result["phrase_scores"].get(phrase, 0)
                if score > 0:
                    msg_phrases_with_scores.append({
                        "phrase": phrase,
                        "score": round(score, 3)
                    })
        
        message_details.append({
            "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
            "timestamp": msg.created_at.strftime("%H:%M"),
            "word_count": len(msg.content.split()),
            "phrases": msg_phrases_with_scores[:3]
        })

    top_phrases = sorted(
        phrase_frequency.items(),
        key=lambda x: x[1],
        reverse=True
    )[:20]

    phrases_with_full_data = []
    for phrase, freq in top_phrases:
        tfidf_score = bert_result.get("phrase_scores", {}).get(phrase, 0)
        phrases_with_full_data.append({
            "phrase": phrase,
            "frequency": freq,
            "percentage": round((freq / len(messages)) * 100, 1),
            "tfidf_score": round(tfidf_score, 3) if tfidf_score > 0 else None,
            "importance": "high" if freq >= 3 else "medium" if freq >= 2 else "low"
        })

    # ===== 4. EMOTION ANALYSIS =====
    emotion_data = {
        "scores": bert_result.get("emotion_scores", {}),
        "dominant": None
    }
    
    if emotion_data["scores"]:
        dominant_emotion = max(
            emotion_data["scores"].items(),
            key=lambda x: x[1]
        )
        emotion_data["dominant"] = {
            "name": dominant_emotion[0],
            "score": round(dominant_emotion[1], 3)
        }

    # ===== 5. BERT FEATURES =====
    bert_features_data = bert_result.get("bert_summary", {})
    bert_features = {
        "embedding_dimension": bert_features_data.get("embedding_dim", 768),
        "statistics": {
            "mean": round(bert_features_data.get("embedding_mean", 0), 4),
            "std": round(bert_features_data.get("embedding_std", 0), 4),
            "max": round(bert_features_data.get("embedding_max", 0), 4),
            "min": round(bert_features_data.get("embedding_min", 0), 4)
        }
    }

    # ===== 6. TEXT STATISTICS =====
    text_stats = bert_result.get("text_stats", {})
    text_statistics = {
        "total_messages": len(messages),
        "avg_message_length": round(
            sum(len(m.content.split()) for m in messages) / len(messages), 1
        ),
        "word_count": text_stats.get("word_count", 0),
        "sentence_count": text_stats.get("sentence_count", 0),
        "clean_text_length": text_stats.get("clean_text_length", 0)
    }

    # ===== 7. GENERATE AI INSIGHTS WITH GEMINI =====
    rule_scores = {
        "secure": bert_result["probabilities"].get("secure", 0),
        "anxious": bert_result["probabilities"].get("anxious", 0),
        "avoidant": bert_result["probabilities"].get("avoidant", 0)
    }
    
    key_phrases_for_gemini = [p["phrase"] for p in phrases_with_full_data[:15]]
    
    try:
        gemini_summary = gemini_analyzer.summarize_conversation(
            conversation_text=conversation_text,
            key_phrases=key_phrases_for_gemini,
            rule_scores=rule_scores
        )
    except Exception as e:
        gemini_summary = f"Gagal generate AI insights: {str(e)}"

    # ===== 8. SAVE TO DATABASE =====
    phrase_analysis_data = {
        "top_phrases": phrases_with_full_data,
        "total_unique_phrases": len(phrase_frequency),
        "total_phrases_extracted": len(all_phrases)
    }
    
    probabilities_data = {
        k: round(v * 100, 1) 
        for k, v in bert_result["probabilities"].items()
    }
    
    rule_scores_data = {
        k: round(v * 100, 1)
        for k, v in rule_scores.items()
    }
    
    new_analysis = SessionAnalysis(
        session_id=session_id,
        attachment_style=bert_result["prediction"],
        confidence=bert_result["confidence"],
        probabilities=json.dumps(probabilities_data),
        phrase_analysis=json.dumps(phrase_analysis_data),
        emotion_analysis=json.dumps(emotion_data),
        bert_features=json.dumps(bert_features),
        text_statistics=json.dumps(text_statistics),
        timeline_data=json.dumps(message_details),
        ai_insights=gemini_summary,
        rule_scores=json.dumps(rule_scores_data)
    )
    
    db.session.add(new_analysis)
    session.status = 'analyzed'
    db.session.commit()
    
    print(f"[SUCCESS] Analysis saved for session {session_id}")

    return jsonify({
        "cached": False,
        "attachment_style": {
            "prediction": bert_result["prediction"],
            "confidence": round(bert_result["confidence"] * 100, 1),
            "probabilities": probabilities_data
        },
        "phrase_analysis": phrase_analysis_data,
        "emotion_analysis": emotion_data,
        "bert_features": bert_features,
        "text_statistics": text_statistics,
        "timeline": message_details,
        "ai_insights": gemini_summary,
        "rule_scores": rule_scores_data
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