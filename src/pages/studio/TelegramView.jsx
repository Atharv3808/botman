import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { connectTelegram, getBot } from '../../api/client';
import { Send, CheckCircle2, AlertCircle, Loader2, ExternalLink, ShieldCheck, Info } from 'lucide-react';

export default function TelegramView() {
  const { botId } = useParams();
  const [token, setToken] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [status, setStatus] = useState({ type: '', message: '' });
  const [integration, setIntegration] = useState(null);

  const loadBot = useCallback(async () => {
    try {
      const response = await getBot(botId);
      if (response.data.telegram_integration) {
        setIntegration(response.data.telegram_integration);
        setToken(response.data.telegram_integration.telegram_bot_token || '');
      }
    } catch (error) {
      console.error('Failed to load bot:', error);
    }
  }, [botId]);
  
  useEffect(() => {
    loadBot();
  }, [loadBot]);

  const handleConnect = async (e) => {
    e.preventDefault();
    if (!token) return;

    setIsConnecting(true);
    setStatus({ type: '', message: '' });

    try {
      const response = await connectTelegram({
        bot_id: botId,
        telegram_bot_token: token
      });
      
      setStatus({ 
        type: 'success', 
        message: `Successfully connected to @${response.data.bot_username}!` 
      });
      
      // Reload bot to get updated integration data
      loadBot();
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Failed to connect Telegram bot. Please check your token.';
      setStatus({ type: 'error', message: errorMsg });
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header Section */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-500/10 rounded-xl">
            <Send className="text-blue-400" size={24} />
          </div>
          <h2 className="text-2xl font-bold text-white/90">Telegram Integration</h2>
        </div>
        <p className="text-white/40 text-sm leading-relaxed max-w-2xl">
          Connect your bot to Telegram and reach your users where they are. 
          Botman will automatically handle messages using your AI configuration.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Connection Form */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-[#161616]/40 backdrop-blur-xl border border-white/5 rounded-2xl p-6 space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wider">Configuration</h3>
              {integration?.is_active && (
                <span className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 text-emerald-400 text-[10px] font-bold rounded-full border border-emerald-500/20 uppercase tracking-tight">
                  <div className="w-1 h-1 bg-emerald-400 rounded-full animate-pulse"></div>
                  Connected
                </span>
              )}
            </div>

            <form onSubmit={handleConnect} className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-white/40 ml-1">Telegram Bot Token</label>
                <div className="relative group">
                  <input
                    type="password"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
                    className="w-full bg-white/[0.03] border border-white/5 rounded-xl px-4 py-3.5 text-sm text-white/80 placeholder:text-white/10 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/40 transition-all duration-300"
                  />
                  <div className="absolute inset-0 rounded-xl bg-blue-500/5 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-300"></div>
                </div>
              </div>

              <button
                type="submit"
                disabled={isConnecting || !token}
                className="w-full bg-blue-500 hover:bg-blue-400 disabled:bg-white/5 disabled:text-white/20 text-white font-semibold py-3.5 rounded-xl transition-all duration-300 flex items-center justify-center gap-2 shadow-lg shadow-blue-500/10 active:scale-[0.98]"
              >
                {isConnecting ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <ShieldCheck size={18} />
                    {integration ? 'Update Connection' : 'Connect Telegram Bot'}
                  </>
                )}
              </button>
            </form>

            {status.message && (
              <div className={`p-4 rounded-xl flex items-start gap-3 border animate-in zoom-in-95 duration-300 ${
                status.type === 'success' 
                  ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-400' 
                  : 'bg-red-500/5 border-red-500/20 text-red-400'
              }`}>
                {status.type === 'success' ? <CheckCircle2 size={18} className="shrink-0 mt-0.5" /> : <AlertCircle size={18} className="shrink-0 mt-0.5" />}
                <p className="text-sm font-medium leading-relaxed">{status.message}</p>
              </div>
            )}
          </div>

          {integration && (
            <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-6 space-y-4">
              <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wider">Bot Details</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-white/20 uppercase tracking-widest">Username</p>
                  <p className="text-sm text-white/80 font-medium">@{integration.telegram_bot_username}</p>
                </div>
                <div className="space-y-1 text-right">
                  <p className="text-[10px] font-bold text-white/20 uppercase tracking-widest">Status</p>
                  <p className="text-sm text-emerald-400 font-bold">ACTIVE</p>
                </div>
              </div>
              <div className="pt-4 border-t border-white/5">
                <a 
                  href={`https://t.me/${integration.telegram_bot_username}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1.5 transition-colors font-medium"
                >
                  Open in Telegram <ExternalLink size={12} />
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <div className="bg-gradient-to-br from-blue-500/10 to-indigo-500/10 border border-blue-500/20 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-blue-400">
              <Info size={18} />
              <h4 className="text-sm font-bold uppercase tracking-wider">Setup Guide</h4>
            </div>
            <ol className="space-y-4 text-xs text-white/50 leading-relaxed list-decimal ml-4">
              <li>Message <a href="https://t.me/botfather" target="_blank" className="text-blue-400 hover:underline">@BotFather</a> on Telegram.</li>
              <li>Create a new bot with <code className="bg-white/5 px-1 rounded text-white/70">/newbot</code> command.</li>
              <li>Follow instructions to get your <b>API Token</b>.</li>
              <li>Paste the token here and click <b>Connect</b>.</li>
              <li>Your bot is ready! Start chatting with it.</li>
            </ol>
          </div>

          <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-6 space-y-3">
             <h4 className="text-[10px] font-bold text-white/20 uppercase tracking-widest">Webhooks</h4>
             <p className="text-[11px] text-white/40 leading-relaxed">
               Webhook registration is automatic. Botman sets up the secure connection as soon as you connect your token.
             </p>
          </div>
        </div>
      </div>
    </div>
  );
}
