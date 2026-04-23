import React from 'react';
import { Bot, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex justify-center p-6">
      <motion.div 
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1.2, ease: [0.1, 1, 0.5, 1] }}
        className="antigravity-pill px-8 py-3 rounded-full flex items-center justify-between w-full max-w-6xl shadow-[0_0_50px_rgba(59,130,246,0.1)]"
      >
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-accent-blue/10 rounded-lg border border-accent-blue/20">
            <Bot size={24} className="text-accent-blue" />
          </div>
          <span className="font-display text-xl font-bold tracking-tight">Botman</span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-white/70">
          <a href="#features" className="hover:text-white transition-colors">Features</a>
          <a href="#workflow" className="hover:text-white transition-colors">Workflow</a>
          <a href="#demo" className="hover:text-white transition-colors">Demo</a>
          <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
        </div>

        <div>
          <Link to="/login" className="group relative flex items-center gap-2 bg-white text-black px-6 py-2.5 rounded-full font-bold text-sm transition-all hover:scale-105 active:scale-95 button-glow">
            Get Started
            <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
            <div className="absolute inset-0 rounded-full bg-accent-blue blur-xl opacity-0 group-hover:opacity-40 transition-opacity -z-10" />
          </Link>
        </div>
      </motion.div>
    </nav>
  );
}
