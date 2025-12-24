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

document.addEventListener("DOMContentLoaded", loadMessages);


function analyzeConversation() {
    const analyzeBtn = document.getElementById("analyzeBtn");
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "⏳ Menganalisis...";

    fetch(`/chat/${SESSION_ID}/analyze`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
    })
        .then((res) => res.json())
        .then((data) => {
            displayAnalysisResult(data);
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = "Analisis Percakapan";
        })
        .catch((err) => {
            console.error(err);
            alert("Gagal menganalisis");
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = "Analisis Percakapan";
        });
}

function displayAnalysisResult(data) {
    const resultDiv = document.getElementById("analysisResult");
    
    let phrasesHtml = data.key_phrases
        .slice(0, 10)
        .map(p => `<li><strong>${p.phrase}</strong> (${p.score}x)</li>`)
        .join("");

    resultDiv.innerHTML = `
        <div class="analysis-card">
            <h3>Hasil Analisis</h3>
            
            <div class="attachment-style">
                <h4>Attachment Style: ${data.attachment_style}</h4>
                <p>Confidence: ${(data.confidence * 100).toFixed(1)}%</p>
            </div>

            <div class="probabilities">
                <h4>Probabilitas:</h4>
                <ul>
                    ${Object.entries(data.probabilities)
                        .map(([k, v]) => `<li>${k}: ${(v * 100).toFixed(1)}%</li>`)
                        .join("")}
                </ul>
            </div>

            <div class="key-phrases">
                <h4>Frasa Kunci (dengan skor):</h4>
                <ul>${phrasesHtml}</ul>
            </div>

            <div class="summary">
                <h4>Ringkasan AI:</h4>
                <pre>${data.summary}</pre>
            </div>
        </div>
    `;
    
    resultDiv.style.display = "block";
    resultDiv.scrollIntoView({ behavior: "smooth" });
}