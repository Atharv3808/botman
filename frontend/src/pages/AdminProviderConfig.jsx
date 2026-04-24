import { useState, useEffect } from 'react';
import { 
  Plus, Shield, CheckCircle, XCircle, RefreshCcw, 
  Trash2, Edit, Save, History, Activity, Key, Globe, Layers, AlertCircle, Clock
} from 'lucide-react';
import { 
  getProviders, createProvider, updateProvider, 
  deleteProvider, testProviderConnection, rollbackProvider, 
  getProviderLogs 
} from '../api/client';

const PROVIDER_TEMPLATES = {
  openai: {
    name: 'OpenAI',
    fields: [
      { name: 'api_key', label: 'API Key', type: 'password', sensitive: true },
      { name: 'organization_id', label: 'Organization ID', type: 'text' },
    ],
    config_fields: [
      { name: 'default_model', label: 'Default Model', type: 'select', options: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
    ]
  },
  anthropic: {
    name: 'Anthropic',
    fields: [
      { name: 'api_key', label: 'API Key', type: 'password', sensitive: true },
    ],
    config_fields: [
      { name: 'default_model', label: 'Default Model', type: 'select', options: ['claude-3-5-sonnet-20240620', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'] },
    ]
  },
  google: {
    name: 'Google AI',
    fields: [
      { name: 'api_key', label: 'API Key', type: 'password', sensitive: true },
    ],
    config_fields: [
      { name: 'default_model', label: 'Default Model', type: 'select', options: ['gemini-1.5-pro', 'gemini-1.5-flash'] },
    ]
  },
  azure: {
    name: 'Azure OpenAI',
    fields: [
      { name: 'api_key', label: 'API Key', type: 'password', sensitive: true },
      { name: 'endpoint', label: 'Endpoint URL', type: 'text' },
    ],
    config_fields: [
      { name: 'api_version', label: 'API Version', type: 'text', defaultValue: '2023-05-15' },
      { name: 'deployment_name', label: 'Deployment Name', type: 'text' },
    ]
  }
};

export default function AdminProviderConfig() {
  const [providers, setProviders] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [testResults, setTestResults] = useState({});
  const [testing, setTesting] = useState({});
  const [activeTab, setActiveTab] = useState('list'); // list, logs

  const [formData, setFormData] = useState({
    provider_type: 'openai',
    name: '',
    credentials: {},
    config_data: {
      rate_limit: 60,
      custom_headers: {}
    },
    is_active: true
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [providersRes, logsRes] = await Promise.all([
        getProviders(),
        getProviderLogs()
      ]);
      setProviders(providersRes.data);
      setLogs(logsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e, section = 'root') => {
    const { name, value, type, checked } = e.target;
    const val = type === 'checkbox' ? checked : value;

    if (section === 'root') {
      setFormData(prev => ({ ...prev, [name]: val }));
      if (name === 'provider_type') {
        // Reset credentials and config when provider type changes
        setFormData(prev => ({ 
          ...prev, 
          [name]: val,
          credentials: {},
          config_data: { ...prev.config_data, default_model: PROVIDER_TEMPLATES[val]?.config_fields[0]?.options?.[0] || '' }
        }));
      }
    } else if (section === 'credentials') {
      setFormData(prev => ({
        ...prev,
        credentials: { ...prev.credentials, [name]: val }
      }));
    } else if (section === 'config_data') {
      setFormData(prev => ({
        ...prev,
        config_data: { ...prev.config_data, [name]: val }
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (selectedProvider) {
        await updateProvider(selectedProvider.id, formData);
      } else {
        await createProvider(formData);
      }
      setShowForm(false);
      setSelectedProvider(null);
      setFormData({
        provider_type: 'openai',
        name: '',
        credentials: {},
        config_data: { rate_limit: 60, custom_headers: {} },
        is_active: true
      });
      fetchData();
    } catch (error) {
      alert('Failed to save provider configuration: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleEdit = (provider) => {
    setSelectedProvider(provider);
    setFormData({
      provider_type: provider.provider_type,
      name: provider.name,
      credentials: {}, // Don't show old credentials for security
      config_data: provider.config_data,
      is_active: provider.is_active
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this provider?')) {
      try {
        await deleteProvider(id);
        fetchData();
      } catch (error) {
        alert('Failed to delete provider');
      }
    }
  };

  const handleTestConnection = async (id) => {
    setTesting(prev => ({ ...prev, [id]: true }));
    try {
      const response = await testProviderConnection(id);
      setTestResults(prev => ({ ...prev, [id]: response.data }));
    } catch (error) {
      setTestResults(prev => ({ 
        ...prev, 
        [id]: { success: false, message: error.response?.data?.message || error.message } 
      }));
    } finally {
      setTesting(prev => ({ ...prev, [id]: false }));
      fetchData(); // Refresh logs
    }
  };

  if (loading && providers.length === 0) {
    return <div className="flex items-center justify-center h-screen text-white/40">Loading Configuration...</div>;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto min-h-screen">
      <div className="flex justify-between items-center mb-10">
        <div>
          <h2 className="text-3xl font-semibold text-white tracking-tight">AI Provider <span className="text-white/60 font-normal">Configuration</span></h2>
          <p className="text-white/40 mt-1">Manage AI service providers, credentials, and connectivity.</p>
        </div>
        <div className="flex gap-4">
          <button 
            onClick={() => setActiveTab(activeTab === 'list' ? 'logs' : 'list')}
            className="flex items-center gap-2 px-5 py-2.5 bg-white/[0.03] border border-white/10 rounded-xl text-white/70 hover:bg-white/[0.06] hover:text-white transition-all"
          >
            {activeTab === 'list' ? <History size={18} /> : <Layers size={18} />}
            <span>{activeTab === 'list' ? 'View Logs' : 'View Providers'}</span>
          </button>
          <button 
            onClick={() => {
              setShowForm(true);
              setSelectedProvider(null);
            }}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl text-[#0a0a0a] font-semibold hover:scale-105 transition-all shadow-lg shadow-emerald-500/20"
          >
            <Plus size={18} />
            <span>Add Provider</span>
          </button>
        </div>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#161616] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-8 shadow-2xl">
            <div className="flex justify-between items-center mb-8">
              <h3 className="text-2xl font-semibold text-white">
                {selectedProvider ? 'Edit Provider' : 'Add New Provider'}
              </h3>
              <button onClick={() => setShowForm(false)} className="text-white/40 hover:text-white">
                <XCircle size={24} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-white/60 mb-2">Provider Type</label>
                  <select 
                    name="provider_type"
                    value={formData.provider_type}
                    onChange={(e) => handleInputChange(e)}
                    className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500/50 transition-all"
                  >
                    {Object.keys(PROVIDER_TEMPLATES).map(type => (
                      <option key={type} value={type} className="bg-[#161616]">{PROVIDER_TEMPLATES[type].name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white/60 mb-2">Friendly Name</label>
                  <input 
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={(e) => handleInputChange(e)}
                    placeholder="e.g. My OpenAI Production"
                    className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500/50 transition-all"
                    required
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-white/5">
                <h4 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <Key size={14} /> Credentials
                </h4>
                <div className="grid grid-cols-1 gap-4">
                  {PROVIDER_TEMPLATES[formData.provider_type].fields.map(field => (
                    <div key={field.name}>
                      <label className="block text-sm font-medium text-white/60 mb-2">{field.label}</label>
                      <input 
                        type={field.type}
                        name={field.name}
                        value={formData.credentials[field.name] || ''}
                        onChange={(e) => handleInputChange(e, 'credentials')}
                        placeholder={selectedProvider ? 'Leave empty to keep current' : `Enter ${field.label}`}
                        className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500/50 transition-all"
                        required={!selectedProvider && field.sensitive}
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-white/5">
                <h4 className="text-sm font-semibold text-blue-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <Globe size={14} /> Configuration
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  {PROVIDER_TEMPLATES[formData.provider_type].config_fields.map(field => (
                    <div key={field.name}>
                      <label className="block text-sm font-medium text-white/60 mb-2">{field.label}</label>
                      {field.type === 'select' ? (
                        <select 
                          name={field.name}
                          value={formData.config_data[field.name] || ''}
                          onChange={(e) => handleInputChange(e, 'config_data')}
                          className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500/50 transition-all"
                        >
                          {field.options.map(opt => (
                            <option key={opt} value={opt} className="bg-[#161616]">{opt}</option>
                          ))}
                        </select>
                      ) : (
                        <input 
                          type={field.type}
                          name={field.name}
                          value={formData.config_data[field.name] || field.defaultValue || ''}
                          onChange={(e) => handleInputChange(e, 'config_data')}
                          className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500/50 transition-all"
                        />
                      )}
                    </div>
                  ))}
                  <div>
                    <label className="block text-sm font-medium text-white/60 mb-2">Rate Limit (RPM)</label>
                    <input 
                      type="number"
                      name="rate_limit"
                      value={formData.config_data.rate_limit}
                      onChange={(e) => handleInputChange(e, 'config_data')}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-emerald-500/50 transition-all"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-4 pt-6">
                <button 
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-6 py-2.5 text-white/60 hover:text-white transition-all"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="px-8 py-2.5 bg-emerald-500 rounded-xl text-[#0a0a0a] font-bold hover:bg-emerald-400 transition-all shadow-lg shadow-emerald-500/10"
                >
                  {selectedProvider ? 'Update Configuration' : 'Save Provider'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {activeTab === 'list' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {providers.length === 0 ? (
            <div className="col-span-full py-20 text-center bg-white/[0.02] border border-dashed border-white/10 rounded-3xl">
              <Shield size={48} className="mx-auto text-white/10 mb-4" />
              <p className="text-white/40">No providers configured yet. Click "Add Provider" to get started.</p>
            </div>
          ) : (
            providers.map(provider => (
              <div key={provider.id} className="bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6 hover:border-white/10 transition-all group">
                <div className="flex justify-between items-start mb-6">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
                      <Globe size={20} />
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">{provider.name}</h4>
                      <span className="text-xs text-white/40 uppercase tracking-widest">{provider.provider_type}</span>
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => handleEdit(provider)} className="p-2 text-white/40 hover:text-white transition-colors">
                      <Edit size={16} />
                    </button>
                    <button onClick={() => handleDelete(provider.id)} className="p-2 text-red-500/40 hover:text-red-500 transition-colors">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                <div className="space-y-3 mb-6">
                  <div className="flex justify-between text-sm">
                    <span className="text-white/40">Default Model</span>
                    <span className="text-white/70">{provider.config_data.default_model || 'Not set'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-white/40">Rate Limit</span>
                    <span className="text-white/70">{provider.config_data.rate_limit} RPM</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-white/40">Version</span>
                    <span className="text-white/70">v{provider.version}</span>
                  </div>
                </div>

                <div className="pt-4 border-t border-white/5 flex flex-col gap-3">
                  <button 
                    onClick={() => handleTestConnection(provider.id)}
                    disabled={testing[provider.id]}
                    className={`flex items-center justify-center gap-2 w-full py-2.5 rounded-xl text-sm font-medium transition-all ${
                      testing[provider.id] ? 'bg-white/5 text-white/40' : 'bg-white/[0.05] text-white hover:bg-white/10'
                    }`}
                  >
                    {testing[provider.id] ? <RefreshCcw size={16} className="animate-spin" /> : <Activity size={16} />}
                    {testing[provider.id] ? 'Testing...' : 'Test Connection'}
                  </button>

                  {testResults[provider.id] && (
                    <div className={`p-3 rounded-xl flex items-start gap-3 text-xs animate-in fade-in slide-in-from-top-2 ${
                      testResults[provider.id].success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                    }`}>
                      {testResults[provider.id].success ? <CheckCircle size={14} className="mt-0.5 flex-shrink-0" /> : <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />}
                      <div>
                        <p className="font-semibold mb-0.5">{testResults[provider.id].success ? 'Connected' : 'Failed'}</p>
                        <p className="opacity-80 leading-relaxed">{testResults[provider.id].message}</p>
                        {testResults[provider.id].response_time_ms && (
                          <p className="mt-1 flex items-center gap-1 opacity-60">
                            <Clock size={10} /> {Math.round(testResults[provider.id].response_time_ms)}ms
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl overflow-hidden">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-white/[0.02] border-b border-white/5">
                <th className="px-6 py-4 text-sm font-medium text-white/40">Time</th>
                <th className="px-6 py-4 text-sm font-medium text-white/40">User</th>
                <th className="px-6 py-4 text-sm font-medium text-white/40">Provider</th>
                <th className="px-6 py-4 text-sm font-medium text-white/40">Action</th>
                <th className="px-6 py-4 text-sm font-medium text-white/40">Status</th>
                <th className="px-6 py-4 text-sm font-medium text-white/40">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {logs.map(log => (
                <tr key={log.id} className="hover:bg-white/[0.01] transition-colors">
                  <td className="px-6 py-4 text-sm text-white/60">{new Date(log.created_at).toLocaleString()}</td>
                  <td className="px-6 py-4 text-sm text-white/60">{log.user}</td>
                  <td className="px-6 py-4 text-sm text-white/90 font-medium">{log.provider_name}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 bg-white/5 rounded text-xs text-white/40 uppercase tracking-widest">{log.action}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`flex items-center gap-1.5 text-xs font-medium ${log.status === 'success' ? 'text-emerald-400' : 'text-red-400'}`}>
                      {log.status === 'success' ? <CheckCircle size={12} /> : <XCircle size={12} />}
                      {log.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-white/40 max-w-xs truncate">
                    {JSON.stringify(log.details)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
