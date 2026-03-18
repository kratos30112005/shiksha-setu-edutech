/* =========================================================
   ShikshaSetu - Main Frontend JavaScript
   Handles: AI Tutor, Quiz, Navigation, Toast Notifications
   ========================================================= */

// ---- Toast Notification System ----
let toastContainer = null;

function ensureToastContainer() {
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }
}

function showToast(message, type = 'info', duration = 3500) {
  ensureToastContainer();
  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || '💬'}</span><span>${message}</span>`;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'fadeIn 0.3s reverse both';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ---- PDF Upload Utility ----
async function uploadPDF(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  if (onProgress) onProgress('Uploading PDF...');

  try {
    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await res.json();

    if (data.error) {
      showToast(data.error, 'error');
      return null;
    }

    showToast(`✅ PDF uploaded! (${data.word_count || '?'} words extracted)`, 'success');
    if (onProgress) onProgress(null);
    return data;

  } catch (err) {
    showToast('Upload failed. Is the server running?', 'error');
    if (onProgress) onProgress(null);
    return null;
  }
}

// ---- AI Tutor Chat Logic ----

let isSending = false;

document.addEventListener('DOMContentLoaded', () => {

  // PDF Upload listener for AI Tutor
  const pdfInput = document.getElementById('pdfFile');
  if (pdfInput) {
    pdfInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const uploadLabel = document.getElementById('upload-status');
      const result = await uploadPDF(file, (msg) => {
        if (uploadLabel) uploadLabel.textContent = msg || `📚 ${file.name} loaded`;
      });

      if (result && uploadLabel) {
        uploadLabel.textContent = `📚 ${file.name} — Ready to chat!`;
        uploadLabel.style.color = '#34D399';
      }
    });
  }

  // Chat input Enter key
  const chatInput = document.getElementById('userInput');
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  // Load user info on pages that need it
  loadUserInfo();
});

// ---- Load User Info ----
async function loadUserInfo() {
  try {
    const res = await fetch('/api/user');
    const data = await res.json();

    const nameEl = document.getElementById('user-name');
    if (nameEl) nameEl.textContent = data.user || 'Student';

    const welcomeEl = document.getElementById('welcome-msg');
    if (welcomeEl) welcomeEl.textContent = `Namaste, ${data.user || 'Student'}! 👋`;

    const cogEl = document.getElementById('cognitive-score');
    if (cogEl) cogEl.textContent = data.cognitive_score || 50;

    const accEl = document.getElementById('avg-accuracy');
    if (accEl) accEl.textContent = (data.average_accuracy || 0).toFixed(1) + '%';

    const attEl = document.getElementById('total-attempts');
    if (attEl) attEl.textContent = data.total_attempts || 0;

    return data;
  } catch (err) {
    return null;
  }
}

// ---- Send Chat Message ----
async function sendMessage() {
  if (isSending) return;

  const input = document.getElementById('userInput');
  const chatBox = document.getElementById('chatBox');

  if (!input || !chatBox) return;

  const text = input.value.trim();
  if (!text) {
    showToast('Please type a message first!', 'warning');
    return;
  }

  isSending = true;
  input.disabled = true;
  appendMessage(chatBox, text, 'user');
  input.value = '';

  const thinkingId = 'think-' + Date.now();
  appendThinking(chatBox, thinkingId);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });

    if (!res.ok) throw new Error('API error');
    const data = await res.json();

    const bubble = document.getElementById(thinkingId);
    if (bubble) {
      bubble.innerHTML = formatMarkdown(data.reply || 'No response');
      bubble.classList.remove('thinking');
    }

  } catch (err) {
    const bubble = document.getElementById(thinkingId);
    if (bubble) bubble.innerHTML = '❌ Server not reachable. Make sure the backend is running!';
    showToast('Connection error', 'error');
  }

  chatBox.scrollTop = chatBox.scrollHeight;
  isSending = false;
  input.disabled = false;
  input.focus();
}

// ---- Append Message ----
function appendMessage(container, text, sender) {
  const div = document.createElement('div');
  div.className = `msg msg-${sender}`;
  div.innerHTML = sender === 'user' ? escapeHtml(text) : formatMarkdown(text);
  container.appendChild(div);
  container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
  return div;
}

// ---- Thinking Bubble ----
function appendThinking(container, id) {
  const div = document.createElement('div');
  div.className = 'msg msg-ai thinking';
  div.id = id;
  div.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
  container.appendChild(div);
  container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
}

// ---- Quick Ask ----
function quickAsk(text) {
  const input = document.getElementById('userInput');
  if (input) {
    input.value = text;
    sendMessage();
  }
}

// ---- Format Markdown (Basic) ----
function formatMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/^#{1,3} (.*$)/gm, '<h4>$1</h4>')
    .replace(/^• (.*$)/gm, '<li>$1</li>')
    .replace(/^- (.*$)/gm, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}

// ---- Escape HTML ----
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ---- Voice Input ----
function startVoice() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    showToast('Voice input not supported in this browser.', 'warning');
    return;
  }
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SpeechRecognition();
  rec.lang = 'en-IN';
  rec.start();
  showToast('🎤 Listening...', 'info', 2000);
  rec.onresult = (e) => {
    const text = e.results[0][0].transcript;
    const input = document.getElementById('userInput');
    if (input) input.value = text;
    sendMessage();
  };
  rec.onerror = () => showToast('Voice input failed.', 'error');
}
