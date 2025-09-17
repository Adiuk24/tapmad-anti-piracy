"use client";
import React from 'react';

export default function Rows({ rows }: { rows: any[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Platform</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">URL</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Decision</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {rows.map((r) => (
            <Row key={r.id} r={r} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Row({ r }: { r: any }) {
  const [open, setOpen] = React.useState(false);
  const [evidence, setEvidence] = React.useState<any | null>(null);
  const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  const apiKey = process.env.NEXT_PUBLIC_API_KEY || 'change_this_token';

  async function loadEvidence() {
    try {
      const presigned = await fetch(`${apiBase}/detections/${r.id}/evidence`, { headers: { 'X-API-Key': apiKey } });
      if (!presigned.ok) return;
      const { url } = await presigned.json();
      const ev = await fetch(url);
      if (!ev.ok) return;
      setEvidence(await ev.json());
    } catch {}
  }

  async function trigger() {
    try {
      await fetch(`${apiBase}/detections/${r.id}/takedown`, { method: 'POST', headers: { 'X-API-Key': apiKey } });
    } catch {}
  }

  return (
    <>
      <tr className="cursor-pointer hover:bg-gray-50 transition-colors" onClick={() => { setOpen(!open); if (!evidence) loadEvidence(); }}>
        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{r.id}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            r.platform === 'youtube' ? 'bg-red-100 text-red-800' :
            r.platform === 'telegram' ? 'bg-blue-100 text-blue-800' :
            r.platform === 'facebook' ? 'bg-blue-100 text-blue-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {r.platform}
          </span>
        </td>
        <td className="px-6 py-4 text-sm text-gray-900 truncate max-w-xs">{r.title}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
          <a className="text-blue-600 hover:text-blue-800 underline" href={r.url} target="_blank" rel="noopener noreferrer">
            View
          </a>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(r.detected_at).toLocaleString()}</td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            Number(r.confidence) > 0.8 ? 'bg-green-100 text-green-800' :
            Number(r.confidence) > 0.5 ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            {Number(r.confidence).toFixed(2)}
          </span>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            r.decision === 'approve' ? 'bg-green-100 text-green-800' :
            r.decision === 'review' ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            {r.decision}
          </span>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            r.takedown_status === 'sent' ? 'bg-green-100 text-green-800' :
            r.takedown_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
            r.takedown_status === 'failed' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {r.takedown_status}
          </span>
        </td>
      </tr>
      {open && (
        <tr>
          <td colSpan={8} className="bg-gray-50">
            <div className="p-6">
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-sm font-medium text-gray-900">Evidence Details</h4>
                  <button 
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
                    onClick={trigger}
                  >
                    Trigger Takedown
                  </button>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-auto">
                  <pre className="text-xs text-gray-700">{evidence ? JSON.stringify(evidence, null, 2) : 'Loading evidence...'}</pre>
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}


export function ChatPanel() {
  type Msg = { role: 'user' | 'agent', text: string };
  const [log, setLog] = React.useState<Msg[]>([]);
  const [msg, setMsg] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  const apiKey = process.env.NEXT_PUBLIC_API_KEY || 'change_this_token';

  async function send() {
    const text = msg.trim();
    if (!text) return;
    setLog((l) => [...l, { role: 'user', text }]);
    setMsg("");
    setSending(true);
    try {
      const res = await fetch(`${apiBase}/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) {
        setLog((l) => [...l, { role: 'agent', text: `Error ${res.status}` }]);
        setSending(false);
        return;
      }
      const data = await res.json();
      setLog((l) => [...l, { role: 'agent', text: data.reply || '' }]);
    } catch (e) {
      setLog((l) => [...l, { role: 'agent', text: 'Network error' }]);
    }
    setSending(false);
  }

  return (
    <div className="h-full w-full flex flex-col bg-white">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-green-50 to-emerald-50">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
            <span className="text-green-400 font-bold text-sm tracking-wide">tapmad</span>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Tapmad Anti-Piracy Agent</h2>
            <p className="text-sm text-gray-500">Chat with the AI agent to control the system</p>
          </div>
        </div>
      </div>
      
      {/* Messages area */}
      <div className="flex-1 overflow-auto p-8 space-y-4 bg-gray-50">
        {log.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-sm">Start by asking the agent to scan for pirated content</p>
          </div>
        )}
        {log.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`${m.role === 'user' ? 'bg-black text-white' : 'bg-white text-gray-900 border border-gray-200'} rounded-2xl px-4 py-3 max-w-[90%] shadow-sm text-sm leading-relaxed`}>
              {m.text}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-500 border border-gray-200 rounded-2xl px-4 py-3 text-sm shadow-sm flex items-center">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Quick actions */}
      <div className="px-6 py-4 border-t border-gray-200 bg-white">
        <div className="flex flex-wrap gap-2">
          {[
            { t: 'Scan YouTube', m: 'scan YouTube now', icon: '🎥' },
            { t: 'Scan Telegram', m: 'scan Telegram 20', icon: '📱' },
            { t: 'Report 24h', m: 'report 24h', icon: '📊' },
            { t: 'Set Threshold 10', m: 'set threshold 10', icon: '⚙️' },
          ].map((q, i) => (
            <button
              key={i}
              className="flex items-center space-x-2 px-4 py-2 rounded-full border border-gray-300 text-sm hover:bg-green-50 hover:border-green-400 hover:text-green-700 transition-colors"
              onClick={() => { setMsg(q.m); }}
            >
              <span>{q.icon}</span>
              <span>{q.t}</span>
            </button>
          ))}
        </div>
      </div>
      
      {/* Input area */}
      <div className="px-6 py-4 border-t border-gray-200 bg-white">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <input
              className="w-full bg-gray-100 border-0 rounded-full px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:bg-white transition-all"
              placeholder="Type a command, e.g., scan YouTube now"
              value={msg}
              onChange={(e) => setMsg(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') send(); }}
            />
            <button 
              className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1.5 rounded-full bg-black text-white hover:bg-gray-800 transition-colors disabled:opacity-50" 
              onClick={send} 
              disabled={sending || !msg.trim()}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}


