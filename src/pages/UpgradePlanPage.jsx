import React from 'react';

const UpgradePlanPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black text-white flex flex-col items-center justify-center p-8">
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold mb-4">Choose Your Plan</h1>
        <p className="text-xl text-gray-400">Unlock more features and create more bots by upgrading your plan.</p>
      </div>
      <div className="grid md:grid-cols-2 gap-8 max-w-4xl w-full">
        <div className="bg-gray-800 p-8 rounded-2xl shadow-lg border border-gray-700 transform hover:scale-105 transition-transform duration-300">
          <h2 className="text-3xl font-bold mb-4">Pro Plan</h2>
          <p className="text-5xl font-bold mb-6">$10<span className="text-xl font-normal text-gray-400">/mo</span></p>
          <ul className="space-y-4 text-lg mb-8">
            <li className="flex items-center"><span className="text-green-400 mr-2">✔</span> 10 bots</li>
            <li className="flex items-center"><span className="text-green-400 mr-2">✔</span> 10,000 messages/mo</li>
            <li className="flex items-center"><span className="text-green-400 mr-2">✔</span> Email support</li>
          </ul>
          <button className="w-full bg-green-500 text-white font-bold py-3 rounded-lg hover:bg-green-600 transition-colors duration-300">Upgrade to Pro</button>
        </div>
        <div className="bg-gray-800 p-8 rounded-2xl shadow-lg border border-gray-700 transform hover:scale-105 transition-transform duration-300">
          <h2 className="text-3xl font-bold mb-4">Enterprise Plan</h2>
          <p className="text-5xl font-bold mb-6">Contact Us</p>
          <ul className="space-y-4 text-lg mb-8">
            <li className="flex items-center"><span className="text-green-400 mr-2">✔</span> Unlimited bots</li>
            <li className="flex items-center"><span className="text-green-400 mr-2">✔</span> Unlimited messages</li>
            <li className="flex items-center"><span className="text-green-400 mr-2">✔</span> Dedicated support</li>
          </ul>
          <button className="w-full bg-blue-500 text-white font-bold py-3 rounded-lg hover:bg-blue-600 transition-colors duration-300">Contact Sales</button>
        </div>
      </div>
    </div>
  );
};

export default UpgradePlanPage;
