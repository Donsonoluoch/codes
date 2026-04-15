import React from 'react';
import { ExternalLink, Mail, Code, Terminal, Zap } from 'lucide-react';

// Manually added GitHub icon
const Github = ({ size = 24, className = "" }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

// Manually added LinkedIn icon
const Linkedin = ({ size = 24, className = "" }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
    <rect width="4" height="12" x="2" y="9" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);

export default function Portfolio() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans selection:bg-blue-200">
      
      {/* Hero Section */}
      <header className="max-w-4xl mx-auto pt-24 pb-16 px-6">
        <div className="inline-block px-3 py-1 bg-gray-200 text-sm font-semibold rounded-full mb-6">
          Available for new opportunities
        </div>
        <h1 className="text-5xl font-extrabold tracking-tight mb-6">
          Hi, I'm Donson Oluoch. <br className="hidden md:block"/>
          <span className="text-gray-500">I build and own products end-to-end.</span>
        </h1>
        <p className="text-xl text-gray-600 mb-10 leading-relaxed max-w-2xl">
          I am a bias-to-action full-stack developer and AI-native thinker. 
          I don't just write code—I take projects from idea to impact, focusing on 
          rapid execution, great UX, and scalable architecture.
        </p>
        
        {/* Contact & Social Links */}
        <div className="flex flex-wrap gap-4">
          <a href="mailto:donsonoluoch@gmail.com" 
             className="flex items-center gap-2 bg-black text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-800 transition shadow-lg shadow-black/20">
            <Mail size={18} /> Get in Touch
          </a>
          <a href="https://github.com/Donsonoluoch/codes" target="_blank" rel="noreferrer"
             className="flex items-center gap-2 bg-white border border-gray-300 text-gray-800 px-6 py-3 rounded-lg font-medium hover:bg-gray-50 transition">
            <Github size={18} /> GitHub
          </a>
          <a href="https://www.linkedin.com/in/donson-oluoch-0042a5382/" target="_blank" rel="noreferrer"
             className="flex items-center gap-2 bg-[#0A66C2] text-white px-6 py-3 rounded-lg font-medium hover:bg-[#004182] transition shadow-lg shadow-[#0A66C2]/20">
            <Linkedin size={18} /> LinkedIn
          </a>
        </div>
      </header>

      {/* Philosophy / Mindset Section */}
      <section className="max-w-4xl mx-auto py-12 px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
            <Terminal className="text-blue-600 mb-4" size={28} />
            <h3 className="font-bold text-lg mb-2">Full-Stack Ownership</h3>
            <p className="text-gray-600 text-sm">I handle everything from server-side logic and databases to crafting clean UI components.</p>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
            <Zap className="text-yellow-500 mb-4" size={28} />
            <h3 className="font-bold text-lg mb-2">Bias to Action</h3>
            <p className="text-gray-600 text-sm">I iterate continuously. I don't wait for permission; I adapt, execute, and deliver results fast.</p>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
            <Code className="text-green-600 mb-4" size={28} />
            <h3 className="font-bold text-lg mb-2">AI-Native Workflow</h3>
            <p className="text-gray-600 text-sm">I actively use AI tools to automate workflows, scaffold faster, and enhance how I build products.</p>
          </div>
        </div>
      </section>

      {/* Featured Project Section */}
      <section className="max-w-4xl mx-auto py-16 px-6">
        <h2 className="text-3xl font-bold mb-8">Featured Work</h2>
        
        <div className="bg-white rounded-3xl border border-gray-200 overflow-hidden shadow-md flex flex-col md:flex-row">
          
          {/* Project Details */}
          <div className="p-8 md:w-1/2 flex flex-col justify-center">
            <div className="text-sm font-bold tracking-widest text-blue-600 uppercase mb-2">Idea to Impact</div>
            <h3 className="text-2xl font-bold mb-4">Codes Web App</h3>
            <p className="text-gray-600 mb-6">
              A modern web application built from scratch and deployed on Vercel. 
              This project demonstrates my ability to build clean user interfaces, manage application state, and ship a production-ready application independently.
            </p>
            
            <div className="flex flex-wrap gap-2 mb-8">
              <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-md font-medium">React</span>
              <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-md font-medium">Vercel</span>
              <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-md font-medium">Tailwind CSS</span>
            </div>

            <div className="flex gap-4">
              <a href="https://codes-q7r2.vercel.app/" target="_blank" rel="noreferrer"
                 className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition">
                <ExternalLink size={18} /> View Live App
              </a>
              <a href="https://github.com/Donsonoluoch/codes" target="_blank" rel="noreferrer"
                 className="flex items-center gap-2 text-gray-600 px-5 py-2.5 font-medium hover:text-black transition">
                Source Code
              </a>
            </div>
          </div>

          {/* Project Preview (Iframe) */}
          <div className="bg-gray-100 md:w-1/2 border-l border-gray-200 relative min-h-[300px]">
            <iframe 
              src="https://codes-q7r2.vercel.app/" 
              className="absolute inset-0 w-full h-full border-0 pointer-events-none"
              title="Project Preview"
              style={{ transform: 'scale(0.9)', transformOrigin: 'top center' }}
            ></iframe>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 mt-12 py-10 text-center text-gray-500">
        <p>© {new Date().getFullYear()} Donson Oluoch. Built with React & Tailwind. Deployed on Vercel.</p>
      </footer>
    </div>
  );
}