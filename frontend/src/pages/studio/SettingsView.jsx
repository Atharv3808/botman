import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getBotSettings, updateBotSettings } from '../../api/client';
import { Save, AlertCircle } from 'lucide-react';

export default function SettingsView() {
  const { botId } = useParams();
  const [settings, setSettings] = useState({
    name: '',
    system_prompt: '',
    selected_llm: 'openai', 
    allowed_domains: '',
    bot_type: 'custom',
    personality: '',
    tone: '',
    fallback_behavior: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadSettings();
  }, [botId]);

  const loadSettings = async () => {
    try {
      const response = await getBotSettings(botId);
      // Ensure we have default values
      setSettings({
        name: response.data.name || '',
        system_prompt: response.data.system_prompt || '',
        selected_llm: response.data.selected_llm || 'openai',
        allowed_domains: response.data.allowed_domains || '',
        bot_type: response.data.bot_type || 'custom',
        personality: response.data.personality || '',
        tone: response.data.tone || '',
        fallback_behavior: response.data.fallback_behavior || ''
      });
    } catch (error) {
      console.error('Failed to load settings:', error);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      await updateBotSettings(botId, settings);
      setMessage({ type: 'success', text: 'Settings saved successfully' });
    } catch (error) {
      console.error('Failed to save settings:', error);
      setMessage({ type: 'error', text: 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading settings...</div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-10">
        <h2 className="text-3xl font-semibold text-white tracking-tight">Bot <span className="text-white/60 font-normal">Configuration</span></h2>
        <p className="text-white/40 mt-1">Manage your bot's identity and behavior.</p>
      </div>

      {message && (
        <div className={`mb-6 p-4 rounded-xl flex items-center gap-3 ${
          message.type === 'success' ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'
        }`}>
          <AlertCircle size={20} />
          <span className="font-medium">{message.text}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8 bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Bot Name</label>
            <input
              type="text"
              value={settings.name}
              onChange={(e) => setSettings({ ...settings, name: e.target.value })}
              className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Bot Type</label>
            <select
              value={settings.bot_type}
              onChange={(e) => setSettings({ ...settings, bot_type: e.target.value })}
              className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
            >
              <option value="custom">Custom Bot</option>
              <option value="sales">Sales Bot</option>
              <option value="support">Support Bot</option>
              <option value="marketing">Marketing Bot</option>
              <option value="faq">FAQ Bot</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Personality</label>
            <p className="text-xs text-white/40 mb-2">Describe the bot's character (e.g. "An aggressive closer", "A helpful guide").</p>
            <textarea
              value={settings.personality}
              onChange={(e) => setSettings({ ...settings, personality: e.target.value })}
              rows={3}
              className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300 font-mono text-sm"
              placeholder="You are a friendly and patient assistant..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Tone</label>
            <p className="text-xs text-white/40 mb-2">Describe the bot's tone (e.g. "Professional, Friendly, Enthusiastic").</p>
            <textarea
              value={settings.tone}
              onChange={(e) => setSettings({ ...settings, tone: e.target.value })}
              rows={3}
              className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300 font-mono text-sm"
              placeholder="e.g. Professional, Friendly, Enthusiastic"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-white/70 mb-2">System Prompt</label>
          <p className="text-xs text-white/40 mb-2">Define how the bot should behave and what personality it should have.</p>
          <textarea
            value={settings.system_prompt}
            onChange={(e) => setSettings({ ...settings, system_prompt: e.target.value })}
            rows={10}
            className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300 font-mono text-sm"
            placeholder="You are a helpful assistant..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-white/70 mb-2">Fallback Behavior</label>
          <p className="text-xs text-white/40 mb-2">What should the bot say when it doesn't know the answer (No knowledge context)?</p>
          <textarea
            value={settings.fallback_behavior}
            onChange={(e) => setSettings({ ...settings, fallback_behavior: e.target.value })}
            rows={3}
            className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300 font-mono text-sm"
            placeholder="I'm sorry, I don't have that information. Would you like to speak to a human?"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Model Provider</label>
            <select
              value={settings.selected_llm}
              onChange={(e) => setSettings({ ...settings, selected_llm: e.target.value })}
              className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
            >
              <option value="openai">OpenAI (GPT-4)</option>
              <option value="gemini">Google Gemini</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Allowed Domains</label>
            <input
              type="text"
              value={settings.allowed_domains}
              onChange={(e) => setSettings({ ...settings, allowed_domains: e.target.value })}
              placeholder="example.com, mysite.com"
              className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
            />
            <p className="text-xs text-white/40 mt-2">Comma-separated list of domains allowed to use the widget.</p>
          </div>
        </div>

        <div className="pt-6 border-t border-white/5 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2.5 px-6 py-2.5 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl text-[#0a0a0a] font-semibold hover:scale-105 active:scale-95 transition-all duration-200 shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save size={18} />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
}
