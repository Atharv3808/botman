import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { signup } from '../api/client';
import { ArrowRight, Chrome, Twitter } from 'lucide-react';

export default function Signup() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await signup({ username, email, password });
      navigate('/login');
    } catch {
      setError('Failed to create account. Username might be taken.');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0a0a] font-sans selection:bg-emerald-500/30">
      {/* Background Glow */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/10 blur-[120px] rounded-full" />
      </div>

      <div className="relative w-full max-w-[440px] px-6">
        <div className="bg-[#161616]/80 backdrop-blur-2xl border border-white/5 rounded-[40px] p-10 shadow-2xl shadow-black">
          {/* Top Glow Effect */}
          <div className="absolute top-0 left-10 w-20 h-20 bg-emerald-400/20 blur-[40px] rounded-full" />
          
          <div className="text-center mb-10">
            <h1 className="text-4xl font-semibold text-white tracking-tight mb-2">
              Create <span className="text-white/60 font-normal">account</span>
            </h1>
            <p className="text-white/40 text-sm">Join the Botman community</p>
          </div>

          {error && (
            <div className="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-center text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-4">
              <div className="relative group">
                <label className="block text-[11px] font-medium text-white/40 uppercase tracking-widest mb-1.5 ml-4">
                  Username
                </label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    className="w-full bg-white/[0.03] border border-white/10 rounded-2xl px-5 py-4 text-white placeholder:text-white/10 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
                    placeholder="botman_dev"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                  />
                </div>
              </div>

              <div className="relative group">
                <label className="block text-[11px] font-medium text-white/40 uppercase tracking-widest mb-1.5 ml-4">
                  Email
                </label>
                <div className="relative">
                  <input
                    type="email"
                    required
                    className="w-full bg-white/[0.03] border border-white/10 rounded-2xl px-5 py-4 text-white placeholder:text-white/10 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
                    placeholder="name@domain.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div className="relative group">
                <label className="block text-[11px] font-medium text-white/40 uppercase tracking-widest mb-1.5 ml-4">
                  Password
                </label>
                <div className="relative">
                  <input
                    type="password"
                    required
                    className="w-full bg-white/[0.03] border border-white/10 rounded-2xl px-5 py-4 text-white placeholder:text-white/10 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button
                    type="submit"
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center text-[#0a0a0a] hover:scale-105 active:scale-95 transition-all duration-200 shadow-lg shadow-emerald-500/20"
                  >
                    <ArrowRight size={20} />
                  </button>
                </div>
              </div>
            </div>
          </form>

          <div className="mt-10 text-center">
            <p className="text-white/40 text-sm">
              Already have an account?{' '}
              <Link to="/login" className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
