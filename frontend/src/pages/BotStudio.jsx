import { useEffect, useState } from 'react';
import { useParams, NavLink, Outlet, Link } from 'react-router-dom';
import { getBot, publishBot } from '../api/client';
import { Settings, Database, Shield, ArrowLeft, BarChart, MessageSquare, Rocket, X, Copy, Check } from 'lucide-react';
import ChatPreview from '../components/ChatPreview';

export default function BotStudio() {
  const { botId } = useParams();
  const [bot, setBot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isPreviewVisible, setIsPreviewVisible] = useState(true);
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishResult, setPublishResult] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadBot();
  }, [botId]);

  const loadBot = async () => {
    try {
      const response = await getBot(botId);
      setBot(response.data);
    } catch (error) {
      console.error('Failed to load bot:', error);
    } finally {
      setLoading(false);
  }
};

  const handlePublish = async () => {
    setIsPublishing(true);
    try {
      const response = await publishBot(botId);
      setPublishResult(response.data);
    } catch (error) {
      console.error('Failed to publish bot:', error);
    } finally {
      setIsPublishing(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return <div className="h-screen flex items-center justify-center text-white/40">Loading Studio...</div>;
  if (!bot) return <div className="h-screen flex items-center justify-center text-white/40">Bot not found</div>;

  const navItems = [
    { to: 'settings', icon: Settings, label: 'Settings' },
    { to: 'knowledge', icon: Database, label: 'Knowledge' },
    { to: 'provider', icon: Shield, label: 'Provider' },
    { to: 'analytics', icon: BarChart, label: 'Analytics' },
  ];

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left Sidebar */}
      <div className="w-64 bg-[#161616]/60 backdrop-blur-xl border-r border-white/5 flex flex-col shrink-0">
        <div className="p-4 border-b border-white/5">
          <Link to="/" className="flex items-center text-white/60 hover:text-white mb-5 transition-colors text-sm font-medium">
            <ArrowLeft size={16} className="mr-2" />
            Back to Dashboard
          </Link>
          <div className="flex items-center gap-3.5">
             <div className="w-11 h-11 bg-gradient-to-br from-emerald-400 to-teal-500 text-[#0a0a0a] rounded-xl flex items-center justify-center font-bold text-xl shadow-lg shadow-emerald-500/20">
               {bot.name.charAt(0).toUpperCase()}
             </div>
             <div className="min-w-0">
                <h1 className="font-semibold text-white/90 text-md truncate" title={bot.name}>{bot.name}</h1>
                <p className="text-xs text-emerald-400 font-medium flex items-center gap-1.5">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
                  Active
                </p>
             </div>
          </div>
        </div>
        
        <nav className="flex-1 p-3 space-y-1.5">
          <div className="text-xs font-semibold text-white/30 uppercase tracking-wider mb-2 px-2.5">Menu</div>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ease-in-out ${
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-300 shadow-sm'
                    : 'text-white/60 hover:bg-white/[0.03] hover:text-white'
                }`
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-white/5 space-y-4">
          <button
            onClick={handlePublish}
            disabled={isPublishing}
            className="w-full flex items-center justify-center gap-2.5 px-4 py-2.5 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl text-[#0a0a0a] font-semibold hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 shadow-lg shadow-emerald-500/20 disabled:opacity-50"
          >
            <Rocket size={18} />
            {isPublishing ? 'Publishing...' : 'Publish Bot'}
          </button>
          <div className="text-xs text-white/30 text-center font-medium">
            BotMan Studio v1.0
          </div>
        </div>
      </div>

      {/* Center Content */}
      <div className="flex-1 overflow-auto relative">
        <Outlet />
        {!isPreviewVisible && (
          <button 
            onClick={() => setIsPreviewVisible(true)}
            className="fixed top-1/2 right-0 -translate-y-1/2 bg-gradient-to-br from-emerald-400 to-teal-500 text-[#0a0a0a] p-3 rounded-l-xl shadow-lg hover:scale-105 transition-all duration-200"
          >
            <MessageSquare size={24} />
          </button>
        )}
      </div>

      {/* Right Preview Panel */}
      {isPreviewVisible && (
        <div className="w-[400px] bg-[#161616]/60 backdrop-blur-xl border-l border-white/5 shrink-0 flex flex-col">
          <ChatPreview botId={botId} onMinimize={() => setIsPreviewVisible(false)} />
        </div>
      )}

      {/* Publish Result Modal */}
      {publishResult && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[9999] p-4">
          <div className="bg-[#161616] border border-white/10 rounded-[32px] p-8 max-w-2xl w-full shadow-2xl">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Bot Published Successfully! 🚀</h2>
                <p className="text-white/40">Copy the script below and paste it before the &lt;/body&gt; tag of your website.</p>
              </div>
              <button 
                onClick={() => setPublishResult(null)}
                className="p-2 text-white/20 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-1000"></div>
              <div className="relative bg-[#0a0a0a] border border-white/5 rounded-2xl p-6 font-mono text-sm overflow-hidden">
                <code className="text-emerald-400 break-all whitespace-pre-wrap">
                  {publishResult.embed_script}
                </code>
                <button
                  onClick={() => copyToClipboard(publishResult.embed_script)}
                  className="absolute top-4 right-4 p-2 bg-white/5 hover:bg-white/10 rounded-lg text-white/60 hover:text-white transition-all"
                  title="Copy to clipboard"
                >
                  {copied ? <Check size={18} className="text-emerald-400" /> : <Copy size={18} />}
                </button>
              </div>
            </div>

            <div className="mt-8 flex items-center gap-4 p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl">
              <div className="w-10 h-10 bg-emerald-500/20 rounded-full flex items-center justify-center text-emerald-400 shrink-0">
                <Settings size={20} />
              </div>
              <div className="text-sm">
                <p className="text-white/80 font-medium">Pro Tip</p>
                <p className="text-white/40">You can manage allowed domains in the Settings tab to restrict where your widget can be loaded.</p>
              </div>
            </div>

            <button
              onClick={() => setPublishResult(null)}
              className="w-full mt-8 py-4 bg-white/[0.03] hover:bg-white/[0.06] border border-white/5 rounded-2xl text-white font-semibold transition-all"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
