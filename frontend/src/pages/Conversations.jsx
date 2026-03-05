import { useState, useEffect } from 'react';
import { getConversations, getConversation, getBots } from '../api/client';
import { MessageSquare, Bot, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const formatDate = (dateString) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleString();
};

export default function Conversations() {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  
  // Filters
  const [filters, setFilters] = useState({
    chatbot_id: '',
    visitor_identifier: '',
    session_id: '',
    start_date: '',
    end_date: '',
    is_preview: '' 
  });

  useEffect(() => {
    fetchBots();
    fetchConversations();
  }, []);

  const fetchBots = async () => {
    try {
      const res = await getBots();
      setBots(res.data);
    } catch (err) {
      console.error("Failed to fetch bots", err);
    }
  };

  const fetchConversations = async () => {
    setLoading(true);
    try {
      // Clean filters
      const params = {};
      Object.keys(filters).forEach(key => {
        if (filters[key]) params[key] = filters[key];
      });
      
      const res = await getConversations(params);
      // Handle different response structures (pagination vs list)
      const data = res.data.results ? res.data.results : res.data;
      setConversations(data); 
      
    } catch (err) {
      console.error("Failed to fetch conversations", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectConversation = async (id) => {
    setLoadingDetails(true);
    try {
      const res = await getConversation(id);
      setSelectedConversation(res.data);
    } catch (err) {
      console.error("Failed to fetch conversation details", err);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const applyFilters = (e) => {
    e.preventDefault();
    fetchConversations();
    setSelectedConversation(null);
  };

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-white font-sans">
       {/* Sidebar / List */}
       <div className={`w-full md:w-1/3 flex flex-col border-r border-white/10 bg-[#161616]/60 backdrop-blur-xl ${selectedConversation ? 'hidden md:flex' : 'flex'}`}>
          <div className="p-4 border-b border-white/10">
             <div className="flex justify-between items-center mb-4">
               <h1 className="text-2xl font-semibold text-white tracking-tight">Conversations</h1>
               <Link to="/" className="text-sm text-emerald-400 hover:text-emerald-300 transition-colors">Back to Dashboard</Link>
             </div>
             
             {/* Filter Form */}
             <form onSubmit={applyFilters} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                   <select 
                      name="chatbot_id" 
                      value={filters.chatbot_id} 
                      onChange={handleFilterChange}
                      className="w-full p-2.5 text-sm bg-white/[0.03] border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
                   >
                      <option value="">All Bots</option>
                      {bots.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                   </select>
                   <input 
                      type="text" 
                      name="visitor_identifier" 
                      placeholder="Visitor ID" 
                      value={filters.visitor_identifier} 
                      onChange={handleFilterChange}
                      className="w-full p-2.5 text-sm bg-white/[0.03] border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300 placeholder:text-white/20"
                   />
                </div>
                <div className="grid grid-cols-2 gap-3">
                   <div className="flex flex-col">
                       <label className="text-xs text-white/40 mb-1.5 ml-1">Start Date</label>
                       <input 
                          type="date" 
                          name="start_date" 
                          value={filters.start_date} 
                          onChange={handleFilterChange}
                          className="w-full p-2.5 text-sm bg-white/[0.03] border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
                       />
                   </div>
                   <div className="flex flex-col">
                       <label className="text-xs text-white/40 mb-1.5 ml-1">End Date</label>
                       <input 
                          type="date" 
                          name="end_date" 
                          value={filters.end_date} 
                          onChange={handleFilterChange}
                          className="w-full p-2.5 text-sm bg-white/[0.03] border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
                       />
                   </div>
                </div>
                <button type="submit" className="w-full py-2.5 bg-emerald-500 text-[#0a0a0a] rounded-xl text-sm font-semibold hover:bg-emerald-600 transition-colors shadow-md shadow-emerald-500/20">
                   Apply Filters
                </button>
             </form>
          </div>
          
          <div className="flex-1 overflow-y-auto">
             {loading ? (
                <div className="p-4 text-center text-white/40">Loading...</div>
             ) : conversations.length === 0 ? (
                <div className="p-4 text-center text-white/40">No conversations found.</div>
             ) : (
                <div className="divide-y divide-white/5">
                   {conversations.map(conv => (
                      <div 
                         key={conv.id} 
                         onClick={() => handleSelectConversation(conv.id)}
                         className={`p-4 cursor-pointer hover:bg-white/[0.03] transition-colors ${
                            selectedConversation?.id === conv.id ? 'bg-emerald-500/10 border-l-4 border-emerald-400' : 'border-l-4 border-transparent'
                         }`}
                      >
                         <div className="flex justify-between items-start mb-1">
                            <span className="font-medium text-white/90 truncate" title={conv.visitor_identifier}>
                                {conv.visitor_identifier}
                            </span>
                            <span className="text-xs text-white/40 whitespace-nowrap ml-2">{formatDate(conv.started_at)}</span>
                         </div>
                         <div className="flex justify-between items-center text-sm text-white/50">
                            <div className="flex items-center gap-1.5">
                               <Bot size={14} />
                               <span>{conv.chatbot?.name}</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                               <MessageSquare size={14} />
                               <span>{conv.message_count} msgs</span>
                            </div>
                         </div>
                      </div>
                   ))}
                </div>
             )}
          </div>
       </div>

       {/* Detail View */}
       <div className={`w-full md:w-2/3 flex flex-col bg-[#0a0a0a] ${!selectedConversation ? 'hidden md:flex' : 'flex'}`}>
          {selectedConversation ? (
             <>
                {/* Header */}
                <div className="p-4 border-b border-white/10 flex justify-between items-center bg-[#161616]/60 backdrop-blur-xl shadow-sm z-10">
                   <div className="flex items-center gap-3">
                      <button onClick={() => setSelectedConversation(null)} className="md:hidden p-2 hover:bg-white/10 rounded-full transition-colors">
                         <ArrowRight className="rotate-180" size={20} />
                      </button>
                      <div>
                         <h2 className="font-bold text-white/90 text-lg">{selectedConversation.visitor_identifier}</h2>
                         <div className="text-sm text-white/50 flex flex-wrap gap-x-4">
                            <span>Session: {selectedConversation.session_id}</span>
                            <span>Bot: {selectedConversation.chatbot?.name}</span>
                            {selectedConversation.is_preview && <span className="text-amber-400 bg-amber-500/10 px-2 rounded-full text-xs py-0.5">Preview Mode</span>}
                         </div>
                      </div>
                   </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                   {loadingDetails ? (
                      <div className="text-center py-10 text-white/40">Loading messages...</div>
                   ) : selectedConversation.messages.map((msg) => (
                      <div key={msg.id} className={`flex items-end gap-2.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                         {msg.sender !== 'user' && <div className="w-8 h-8 rounded-full bg-[#161616] border border-white/10 flex items-center justify-center shrink-0 shadow-sm text-emerald-400"><Bot size={16} /></div>}
                         <div className={`max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-3 shadow-sm ${
                            msg.sender === 'user' 
                               ? 'bg-emerald-500 text-[#0a0a0a] rounded-br-none' 
                               : 'bg-[#1c1c1c] text-white/80 rounded-bl-none border border-white/10'
                         }`}>
                            <div className="whitespace-pre-wrap text-sm leading-relaxed font-light">{msg.content}</div>
                            <div className={`text-xs mt-2 flex gap-3 ${msg.sender === 'user' ? 'text-black/50' : 'text-white/30'}`}>
                               <span>{new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                               {msg.latency && <span>{Math.round(msg.latency)}ms</span>}
                               {msg.source && <span className="uppercase text-[10px] tracking-wider border border-current px-1 rounded">{msg.source}</span>}
                            </div>
                         </div>
                      </div>
                   ))}
                   {selectedConversation.messages.length === 0 && (
                       <div className="text-center text-white/30 py-10">No messages in this conversation.</div>
                   )}
                </div>
             </>
          ) : (
             <div className="flex-1 flex flex-col items-center justify-center text-white/40">
                <div className="bg-[#161616]/60 backdrop-blur-xl border border-white/5 p-6 rounded-full shadow-2xl mb-4">
                    <MessageSquare size={48} className="opacity-40 text-emerald-400" />
                </div>
                <p className="text-lg font-medium text-white/50">Select a conversation to view details</p>
             </div>
          )}
       </div>
    </div>
  );
}
