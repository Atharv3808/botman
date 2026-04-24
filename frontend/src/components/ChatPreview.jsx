import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, RefreshCw, Loader2, Mic, MicOff, Volume2, VolumeX, Settings, ChevronDown, X, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { chatTest } from '../api/client';
import { voiceManager } from '../utils/voiceManager';

const CodeBlock = ({ language, value }) => {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-4 rounded-lg overflow-hidden border border-white/10">
      <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/10 text-[10px] uppercase tracking-widest font-bold text-white/40">
        <span>{language || 'code'}</span>
        <button 
          onClick={copyToClipboard}
          className="flex items-center gap-1.5 hover:text-white transition-colors"
        >
          {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <SyntaxHighlighter
        language={language || 'text'}
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          padding: '1.25rem',
          fontSize: '0.85rem',
          backgroundColor: 'transparent',
        }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
};

const FormattedMessage = ({ content, role }) => {
  if (role === 'user') {
    return <div className="whitespace-pre-wrap">{content}</div>;
  }

  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            return !inline ? (
              <CodeBlock
                language={match ? match[1] : ''}
                value={String(children).replace(/\n$/, '')}
              />
            ) : (
              <code className="bg-white/10 px-1.5 py-0.5 rounded text-emerald-300 font-mono text-[0.9em]" {...props}>
                {children}
              </code>
            );
          },
          p: ({ children }) => <p className="mb-4 last:mb-0 leading-relaxed">{children}</p>,
          ul: ({ children }) => <ul className="list-disc ml-4 mb-4 space-y-2">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal ml-4 mb-4 space-y-2">{children}</ol>,
          li: ({ children }) => <li className="pl-1">{children}</li>,
          h1: ({ children }) => <h1 className="text-xl font-bold mb-4 mt-6 first:mt-0">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-bold mb-3 mt-5 first:mt-0">{children}</h2>,
          h3: ({ children }) => <h3 className="text-md font-bold mb-2 mt-4 first:mt-0">{children}</h3>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-emerald-500/30 pl-4 py-1 my-4 italic text-white/60 bg-white/5 rounded-r-lg">
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-6 rounded-xl border border-white/10">
              <table className="w-full text-left border-collapse">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-white/5 text-white/90 font-bold">{children}</thead>,
          th: ({ children }) => <th className="p-3 border-b border-white/10">{children}</th>,
          td: ({ children }) => <td className="p-3 border-b border-white/5 text-white/70">{children}</td>,
          hr: () => <hr className="my-8 border-white/10" />,
          a: ({ children, href }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:underline">
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default function ChatPreview({ botId, onMinimize }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const [sessionId] = useState(`test-${Date.now()}`);
  
  // Voice State
  const [isListening, setIsListening] = useState(false);
  const [voiceEnabled] = useState(false);
  const [showVoiceSettings] = useState(false);
  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initialize voices
    voiceManager.getVoices().then(availableVoices => {
      setVoices(availableVoices);
      // Try to find a good default English voice
      const defaultVoice = availableVoices.find(v => v.lang === 'en-US' && v.name.includes('Google')) || availableVoices[0];
      if (defaultVoice) setSelectedVoice(defaultVoice.name);
    });
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    // Stop listening if sending
    if (isListening) {
        voiceManager.stopListening();
        setIsListening(false);
    }
    
    // Stop any current speech (Barge-in)
    voiceManager.cancel();

    const userMessage = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInput('');
    setLoading(true);

    try {
      const response = await chatTest({
        bot_id: botId,
        message: userMessage,
        visitor_id: sessionId,
        stream: false
      });

      const botResponse = response.data.response || response.data.answer || "I didn't get a response.";
      
      setMessages(prev => [...prev, { role: 'assistant', content: botResponse }]);

      // TTS - Speak response if enabled
      if (voiceEnabled) {
          voiceManager.speak(botResponse, selectedVoice);
      }

    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error.' }]);
      if (voiceEnabled) voiceManager.speak('Sorry, I encountered an error.', selectedVoice);
    } finally {
      setLoading(false);
    }
  };

  const toggleListening = () => {
    if (isListening) {
      voiceManager.stopListening();
      setIsListening(false);
    } else {
      // Barge-in: stop speaking when user starts listening
      voiceManager.cancel();
      
      const started = voiceManager.startListening(
        (transcript, isFinal) => {
          setInput(transcript);
          if (isFinal) {
              // Optional: Auto-send on final result for "hands-free" feel
              // We need to wait a tick for state update or pass transcript directly
              // For now, let's just fill it. User can click send or we can auto-send.
              // To auto-send, we'd need to refactor handleSend to accept text.
              // Let's keep it manual for safety unless we want full voice mode.
              // Actually, "comprehensive voice chat" implies auto-send.
              // But React state 'input' might not be updated inside this callback immediately for handleSend to see it if we call handleSend() directly.
              // So we will just setInput.
          }
        },
        () => setIsListening(false),
        (err) => {
             console.error("Mic error:", err);
             setIsListening(false);
        }
      );
      if (started) setIsListening(true);
    }
  };

  return (
    <div className="flex flex-col h-full bg-transparent font-sans">
      <div className="p-4 border-b border-white/10 flex justify-between items-center">
        <h3 className="font-semibold text-white/90">Live Preview</h3>
        <div className="flex items-center gap-1.5">
            <button
                onClick={onMinimize}
                className={`p-2 rounded-lg transition-colors text-white/60 hover:bg-white/10 hover:text-white'}`}
                title="Hide Preview"
            >
                <X size={18} />
            </button>
        </div>
      </div>

      {/* Voice Settings Panel */}
      {showVoiceSettings && (
          <div className="bg-black/20 px-4 py-3 border-b border-white/10 text-xs">
              <label className="block mb-1.5 font-semibold text-white/70">Voice</label>
              <select 
                className="w-full p-2 bg-white/[0.05] border border-white/10 rounded-md text-sm text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-shadow"
                value={selectedVoice || ''}
                onChange={(e) => setSelectedVoice(e.target.value)}
              >
                  {voices.map(v => (
                      <option key={v.name} value={v.name} className="bg-[#1c1c1c]">
                          {v.name} ({v.lang})
                      </option>
                  ))}
              </select>
          </div>
      )}

      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex items-end gap-2.5 ${
              msg.role === 'user' ? 'flex-row-reverse' : ''
            }`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${
              msg.role === 'user' ? 'bg-emerald-500 text-[#0a0a0a]' : 'bg-[#1c1c1c] border border-white/10 text-emerald-400'
            }`}>
              {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div
              className={`max-w-[85%] p-3.5 rounded-2xl text-sm shadow-sm ${
                msg.role === 'user'
                  ? 'bg-emerald-500 text-[#0a0a0a] rounded-br-none'
                  : 'bg-[#1c1c1c] text-white/80 rounded-bl-none border border-white/10'
              }`}
            >
              <FormattedMessage content={msg.content} role={msg.role} />
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-end gap-2.5">
            <div className="w-8 h-8 rounded-full bg-[#1c1c1c] border border-white/10 text-emerald-400 flex items-center justify-center shrink-0 shadow-sm">
              <Bot size={16} />
            </div>
            <div className="bg-[#1c1c1c] p-3.5 rounded-2xl rounded-bl-none border border-white/10 shadow-sm">
              <Loader2 size={16} className="animate-spin text-white/40" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-white/10">
        <form onSubmit={handleSend} className="flex items-center gap-2.5">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isListening ? "Listening..." : "Type a message..."}
            className="flex-1 px-4 py-2.5 bg-white/[0.03] border border-white/10 rounded-xl text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
            disabled={loading}
          />
          <button
            type="button"
            onClick={toggleListening}
            className={`p-2.5 rounded-xl transition-colors ${
                isListening 
                ? 'bg-red-500/10 text-red-400 animate-pulse' 
                : 'text-white/60 hover:bg-white/10 hover:text-white'
            }`}
            title="Toggle Voice Input"
          >
            {isListening ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2.5 bg-gradient-to-br from-emerald-400 to-teal-500 text-[#0a0a0a] rounded-xl hover:scale-105 active:scale-95 transition-all duration-200 shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
