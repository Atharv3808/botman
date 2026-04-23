import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getBots, createBot, deleteBot } from '../api/client';
import { Plus, MessageSquare, Settings, BarChart, Trash2 } from 'lucide-react';

export default function Dashboard() {
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newBotName, setNewBotName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadBots();
  }, []);

  const loadBots = async () => {
    try {
      const response = await getBots();
      setBots(response.data);
    } catch (error) {
      console.error('Failed to load bots:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBot = async (e, botId) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this bot? This action cannot be undone.')) {
      try {
        await deleteBot(botId);
        loadBots();
      } catch (error) {
        console.error('Failed to delete bot:', error);
        alert('Failed to delete bot');
      }
    }
  };

  const handleCreateBot = async (e) => {
    e.preventDefault();
    if (!newBotName.trim()) return;

    try {
      await createBot({ name: newBotName });
      setNewBotName('');
      setIsCreating(false);
      loadBots();
    } catch (error) {
      if (error.response && error.response.status === 403) {
        navigate('/upgrade-plan');
      } else {
        console.error('Failed to create bot:', error);
      }
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen bg-gray-50">Loading...</div>;
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-10">
          <h1 className="text-4xl font-semibold text-white tracking-tight">
            My <span className="text-white/60 font-normal">Bots</span>
          </h1>
          <div className="flex gap-3">
            <Link 
              to="/conversations" 
              className="flex items-center gap-2.5 px-5 py-2.5 bg-white/[0.03] border border-white/10 rounded-xl text-white/70 hover:bg-white/[0.06] hover:text-white transition-all duration-200 group"
            >
              <MessageSquare size={18} />
              <span className="text-sm font-medium">Conversations</span>
            </Link>
            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center gap-2.5 px-5 py-2.5 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl text-[#0a0a0a] hover:scale-105 active:scale-95 transition-all duration-200 shadow-lg shadow-emerald-500/20"
            >
              <Plus size={18} />
              <span className="text-sm font-semibold">Create New Bot</span>
            </button>
          </div>
        </div>

        {isCreating && (
          <div className="mb-8 p-6 bg-[#161616]/80 backdrop-blur-2xl border border-white/5 rounded-2xl shadow-2xl shadow-black">
            <form onSubmit={handleCreateBot} className="flex items-center gap-4">
              <input
                type="text"
                value={newBotName}
                onChange={(e) => setNewBotName(e.target.value)}
                placeholder="Enter your new bot's name..."
                className="flex-1 bg-white/[0.03] border border-white/10 rounded-xl px-5 py-3 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
                autoFocus
              />
              <button
                type="submit"
                className="px-6 py-3 bg-emerald-500 text-[#0a0a0a] font-semibold rounded-xl hover:bg-emerald-600 transition-colors shadow-md shadow-emerald-500/20"
              >
                Create Bot
              </button>
              <button
                type="button"
                onClick={() => setIsCreating(false)}
                className="px-6 py-3 bg-white/[0.03] text-white/60 rounded-xl hover:bg-white/[0.06] transition-colors"
              >
                Cancel
              </button>
            </form>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bots.map((bot) => (
            <Link
              key={bot.id}
              to={`/bot/${bot.id}`}
              className="block p-6 bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl hover:bg-white/[0.06] transition-all duration-200 group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl text-[#0a0a0a] shadow-lg shadow-emerald-500/10">
                  <MessageSquare size={24} />
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${
                    bot.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-white/5 text-white/40'
                  }`}>
                    {bot.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <button
                    onClick={(e) => handleDeleteBot(e, bot.id)}
                    className="p-1.5 text-white/30 hover:text-red-500 rounded-full hover:bg-red-500/10 transition-colors"
                    title="Delete Bot"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-1.5 group-hover:text-emerald-400 transition-colors">{bot.name}</h3>
              <p className="text-white/40 text-sm mb-4">
                Created {new Date(bot.created_at).toLocaleDateString()}
              </p>
              <div className="flex gap-4 mt-4 pt-4 border-t border-white/5">
                <div className="flex items-center gap-2 text-white/40 text-sm">
                  <Settings size={16} />
                  <span>Configure</span>
                </div>
                <div className="flex items-center gap-2 text-white/40 text-sm">
                  <BarChart size={16} />
                  <span>View Analytics</span>
                </div>
              </div>
            </Link>
          ))}
          
          {bots.length === 0 && !isCreating && (
            <div className="col-span-full text-center py-20 bg-[#161616]/60 backdrop-blur-xl border border-dashed border-white/10 rounded-2xl">
              <p className="text-white/40 mb-4">No bots found. Create your first bot to get started.</p>
              <button
                onClick={() => setIsCreating(true)}
                className="text-emerald-400 font-semibold hover:text-emerald-300 transition-colors"
              >
                + Create a Bot
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
