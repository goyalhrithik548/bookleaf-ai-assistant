const chatLog = document.getElementById("chatLog");
const chatForm = document.getElementById("chatForm");
const emailInput = document.getElementById("emailInput");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const loadingIndicator = document.getElementById("loadingIndicator");

const apiBase = window.location.protocol.startsWith("http")
    ? window.location.origin
    : "http://127.0.0.1:8000";

const sessionId = getOrCreateSessionId();

function getOrCreateSessionId() {
    const existingSessionId = localStorage.getItem("bookleaf_session_id");

    if (existingSessionId) {
        return existingSessionId;
    }

    const newSessionId = window.crypto && crypto.randomUUID
        ? crypto.randomUUID()
        : `session-${Date.now()}`;

    localStorage.setItem("bookleaf_session_id", newSessionId);

    return newSessionId;
}

function renderEmptyState() {
    if (chatLog.children.length > 0) {
        return;
    }

    const emptyState = document.createElement("div");
    emptyState.className = "empty-state";
    emptyState.textContent = "Start a conversation with the BookLeaf assistant.";
    chatLog.appendChild(emptyState);
}

function clearEmptyState() {
    const emptyState = chatLog.querySelector(".empty-state");

    if (emptyState) {
        emptyState.remove();
    }
}

function appendMessage(role, content) {
    clearEmptyState();

    const message = document.createElement("div");
    message.className = `message ${role}`;
    message.textContent = content;

    chatLog.appendChild(message);
    chatLog.scrollTop = chatLog.scrollHeight;
}

function setLoading(isLoading) {
    loadingIndicator.hidden = !isLoading;
    sendButton.disabled = isLoading;
    messageInput.disabled = isLoading;
}

async function loadHistory() {
    try {
        const response = await fetch(`${apiBase}/history/${sessionId}`);
        const data = await response.json();

        if (!data.success || !Array.isArray(data.history)) {
            renderEmptyState();
            return;
        }

        data.history.forEach((message) => {
            appendMessage(
                message.role === "user" ? "user" : "assistant",
                message.content
            );
        });

        renderEmptyState();

    } catch (error) {
        renderEmptyState();
    }
}

chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const query = messageInput.value.trim();

    if (!query) {
        return;
    }

    appendMessage("user", query);
    messageInput.value = "";
    setLoading(true);

    try {
        const response = await fetch(`${apiBase}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query,
                email: emailInput.value.trim() || null,
                session_id: sessionId
            })
        });

        const data = await response.json();

        if (data.success && data.response) {
            appendMessage("assistant", data.response);
        } else {
            appendMessage("assistant", data.message || "Unable to get a response.");
        }

    } catch (error) {
        appendMessage("assistant", "Could not connect to the backend.");

    } finally {
        setLoading(false);
        messageInput.focus();
    }
});

loadHistory();
