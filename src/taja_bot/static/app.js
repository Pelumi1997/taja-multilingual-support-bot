const form = document.querySelector('#chat-form');
const input = document.querySelector('#message');
const messages = document.querySelector('#messages');
const errorBox = document.querySelector('#error');
const sessionId = window.crypto?.randomUUID?.() ?? `web-${Date.now()}-${Math.random()}`;

function addMessage(text, type, meta = '') {
  const bubble = document.createElement('div');
  bubble.className = `message ${type}`;
  bubble.textContent = text;
  if (meta) {
    const small = document.createElement('small');
    small.textContent = meta;
    bubble.appendChild(small);
  }
  messages.appendChild(bubble);
  messages.scrollTop = messages.scrollHeight;
}

async function sendMessage(message) {
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({session_id: sessionId, message, channel: 'web-demo'})
  });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  errorBox.textContent = '';
  const message = input.value.trim();
  if (!message) return;
  input.value = '';
  addMessage(message, 'user');
  input.disabled = true;
  try {
    const result = await sendMessage(message);
    const meta = result.requires_human
      ? `Human review · ${result.case_reference}`
      : result.matched_faq_id
        ? `FAQ: ${result.matched_faq_id} · ${result.answer_mode} · confidence ${Math.round(result.confidence * 100)}%`
        : '';
    addMessage(result.reply, 'bot', meta);
  } catch (error) {
    errorBox.textContent = error.message;
  } finally {
    input.disabled = false;
    input.focus();
  }
});

addMessage('Welcome. Type hello to choose a language, or ask a question directly.', 'bot');
