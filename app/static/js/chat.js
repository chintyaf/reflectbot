const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const chatMessages = document.getElementById("chatMessages");

chatInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = this.scrollHeight + "px";
});

function loadMessages() {
    console.log("load messages");
    fetch(`/chat/${SESSION_ID}/read`)
        .then((res) => res.json())
        .then((messages) => {
            chatMessages.innerHTML = "";

            messages.forEach((msg) => {
                appendMessage(msg.sender, msg.content);
            });

            scrollToBottom();
        })
        .catch((err) => console.error(err));
}

function sendMessage() {
    const message = chatInput.innerText.trim();
    if (!message) return;

    // Send message langsung ke frontend
    appendMessage("user", message);

    console.log("send");
    fetch(`/chat/${SESSION_ID}/send`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            // "X-CSRFToken": CSRF_TOKEN // jika pakai Flask-WTF
        },
        body: new URLSearchParams({
            sender: "user",
            message: message,
        }),
    })
        .then((response) => {
            if (!response.ok) throw new Error("Failed to send message");
            return response.json();
        })
        .then((data) => {
            console.log("Saved message:", data);
            loadMessages();
            chatInput.textContent = "";
            scrollToBottom();
        })
        .catch((error) => {
            console.error("Error:", error);
            alert("Message failed to send");
        });
}

function receiveMessage(bot_message) {
    const botMessage = document.createElement("div");
    botMessage.className = "chat-text chat-user";
    botMessage.innerHTML = `
        <img height="40" src="${USER_IMG}" alt="user_profile.png" />
        <span class="chat-bubble">
                ${bot_message}
        </span>
    `;

    chatMessages.appendChild(botMessage);
    chatInput.value = "";

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight + 200;
}

function appendMessage(sender, text) {
    const div = document.createElement("div");

    div.className =
        sender === "user"
            ? "chat-text chat-user"
            : "chat-text chat-bot";

    if (sender === "user") {
        div.innerHTML = `
        <span class="chat-bubble">
            ${text.replace(/\n/g, "<br>")}
        </span>
        <img height="40" src="${USER_IMG}" alt="user_profile.png" />
        `;
    } else {
        div.innerHTML = `
        <img height="40" src="${BOT_IMG}" alt="user_profile.png" />
        <span class="chat-bubble">
            ${text.replace(/\n/g, "<br>")}
        </span>

    `;
    }
    chatMessages.appendChild(div);
}



