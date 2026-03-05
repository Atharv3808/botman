(function() {
  "use strict";

  if (window.__botman_script_loaded) return;
  window.__botman_script_loaded = true;

  const getScriptConfig = () => {
    const scriptTag = document.currentScript || document.querySelector('script[data-bot-id]');
    if (!scriptTag) {
      console.error("Botman: Script tag not found. Make sure you use data-bot-id attribute.");
      return null;
    }
    
    const src = scriptTag.src;
    const url = new URL(src);
    const apiBase = `${url.origin}/widget`;
    
    return {
      botId: scriptTag.getAttribute('data-bot-id') || scriptTag.getAttribute('data-bot-token'),
      apiBase: apiBase
    };
  };

  const scriptConfig = getScriptConfig();
  if (!scriptConfig) return;

  const CONFIG = {
    API_BASE: scriptConfig.apiBase,
    CDN_BASE: "https://cdn.botman.ai",
    SESSION_KEY: "botman_session",
    RECONNECT_DELAY: 1000,
    MAX_RECONNECT_DELAY: 30000,
  };

  class BotmanWidget {
    constructor() {
      if (window.__botman_initialized) return;
      window.__botman_initialized = true;

      this.botId = scriptConfig.botId;
      this.config = null;
      this.sessionToken = null;
      this.visitorId = null;
      this.isOpen = false;
      this.container = null;
      this.shadow = null;
      this.socket = null;
      this.reconnectAttempts = 0;
      this.isTyping = false;

      this.init();
    }

    async init() {
      console.log("Botman: Initializing for bot:", this.botId);
      
      // Try to load config from sessionStorage first to avoid unnecessary network requests
      const cachedConfigKey = `botman_config_${this.botId}`;
      const cachedConfig = sessionStorage.getItem(cachedConfigKey);
      
      if (cachedConfig) {
        try {
          this.config = JSON.parse(cachedConfig);
          console.log("Botman: Using cached config", this.config);
          this.setupUI();
          return;
        } catch (e) {
          sessionStorage.removeItem(cachedConfigKey);
        }
      }

      // 2. Fetch Configuration
      try {
        const configUrl = `${CONFIG.API_BASE}/config/${this.botId}/`;
        console.log("Botman: Fetching config from:", configUrl);
        const response = await fetch(configUrl);
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(`Botman: Failed to fetch configuration. ${errorData.error || response.statusText}`);
        }
        this.config = await response.json();
        console.log("Botman: Config loaded successfully", this.config);
        
        // Cache config in sessionStorage
        sessionStorage.setItem(cachedConfigKey, JSON.stringify(this.config));
      } catch (err) {
        console.error("Botman: Error during init:", err);
        return;
      }

      // 3. Setup UI Container (Shadow DOM)
      this.setupUI();
    }

    setupUI() {
      if (!document.body) {
        console.warn("Botman: document.body not ready. Retrying setupUI in 50ms...");
        setTimeout(() => this.setupUI(), 50);
        return;
      }
      this.container = document.createElement('div');
      this.container.id = 'botman-widget-container';
      document.body.appendChild(this.container);

      this.shadow = this.container.attachShadow({ mode: 'closed' });
      this.injectStyles();
      this.render();
    }

    injectStyles() {
      const primaryColor = this.config.theme?.primary_color || "#10b981";
      const style = document.createElement('style');
      style.textContent = `
        :host {
          all: initial;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        .botman-launcher {
          position: fixed;
          bottom: 24px;
          right: 24px;
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background: ${primaryColor};
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 0.2s ease;
          z-index: 999999;
        }
        .botman-launcher:hover { transform: scale(1.1); }
        .botman-launcher svg { fill: white; width: 30px; height: 30px; }

        .botman-window {
          position: fixed;
          bottom: 100px;
          right: 24px;
          width: 380px;
          height: 600px;
          max-height: calc(100vh - 120px);
          background: white;
          border-radius: 16px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.2);
          display: none;
          flex-direction: column;
          overflow: hidden;
          z-index: 999999;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          opacity: 0;
          transform: translateY(20px);
        }
        .botman-window.active {
          display: flex;
          opacity: 1;
          transform: translateY(0);
        }

        .botman-header {
          padding: 20px;
          background: ${primaryColor};
          color: white;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .botman-header h3 { margin: 0; font-size: 16px; font-weight: 600; }
        
        .botman-messages {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 12px;
          background: #f9fafb;
        }
        .message {
          max-width: 80%;
          padding: 10px 14px;
          border-radius: 12px;
          font-size: 14px;
          line-height: 1.4;
          word-wrap: break-word;
        }
        .message.bot { background: white; border: 1px solid #e5e7eb; align-self: flex-start; border-bottom-left-radius: 2px; }
        .message.user { background: ${primaryColor}; color: white; align-self: flex-end; border-bottom-right-radius: 2px; }

        .botman-input-area {
          padding: 16px;
          border-top: 1px solid #e5e7eb;
          display: flex;
          gap: 8px;
        }
        .botman-input {
          flex: 1;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 8px 12px;
          outline: none;
          font-size: 14px;
        }
        .botman-send {
          background: ${primaryColor};
          color: white;
          border: none;
          border-radius: 8px;
          padding: 8px 16px;
          cursor: pointer;
          font-weight: 600;
        }
        
        .typing-indicator {
          display: flex;
          gap: 4px;
          padding: 10px 14px;
          background: #f3f4f6;
          border-radius: 12px;
          width: fit-content;
          align-self: flex-start;
          display: none;
        }
        .dot { width: 4px; height: 4px; background: #9ca3af; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out; }
        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); } }

        @media (max-width: 480px) {
          .botman-window { width: 100%; height: 100%; bottom: 0; right: 0; border-radius: 0; max-height: 100%; }
        }
      `;
      this.shadow.appendChild(style);
    }

    render() {
      const launcher = document.createElement('div');
      launcher.className = 'botman-launcher';
      launcher.innerHTML = `<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>`;
      launcher.onclick = () => this.toggleChat();
      
      const window = document.createElement('div');
      window.className = 'botman-window';
      window.innerHTML = `
        <div class="botman-header">
          <h3>${this.config.name}</h3>
          <span style="cursor:pointer" id="botman-close">✕</span>
        </div>
        <div class="botman-messages" id="botman-messages">
          <div class="message bot">${this.config.initial_message}</div>
          <div class="typing-indicator" id="botman-typing">
            <div class="dot"></div><div class="dot"></div><div class="dot"></div>
          </div>
        </div>
        <form class="botman-input-area" id="botman-form">
          <input type="text" class="botman-input" placeholder="Type a message..." id="botman-input" autocomplete="off">
          <button type="submit" class="botman-send">Send</button>
        </form>
      `;

      this.shadow.appendChild(launcher);
      this.shadow.appendChild(window);

      this.shadow.getElementById('botman-close').onclick = () => this.toggleChat();
      this.shadow.getElementById('botman-form').onsubmit = (e) => {
        e.preventDefault();
        this.handleSend();
      };
    }

    async toggleChat() {
      this.isOpen = !this.isOpen;
      const win = this.shadow.querySelector('.botman-window');
      win.classList.toggle('active', this.isOpen);
      
      if (this.isOpen && !this.sessionToken) {
        await this.initSession();
      }
    }

    async initSession() {
      // 1. Get Session from localStorage or API
      const stored = localStorage.getItem(`${CONFIG.SESSION_KEY}_${this.botId}`);
      if (stored) {
        const { token, vid } = JSON.parse(stored);
        this.sessionToken = token;
        this.visitorId = vid;
      } else {
        try {
          const res = await fetch(`${CONFIG.API_BASE}/session/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bot_token: this.botId })
          });
          const data = await res.json();
          this.sessionToken = data.session_token;
          this.visitorId = data.visitor_id;
          localStorage.setItem(`${CONFIG.SESSION_KEY}_${this.botId}`, JSON.stringify({
            token: this.sessionToken,
            vid: this.visitorId
          }));
        } catch (err) {
          console.error("Botman: Session init failed", err);
        }
      }
    }

    handleSend() {
      const input = this.shadow.getElementById('botman-input');
      const text = input.value.trim();
      if (!text) return;

      this.addMessage(text, 'user');
      input.value = '';
      this.sendMessage(text);
    }

    addMessage(text, role) {
      const container = this.shadow.getElementById('botman-messages');
      const typing = this.shadow.getElementById('botman-typing');
      
      const msg = document.createElement('div');
      msg.className = `message ${role}`;
      msg.textContent = text;
      
      container.insertBefore(msg, typing);
      container.scrollTop = container.scrollHeight;
    }

    async sendMessage(text) {
      this.showTyping(true);
      
      try {
        const response = await fetch(`${CONFIG.API_BASE}/chat/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_token: this.sessionToken,
            message: text
          })
        });

        if (response.headers.get('Content-Type')?.includes('text/event-stream')) {
          this.handleStreamingResponse(response);
        } else {
          const data = await response.json();
          this.showTyping(false);
          this.addMessage(data.response, 'bot');
        }
      } catch (err) {
        this.showTyping(false);
        this.addMessage("Sorry, I'm having trouble connecting right now.", 'bot');
      }
    }

    async handleStreamingResponse(response) {
      this.showTyping(false);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let botMessageElement = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.trim().startsWith('data: ')) {
            const dataStr = line.trim().slice(6);
            if (dataStr === '[DONE]') break;
            
            try {
              const data = JSON.parse(dataStr);
              const content = data.content || data.chunk || "";
              
              if (content) {
                if (!botMessageElement) {
                  botMessageElement = document.createElement('div');
                  botMessageElement.className = 'message bot';
                  const container = this.shadow.getElementById('botman-messages');
                  const typing = this.shadow.getElementById('botman-typing');
                  container.insertBefore(botMessageElement, typing);
                }
                
                botMessageElement.textContent += content;
                const container = this.shadow.getElementById('botman-messages');
                container.scrollTop = container.scrollHeight;
              }
            } catch (e) {
              console.warn("Botman: Failed to parse chunk", e, dataStr);
            }
          }
        }
      }
    }

    showTyping(show) {
      this.isTyping = show;
      const indicator = this.shadow.getElementById('botman-typing');
      indicator.style.display = show ? 'flex' : 'none';
      const container = this.shadow.getElementById('botman-messages');
      container.scrollTop = container.scrollHeight;
    }
  }

  // Self-initialize
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new BotmanWidget());
  } else {
    new BotmanWidget();
  }
})();
