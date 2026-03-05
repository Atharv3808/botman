(function() {
  // Configuration
  const script = document.currentScript || document.querySelector('script[data-bot]');
  if (!script) {
    console.error('Botman Widget: Script tag must have data-bot attribute.');
    return;
  }
  
  const config = {
    botId: script.getAttribute('data-bot'),
    apiUrl: script.getAttribute('data-api-url') || 'http://localhost:8000/widget', // Default to local backend
    themeColor: script.getAttribute('data-color') || '#2563eb', // Default blue-600
  };

  // State
  let state = {
    isOpen: false,
    sessionToken: localStorage.getItem(`botman_session_${config.botId}`),
    messages: [],
    isTyping: false
  };

  // Styles
  const styles = `
    .botman-widget-container {
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 9999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    .botman-launcher {
      width: 60px;
      height: 60px;
      border-radius: 30px;
      background-color: ${config.themeColor};
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s;
    }
    
    .botman-launcher:hover {
      transform: scale(1.05);
    }
    
    .botman-launcher svg {
      width: 30px;
      height: 30px;
      fill: white;
    }
    
    .botman-window {
      position: absolute;
      bottom: 80px;
      right: 0;
      width: 350px;
      height: 500px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: opacity 0.2s, transform 0.2s;
      opacity: 0;
      transform: translateY(20px);
      pointer-events: none;
    }
    
    .botman-window.open {
      opacity: 1;
      transform: translateY(0);
      pointer-events: all;
    }
    
    .botman-header {
      background-color: ${config.themeColor};
      color: white;
      padding: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .botman-title {
      font-weight: 600;
      font-size: 16px;
    }
    
    .botman-close {
      cursor: pointer;
      opacity: 0.8;
    }
    
    .botman-close:hover {
      opacity: 1;
    }
    
    .botman-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background-color: #f9fafb;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    
    .botman-message {
      max-width: 80%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 14px;
      line-height: 1.5;
      word-wrap: break-word;
    }
    
    .botman-message.user {
      align-self: flex-end;
      background-color: ${config.themeColor};
      color: white;
      border-bottom-right-radius: 2px;
    }
    
    .botman-message.bot {
      align-self: flex-start;
      background-color: #e5e7eb;
      color: #1f2937;
      border-bottom-left-radius: 2px;
    }
    
    .botman-input-area {
      padding: 16px;
      border-top: 1px solid #e5e7eb;
      background: white;
      display: flex;
      gap: 10px;
    }
    
    .botman-input {
      flex: 1;
      border: 1px solid #d1d5db;
      border-radius: 20px;
      padding: 8px 16px;
      outline: none;
      font-size: 14px;
      resize: none;
      height: 40px; /* fixed height for now */
      line-height: 22px;
    }
    
    .botman-input:focus {
      border-color: ${config.themeColor};
    }
    
    .botman-send {
      background: none;
      border: none;
      cursor: pointer;
      color: ${config.themeColor};
      display: flex;
      align-items: center;
    }
    
    .botman-send:disabled {
      color: #9ca3af;
      cursor: not-allowed;
    }
    
    /* Typing Indicator */
    .typing-indicator {
      display: flex;
      gap: 4px;
      padding: 12px 14px; /* adjusted padding */
    }
    .typing-dot {
      width: 6px;
      height: 6px;
      background: #6b7280;
      border-radius: 50%;
      animation: typing 1.4s infinite ease-in-out both;
    }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }
  `;

  // Inject CSS
  const styleSheet = document.createElement("style");
  styleSheet.innerText = styles;
  document.head.appendChild(styleSheet);

  // DOM Elements
  const container = document.createElement('div');
  container.className = 'botman-widget-container';
  
  const launcher = document.createElement('div');
  launcher.className = 'botman-launcher';
  launcher.innerHTML = `
    <svg viewBox="0 0 24 24">
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
    </svg>
  `;
  
  const windowEl = document.createElement('div');
  windowEl.className = 'botman-window';
  windowEl.innerHTML = `
    <div class="botman-header">
      <div class="botman-title">Chat Support</div>
      <div class="botman-close">✕</div>
    </div>
    <div class="botman-messages"></div>
    <div class="botman-input-area">
      <textarea class="botman-input" placeholder="Type a message..."></textarea>
      <button class="botman-send">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
        </svg>
      </button>
    </div>
  `;
  
  container.appendChild(windowEl);
  container.appendChild(launcher);
  document.body.appendChild(container);

  // References
  const messagesEl = windowEl.querySelector('.botman-messages');
  const inputEl = windowEl.querySelector('.botman-input');
  const sendBtn = windowEl.querySelector('.botman-send');
  const closeBtn = windowEl.querySelector('.botman-close');
  const titleEl = windowEl.querySelector('.botman-title');

  // API Methods
  const api = {
    async initSession() {
      if (state.sessionToken) return; // Already have session
      
      try {
        const res = await fetch(`${config.apiUrl}/session/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bot_id: config.botId })
        });
        
        if (!res.ok) throw new Error('Failed to create session');
        
        const data = await res.json();
        state.sessionToken = data.session_token;
        localStorage.setItem(`botman_session_${config.botId}`, data.session_token);
      } catch (err) {
        console.error('Botman Widget Error:', err);
      }
    },
    
    async getConfig() {
      try {
        const res = await fetch(`${config.apiUrl}/config/${config.botId}/`);
        if (res.ok) {
          const data = await res.json();
          if (data.name) titleEl.innerText = data.name;
          if (data.initial_message && state.messages.length === 0) {
            appendMessage('bot', data.initial_message);
          }
        }
      } catch (err) {
        console.error('Botman Widget Config Error:', err);
      }
    },

    async sendMessage(text) {
      if (!state.sessionToken) await this.initSession();
      
      // Show typing indicator immediately
      const typingDiv = createTypingIndicator();

      try {
        const res = await fetch(`${config.apiUrl}/chat/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            session_token: state.sessionToken,
            message: text
          })
        });

        if (res.status === 401) {
          console.log('Session expired, refreshing...');
          state.sessionToken = null;
          localStorage.removeItem(`botman_session_${config.botId}`);
          await this.initSession();
          // Retry once
          const retryRes = await fetch(`${config.apiUrl}/chat/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_token: state.sessionToken, message: text })
          });
          if (!retryRes.ok) throw new Error('Failed to send message after refresh');
          await this.handleResponse(retryRes, typingDiv);
          return;
        }

        if (!res.ok) throw new Error('Failed to send message');
        
        await this.handleResponse(res, typingDiv);
        
      } catch (err) {
        console.error('Botman Chat Error:', err);
        if (typingDiv && typingDiv.parentNode) typingDiv.remove();
        appendMessage('bot', 'Sorry, something went wrong. Please try again.');
      }
    },

    async handleResponse(res, existingTypingDiv = null) {
        // Use existing typing indicator or create new one
        const typingDiv = existingTypingDiv || createTypingIndicator();
        if (!existingTypingDiv) scrollToBottom();

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let botMessageDiv = null;
        let currentText = '';
        let buffer = '';
        
        try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              
              const chunk = decoder.decode(value, { stream: true });
              buffer += chunk;
              
              // Process buffer for SSE events
              const parts = buffer.split('\n\n');
              // The last part might be incomplete, so keep it in buffer
              // If buffer ended with \n\n, the last element is empty string, which is correct
              buffer = parts.pop(); 
              
              for (const part of parts) {
                  const lines = part.split('\n');
                  let eventType = 'message';
                  let data = null;
                  
                  for (const line of lines) {
                      if (line.startsWith('event: ')) {
                          eventType = line.substring(7).trim();
                      } else if (line.startsWith('data: ')) {
                          const jsonStr = line.substring(6);
                          try {
                              data = JSON.parse(jsonStr);
                          } catch (e) {
                              console.error('Invalid JSON in SSE:', jsonStr);
                          }
                      }
                  }
                  
                  if (data) {
                      if (eventType === 'error') {
                          // Handle error
                          if (botMessageDiv) {
                              botMessageDiv.innerText += `\n[Error: ${data.message}]`;
                          } else {
                              // If we haven't started a message yet, replace typing indicator
                              if (typingDiv && typingDiv.parentNode) typingDiv.remove();
                              appendMessage('bot', `Error: ${data.message}`);
                              botMessageDiv = messagesEl.lastChild; // Set to the error message so we don't create another
                          }
                      } else {
                          // Normal message chunk
                          if (!botMessageDiv) {
                              // First chunk arrived, remove typing indicator and create message
                              if (typingDiv && typingDiv.parentNode) typingDiv.remove();
                              botMessageDiv = createMessageElement('bot', '');
                          }
                          
                          if (data.content) {
                              currentText += data.content;
                              botMessageDiv.innerText = currentText;
                              scrollToBottom();
                          }
                      }
                  }
              }
            }
        } catch (err) {
             console.error("Stream reading error:", err);
             // Cleanup typing if error
             if (typingDiv && typingDiv.parentNode) typingDiv.remove();
             // If we haven't started a message, show error
             if (!botMessageDiv) appendMessage('bot', "Network error occurred.");
        } finally {
             // Final cleanup if stream ends without removing typing (unlikely with above logic but safe)
             if (typingDiv && typingDiv.parentNode) typingDiv.remove();
             
             if (botMessageDiv) {
                 // Save to state
                 state.messages.push({ role: 'bot', content: currentText });
             }
        }
    }
  };

  // UI Methods
  function toggleWindow() {
    state.isOpen = !state.isOpen;
    if (state.isOpen) {
      windowEl.classList.add('open');
      launcher.innerHTML = `<svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>`; // Close icon
      setTimeout(() => inputEl.focus(), 100);
      
      // Initialize if needed
      if (!state.sessionToken) api.initSession();
    } else {
      windowEl.classList.remove('open');
      launcher.innerHTML = `<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>`; // Chat icon
    }
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function createMessageElement(role, text) {
    const div = document.createElement('div');
    div.className = `botman-message ${role}`;
    div.innerText = text;
    messagesEl.appendChild(div);
    scrollToBottom();
    return div;
  }
  
  function createTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'botman-message bot typing-indicator';
    div.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    messagesEl.appendChild(div);
    scrollToBottom();
    return div;
  }

  function appendMessage(role, text) {
    state.messages.push({ role, content: text });
    createMessageElement(role, text);
  }

  function handleSend() {
    const text = inputEl.value.trim();
    if (!text) return;

    appendMessage('user', text);
    inputEl.value = '';
    
    api.sendMessage(text);
  }

  // Event Listeners
  launcher.addEventListener('click', toggleWindow);
  closeBtn.addEventListener('click', toggleWindow);
  
  sendBtn.addEventListener('click', handleSend);
  
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  // Initialization
  api.getConfig();
  if (state.sessionToken) {
    // Maybe load history? Backend doesn't support history API yet for widget.
    // For now, clear messages if we reload page, or persist in local storage if we want.
    // Let's start fresh visually but keep session.
  }

})();
