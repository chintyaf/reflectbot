const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const chatMessages = document.getElementById("chatMessages");

chatInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = this.scrollHeight + "px";
});

function sendMessage() {
    const message = chatInput.innerText.trim();
    if (!message) return;

    console.log(message);

    const userMessage = document.createElement("div");
    userMessage.className = "chat-text chat-user";
    userMessage.innerHTML = `
        <span class="chat-bubble">
            ${message.replace(/\n/g, "<br>")}
        </span>
        <img height="40" src="${USER_IMG}" alt="user_profile.png" />
    `;

    chatMessages.appendChild(userMessage);

    // Clear contenteditable <p>
    chatInput.textContent = "";
    scrollToBottom();
}

function receiveMessage(bot_message){
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
    if (e.key === "Enter"  && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}


