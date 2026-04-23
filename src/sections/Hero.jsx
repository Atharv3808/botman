import React, { useRef, useEffect } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';
import FloatingNodes from '../components/FloatingNodes';
import { Sparkles, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Hero() {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const handleMouseMove = (e) => {
    const { clientX, clientY } = e;
    const moveX = clientX - window.innerWidth / 2;
    const moveY = clientY - window.innerHeight / 2;
    mouseX.set(moveX);
    mouseY.set(moveY);
  };

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center pt-32 pb-20 px-6 overflow-hidden">
      <FloatingNodes mouseX={mouseX} mouseY={mouseY} />
      
      <div className="relative z-10 text-center max-w-4xl mx-auto">
        <motion.div
           initial={{ opacity: 0, y: 20 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ duration: 0.6 }}
           className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-blue/10 border border-accent-blue/20 text-accent-blue text-sm font-medium mb-8"
        >
          <Sparkles size={14} />
          <span>The Next Generation of AI Bot Building</span>
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-6xl md:text-8xl font-display font-bold leading-tight mb-8"
        >
          Build <span className="text-gradient">Intelligent</span> Bots.<br />
          Defy Limits.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="text-xl text-white/60 mb-12 max-w-2xl mx-auto leading-relaxed"
        >
          The first visual-logic platform designed for the AI native era. 
          Connect nodes, train models, and deploy production-ready bots in clicks. 
          Join 10,000+ developers building the future of automated intelligence.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="flex flex-wrap items-center justify-center gap-6"
        >
          <Link to="/login" className="bg-botman-glow p-[1px] rounded-full group button-glow">
            <div className="bg-[#050505] group-hover:bg-transparent transition-all px-10 py-4 rounded-full flex items-center gap-2 font-bold text-lg text-white">
              Start Building 
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
          
          <button className="px-10 py-4 rounded-full font-bold text-lg border border-white/20 hover:bg-white/10 hover:border-white/40 transition-all text-white backdrop-blur-sm">
            View Demo
          </button>
        </motion.div>
      </div>

      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-bounce opacity-60">
        <div className="w-6 h-10 rounded-full border-2 border-accent-blue/50 flex justify-center p-1">
          <div className="w-1.5 h-1.5 bg-accent-blue rounded-full" />
        </div>
      </div>
    </section>
  );
}
