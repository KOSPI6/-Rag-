const chatMessages = document.getElementById('chatMessages');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const btnText = document.getElementById('btnText');
const btnLoader = document.getElementById('btnLoader');

// 添加欢迎消息
addBotMessage('你好！我是 RAG Agent 智能助手，有什么可以帮助你的吗？');

// 回车发送消息
questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const question = questionInput.value.trim();

    if (!question) {
        return;
    }

    // 添加用户消息
    addUserMessage(question);

    // 清空输入框
    questionInput.value = '';

    // 禁用发送按钮
    setLoading(true);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        if (data.success) {
            addBotMessage(data.answer);
        } else {
            addErrorMessage(data.error || '处理请求时出错');
        }

    } catch (error) {
        console.error('Error:', error);
        addErrorMessage('网络请求失败，请检查服务器是否正常运行');
    } finally {
        setLoading(false);
    }
}

function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-user';
    messageDiv.innerHTML = `
        <div class="message-content">${escapeHtml(text)}</div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message message-bot';
    messageDiv.innerHTML = `
        <div class="message-content">${escapeHtml(text)}</div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addErrorMessage(text) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = '❌ ' + text;
    chatMessages.appendChild(errorDiv);
    scrollToBottom();
}

function setLoading(isLoading) {
    sendBtn.disabled = isLoading;
    questionInput.disabled = isLoading;

    if (isLoading) {
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
    } else {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/\n/g, '<br>');
}