function analyzeConversation() {
    const analyzeBtn = document.getElementById("analyzeBtn");
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Menganalisis...";
    fetch(`/chat/${SESSION_ID}/analyze`, {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
    },
})
.then(async (res) => {
    const text = await res.text();
    console.log("RAW RESPONSE:", text);

    if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${text}`);
    }

    return JSON.parse(text);
})
.then((data) => {
    displayAnalysisResult(data);
})
.catch((err) => {
    console.error("FETCH ERROR:", err);
    alert("Gagal menganalisis. Cek console.");
})
.finally(() => {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analisis Percakapan";
});
}
function openModal() {
    const modal = document.getElementById("analysisModal");
    if (!modal) {
        console.warn("Modal not found");
        return;
    }
    modal.style.display = "flex";
}

function closeModal() {
    const modal = document.getElementById("analysisModal");
    if (modal) modal.style.display = "none";
}

function displayAnalysisResult(data) {
    const modalContent = document.getElementById("analysisContent");

     const style = data.attachment_style.prediction;
    const confidence = data.attachment_style.confidence;
    
  
    // Probabilities bars
    const probBars = Object.entries(data.attachment_style.probabilities)
        .map(([s, p]) => {
            const c = '#555';
            return `
                <div class="prob-bar">
                    <span class="prob-label">${s}</span>
                    <div class="prob-track">
                        <div class="prob-fill" style="width: ${p}%; background: ${c};"></div>
                    </div>
                    <span class="prob-value">${p}%</span>
                </div>
            `;
        }).join('');
    
    // Top phrases table
    const phrasesTable = data.phrase_analysis.top_phrases
        .slice(0, 15)
        .map((p, idx) => {
            
            return `
                <tr>
                    <td>${idx + 1}</td>
                    <td><strong>${p.phrase}</strong></td>
                    <td>${p.frequency}x</td>
                    <td>${p.percentage}%</td>
                    <td>${p.tfidf_score !== null ? p.tfidf_score.toFixed(3) : '-'}</td>
                    <td><span class="importance-badge">${p.importance}</span></td>
                </tr>
            `;
        }).join('');
    
    // Emotions (if available)
    let emotionsHtml = '';
    if (data.emotion_analysis.scores && Object.keys(data.emotion_analysis.scores).length > 0) {
        const emotionBars = Object.entries(data.emotion_analysis.scores)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8)
            .map(([emotion, score]) => `
                <div class="emotion-bar">
                    <span class="emotion-label">${emotion}</span>
                    <div class="emotion-track">
                        <div class="emotion-fill" style="width: ${score * 100}%;"></div>
                    </div>
                    <span class="emotion-value">${(score * 100).toFixed(1)}%</span>
                </div>
            `).join('');
        
        emotionsHtml = `
            <div class="section">
                <h3>Analisis Emosi</h3>
                ${data.emotion_analysis.dominant ? `
                    <div class="dominant-emotion">
                        <strong>Emosi Dominan:</strong> ${data.emotion_analysis.dominant.name} 
                        (${(data.emotion_analysis.dominant.score * 100).toFixed(1)}%)
                    </div>
                ` : ''}
                <div class="emotions-container">
                    ${emotionBars}
                </div>
            </div>
        `;
    }
    
    // BERT features
    const bertStats = data.bert_features.statistics;
    const bertHtml = `
        <div class="bert-stats">
            <div class="bert-stat">
                <span class="label">Dimensi</span>
                <span class="value">${data.bert_features.embedding_dimension}</span>
            </div>
            <div class="bert-stat">
                <span class="label">Mean</span>
                <span class="value">${bertStats.mean}</span>
            </div>
            <div class="bert-stat">
                <span class="label">Std Dev</span>
                <span class="value">${bertStats.std}</span>
            </div>
            <div class="bert-stat">
                <span class="label">Range</span>
                <span class="value">${bertStats.min} → ${bertStats.max}</span>
            </div>
        </div>
    `;
    
    // Timeline
    const timelineHtml = data.timeline
        .map((msg) => `
            <div class="timeline-item">
                <div class="timeline-content">
                    <div class="timeline-time">${msg.timestamp}</div>
                    <div class="timeline-text">${msg.content}</div>
                    <div class="timeline-meta">
                        <span>${msg.word_count} kata</span>
                        ${msg.phrases.length > 0 ? `
                            <span class="timeline-phrases">
                                ${msg.phrases.map(p => `${p.phrase} (${p.score})`).join(', ')}
                            </span>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    
    modalContent.innerHTML = `
        <div class="analysis-results">
            ${data.cached ? `
                <div class="cache-notice">
                    Hasil tersimpan dari analisis sebelumnya (${data.analyzed_at})
                </div>
            ` : ''}
            
            <!-- Main Result -->
            <div class="section hero-section">
                <div class="main-result">
                    <h2>Attachment Style Anda</h2>
                    <div class="style-badge">
                        ${style.toUpperCase()}
                    </div>
                    <p class="confidence">Confidence: ${confidence}%</p>
                </div>
            </div>
            
            <!-- Probabilities -->
            <div class="section">
                <h3>Distribusi Probabilitas</h3>
                <div class="probabilities-container">
                    ${probBars}
                </div>
            </div>
            
            <!-- Phrase Analysis (MOST IMPORTANT!) -->
            <div class="section highlight-section">
                <h3>Analisis Frasa Kunci (TF-IDF + Frequency)</h3>
                <div class="stats-row">
                    <div class="stat-box">
                        <div class="stat-value">${data.phrase_analysis.total_unique_phrases}</div>
                        <div class="stat-label">Frasa Unik</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${data.phrase_analysis.total_phrases_extracted}</div>
                        <div class="stat-label">Total Ekstraksi</div>
                    </div>
                </div>
                <table class="phrases-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Frasa</th>
                            <th>Frekuensi</th>
                            <th>%</th>
                            <th>TF-IDF Score</th>
                            <th>Importance</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${phrasesTable}
                    </tbody>
                </table>
            </div>
            
            ${emotionsHtml}
            
            <!-- BERT Features -->
            <div class="section">
                <h3>IndoBERT Embedding Analysis</h3>
                <p class="section-desc">Representasi semantik dari percakapan Anda menggunakan IndoBERT</p>
                ${bertHtml}
            </div>
            
            <!-- Text Statistics -->
            <div class="section">
                <h3>Statistik Teks</h3>
                <div class="stats-row">
                    <div class="stat-box">
                        <div class="stat-value">${data.text_statistics.total_messages}</div>
                        <div class="stat-label">Total Pesan</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${data.text_statistics.avg_message_length}</div>
                        <div class="stat-label">Rata-rata Kata/Pesan</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${data.text_statistics.word_count}</div>
                        <div class="stat-label">Total Kata</div>
                    </div>
                </div>
            </div>
            
            <!-- Timeline -->
            <div class="section">
                <h3>Timeline Percakapan</h3>
                <div class="timeline-container">
                    ${timelineHtml}
                </div>
            </div>
            
           
        </div>
    `;

    openModal(); 
}

document.addEventListener("DOMContentLoaded", () => {
    loadMessages();
});