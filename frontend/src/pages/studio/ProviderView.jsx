import { Shield } from 'lucide-react';

export default function ProviderView() {
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-10">
        <h2 className="text-3xl font-semibold text-white tracking-tight">Provider <span className="text-white/60 font-normal">Configuration</span></h2>
        <p className="text-white/40 mt-1">Manage LLM providers and API keys.</p>
      </div>
      
      <div className="bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl p-12 text-center flex flex-col items-center">
        <div className="inline-flex p-5 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full text-[#0a0a0a] mb-6 shadow-lg shadow-emerald-500/10">
          <Shield size={32} />
        </div>
        <h3 className="text-xl font-semibold text-white/90 mb-2">Provider Settings Coming Soon</h3>
        <p className="text-white/40 max-w-md mx-auto">
          Currently, the system uses the globally configured OpenAI provider. Custom provider settings per bot will be available in a future update.
        </p>
      </div>
    </div>
  );
}
