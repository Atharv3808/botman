import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Shield, CheckCircle, Globe, RefreshCcw, Save, AlertCircle } from 'lucide-react';
import { getBot, updateBot, getProviders } from '../../api/client';

export default function ProviderView() {
  const { botId } = useParams();
  const [bot, setBot] = useState(null);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedProviderId, setSelectedProviderId] = useState('');
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    fetchData();
  }, [botId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [botRes, providersRes] = await Promise.all([
        getBot(botId),
        getProviders()
      ]);
      setBot(botRes.data);
      setProviders(providersRes.data);
      setSelectedProviderId(botRes.data.provider_config || '');
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setMessage({ type: 'error', text: 'Failed to load settings.' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage({ type: '', text: '' });
    try {
      await updateBot(botId, { provider_config: selectedProviderId || null });
      setMessage({ type: 'success', text: 'Provider configuration updated successfully!' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update provider.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-white/40">Loading settings...</div>;
  }

  const selectedProvider = providers.find(p => p.id === parseInt(selectedProviderId));

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-10 flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-semibold text-white tracking-tight">Provider <span className="text-white/60 font-normal">Configuration</span></h2>
          <p className="text-white/40 mt-1">Select the AI provider to power this chatbot.</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-6 py-2.5 bg-emerald-500 rounded-xl text-[#0a0a0a] font-bold hover:bg-emerald-400 transition-all disabled:opacity-50"
        >
          {saving ? <RefreshCcw size={18} className="animate-spin" /> : <Save size={18} />}
          Save Changes
        </button>
      </div>

      {message.text && (
        <div className={`mb-6 p-4 rounded-xl flex items-center gap-3 animate-in fade-in slide-in-from-top-2 ${
          message.type === 'success' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
        }`}>
          {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
          <p className="text-sm font-medium">{message.text}</p>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Select Provider</h3>
            <div className="space-y-3">
              <label className="block text-sm font-medium text-white/60 mb-2">Available Providers</label>
              <select
                value={selectedProviderId}
                onChange={(e) => setSelectedProviderId(e.target.value)}
                className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500/50 transition-all"
              >
                <option value="" className="bg-[#161616]">System Default</option>
                {providers.map(p => (
                  <option key={p.id} value={p.id} className="bg-[#161616]">{p.name} ({p.provider_type})</option>
                ))}
              </select>
              <p className="text-xs text-white/30 mt-2 italic">
                Administrators can configure global providers in the Admin Dashboard.
              </p>
            </div>
          </div>

          <div className="bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Shield size={18} className="text-emerald-400" /> Security Note
            </h3>
            <p className="text-sm text-white/40 leading-relaxed">
              All provider credentials are encrypted at rest using AES-256 (Fernet) encryption. 
              The API keys are never stored in plain text and are only decrypted temporarily when making API calls.
            </p>
          </div>
        </div>

        <div className="bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl p-8 flex flex-col items-center justify-center text-center">
          {selectedProvider ? (
            <div className="animate-in fade-in zoom-in-95 duration-300">
              <div className="inline-flex p-5 bg-emerald-500/10 rounded-full text-emerald-400 mb-6">
                <Globe size={48} />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">{selectedProvider.name}</h3>
              <p className="text-white/40 mb-6 uppercase tracking-widest text-xs font-bold">{selectedProvider.provider_type}</p>
              
              <div className="space-y-2 text-left bg-white/[0.02] border border-white/5 rounded-xl p-4 w-full">
                <div className="flex justify-between text-xs">
                  <span className="text-white/40 uppercase">Model</span>
                  <span className="text-white/70">{selectedProvider.config_data.default_model}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-white/40 uppercase">RPM Limit</span>
                  <span className="text-white/70">{selectedProvider.config_data.rate_limit}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-white/40 uppercase">Status</span>
                  <span className="text-emerald-400 font-bold">ACTIVE</span>
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="inline-flex p-5 bg-white/[0.03] rounded-full text-white/10 mb-6">
                <Shield size={48} />
              </div>
              <h3 className="text-xl font-semibold text-white/90 mb-2">No Custom Provider</h3>
              <p className="text-white/40 max-w-xs mx-auto text-sm leading-relaxed">
                This bot is using the system default provider settings. Select a custom provider from the list to override.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
