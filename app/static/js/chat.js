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
                const div = document.createElement("div");

                div.className =
                    msg.sender === "user"
                        ? "chat-text chat-user"
                        : "chat-text chat-bot";

                if (msg.sender === "user") {
                    div.innerHTML = `
                    <span class="chat-bubble">
                        ${msg.content.replace(/\n/g, "<br>")}
                    </span>
                    <img height="40" src="${USER_IMG}" alt="user_profile.png" />
                    `;
                } else {
                    div.innerHTML = `
                    <img height="40" src="${BOT_IMG}" alt="user_profile.png" />
                    <span class="chat-bubble">
                        ${msg.content.replace(/\n/g, "<br>")}
                    </span>

                `;
                }
                chatMessages.appendChild(div);
            });

            scrollToBottom();
        })
        .catch((err) => console.error(err));
}

function sendMessage() {
    // const message = chatInput.innerText.trim();
    // if (!message) return;

    // console.log(message);

    // const userMessage = document.createElement("div");
    // userMessage.className = "chat-text chat-user";
    // userMessage.innerHTML = `
    //     <span class="chat-bubble">
    //         ${message.replace(/\n/g, "<br>")}
    //     </span>
    //     <img height="40" src="${USER_IMG}" alt="user_profile.png" />
    // `;

    // chatMessages.appendChild(userMessage);

    // // Clear contenteditable <p>
    // chatInput.textContent = "";
    // scrollToBottom();

    const message = chatInput.innerText.trim();
    if (!message) return;

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

            // kalau mau update timestamp / id, bisa di sini
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

document.addEventListener("DOMContentLoaded", loadMessages);
