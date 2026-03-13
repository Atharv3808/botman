import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login, googleLogin } from '../api/client';
import { ArrowRight, Chrome, Github } from 'lucide-react';
import { auth, googleProvider } from '../firebase';
import { signInWithPopup } from 'firebase/auth';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleGoogleLogin = async () => {
    setError('');
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const idToken = await result.user.getIdToken();
      const response = await googleLogin(idToken);
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      navigate('/');
    } catch (err) {
      console.error(err);
      setError('Google Sign-In failed. Please try again.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await login({ username, password });
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      navigate('/');
    } catch {
      setError('Invalid credentials');
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
              Welcome <span className="text-white/60 font-normal">back</span>
            </h1>
            <p className="text-white/40 text-sm">Sign in to your account</p>
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
                    placeholder="username@gmail.com"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
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

          <div className="relative my-10">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/5"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-[#161616] px-4 text-white/20 tracking-widest font-medium">OR</span>
            </div>
          </div>

          <div className="space-y-3">
            <button 
              onClick={handleGoogleLogin}
              className="w-full flex items-center justify-between bg-white/[0.03] border border-white/10 rounded-2xl px-5 py-4 text-white/70 hover:bg-white/[0.06] hover:text-white transition-all duration-200 group"
            >
              <div className="flex items-center gap-4">
                <div className="w-6 h-6 flex items-center justify-center text-white/60">
                  <Chrome size={20} />
                </div>
                <span className="text-sm font-medium">Continue with Google</span>
              </div>
              <ArrowRight size={16} className="text-white/20 group-hover:text-white/60 transition-colors" />
            </button>
          </div>

          <div className="mt-10 text-center">
            <p className="text-white/40 text-sm">
              Don't have an account?{' '}
              <Link to="/signup" className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
