import React, { useState, useEffect } from 'react';
import { GitBranch, BookOpen, Clock } from 'lucide-react';

interface HeaderProps {
  systemStatus?: 'healthy' | 'degraded' | 'initializing' | 'offline';
}

export const Header: React.FC<HeaderProps> = ({ systemStatus = 'initializing' }) => {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = () => {
    switch (systemStatus) {
      case 'healthy':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            System Healthy
          </span>
        );
      case 'degraded':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-950/80 text-amber-400 border border-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Degraded / Setup Pending
          </span>
        );
      case 'offline':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-950/80 text-rose-400 border border-rose-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
            Backend Unreachable
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
            <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-pulse" />
            Probing Status
          </span>
        );
    }
  };

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Left: Branding & Tagline */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-teal-500/20 via-teal-500/40 to-emerald-400/20 border border-teal-500/40 flex items-center justify-center text-teal-400 shadow-sm shadow-teal-500/20">
            <GitBranch className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                CausalTrace
              </h1>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-teal-950 text-teal-300 border border-teal-800/60 uppercase tracking-wider">
                Graph Hacks
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              AI-Powered Incident Investigation Platform
            </p>
          </div>
        </div>

        {/* Right: Telemetry & Navigation */}
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 text-xs text-zinc-400 font-mono bg-zinc-900/60 px-3 py-1.5 rounded-md border border-zinc-800">
            <Clock className="w-3.5 h-3.5 text-zinc-500" />
            <span>{time || 'Loading time...'}</span>
          </div>

          <div className="flex items-center gap-2">
            {getStatusBadge()}
          </div>

          <div className="flex items-center gap-2 border-l border-zinc-800 pl-4">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="text-xs font-medium text-zinc-400 hover:text-teal-300 transition-colors flex items-center gap-1.5 px-2.5 py-1.5 rounded hover:bg-zinc-900"
              title="FastAPI Interactive Documentation"
            >
              <BookOpen className="w-3.5 h-3.5" />
              API Docs
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};
