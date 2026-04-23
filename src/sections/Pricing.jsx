import React from 'react';
import { motion } from 'framer-motion';
import { Check, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const plans = [
  {
    name: "Free",
    price: "$0",
    description: "Perfect for testing and small projects.",
    features: [
      "1,000 Messages / month",
      "Standard AI Models",
      "Web Chat Widget",
      "Community Support"
    ],
    cta: "Start for Free",
    popular: false
  },
  {
    name: "Pro",
    price: "$49",
    description: "For growing businesses and developers.",
    features: [
      "50,000 Messages / month",
      "Premium AI Models (GPT-4)",
      "WhatsApp & Slack Integrations",
      "Priority Support"
    ],
    cta: "Start Pro Trial",
    popular: true
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "Custom solutions for large organizations.",
    features: [
      "Unlimited Messages",
      "Custom Model Training",
      "SLA & Dedicated Support",
      "On-premise Deployment"
    ],
    cta: "Contact Sales",
    popular: false
  }
];

export default function Pricing() {
  return (
    <section id="pricing" className="py-32 px-6 max-w-7xl mx-auto">
      <div className="text-center mb-20">
        <motion.p
           initial={{ opacity: 0, x: -20 }}
           whileInView={{ opacity: 1, x: 0 }}
           transition={{ duration: 0.6 }}
           className="text-accent-blue font-bold uppercase tracking-widest text-sm mb-4"
        >
          Pricing
        </motion.p>
        <motion.h2 
           initial={{ opacity: 0, y: 30 }}
           whileInView={{ opacity: 1, y: 0 }}
           transition={{ duration: 0.8 }}
           className="text-4xl md:text-5xl font-display font-bold mb-6"
        >
          Simple, <span className="text-gradient">Transparent</span> Pricing.
        </motion.h2>
        <p className="text-white/50 text-lg max-w-2xl mx-auto">
          Choose the plan that fits your needs. All plans include access to our visual flow builder.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {plans.map((plan, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: i * 0.1 }}
            className={`relative p-8 rounded-3xl border ${
              plan.popular ? 'border-accent-blue bg-accent-blue/5 shadow-[0_0_50px_rgba(59,130,246,0.1)]' : 'border-white/10 bg-white/[0.02]'
            } flex flex-col`}
          >
            {plan.popular && (
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-accent-blue text-white px-4 py-1 rounded-full text-xs font-bold uppercase tracking-widest">
                Most Popular
              </div>
            )}
            
            <div className="mb-8">
              <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-4xl font-bold">{plan.price}</span>
                {plan.price !== "Custom" && <span className="text-white/40">/month</span>}
              </div>
              <p className="text-white/50 text-sm">{plan.description}</p>
            </div>

            <ul className="space-y-4 mb-10 flex-1">
              {plan.features.map((feature, j) => (
                <li key={j} className="flex items-center gap-3 text-sm text-white/70">
                  <Check size={16} className="text-accent-blue" />
                  {feature}
                </li>
              ))}
            </ul>

            <Link to="/login" className={`w-full py-4 rounded-xl font-bold transition-all flex items-center justify-center gap-2 group ${
              plan.popular 
                ? 'bg-accent-blue text-white hover:bg-accent-blue/80' 
                : 'bg-white/5 border border-white/10 text-white hover:bg-white/10'
            }`}>
              {plan.cta}
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
