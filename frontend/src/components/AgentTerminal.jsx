import React, { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/utils';
import { Send, Terminal } from 'lucide-react';

const AgentTerminal = ({ logs = [] }) => {
    const scrollRef = useRef(null);
    const [query, setQuery] = useState("");
    const [chatMessages, setChatMessages] = useState([]);
    const [isTyping, setIsTyping] = useState(false);

    // System logs from backend + chat messages (separate streams, no duplication)
    const allItems = [
        ...logs.map(l => ({ ...l, type: 'system' })),
        ...chatMessages
    ];

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs, chatMessages, isTyping]);

    const handleCommand = async (e) => {
        e.preventDefault();
        if (!query.trim() || isTyping) return;

        const userMsg = {
            id: Date.now(),
            type: 'user',
            text: query,
            timestamp: new Date().toLocaleTimeString()
        };

        setChatMessages(prev => [...prev, userMsg]);
        setQuery("");
        setIsTyping(true);

        try {
            const res = await fetch('/api/agent/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: userMsg.text })
            });
            const data = await res.json();

            if (data.status === 'success' && data.response) {
                setChatMessages(prev => [...prev, {
                    id: Date.now() + 1,
                    type: 'agent',
                    text: data.response,
                    timestamp: new Date().toLocaleTimeString()
                }]);
            } else {
                setChatMessages(prev => [...prev, {
                    id: Date.now() + 1,
                    type: 'error',
                    text: data.detail || "No response received",
                    timestamp: new Date().toLocaleTimeString()
                }]);
            }
        } catch (err) {
            setChatMessages(prev => [...prev, {
                id: Date.now() + 1,
                type: 'error',
                text: "Connection failed: " + err.message,
                timestamp: new Date().toLocaleTimeString()
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="w-full bg-neutral-900 rounded-xl border border-neutral-800 shadow-xl overflow-hidden flex flex-col h-[500px]">
            {/* Header */}
            <div className="bg-neutral-950 p-3 border-b border-neutral-800 flex justify-between items-center">
                <div className="flex items-center gap-2 text-green-500">
                    <Terminal className="h-4 w-4" />
                    <span className="text-xs font-bold uppercase tracking-wider">Balance AI Agent</span>
                </div>
                <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/50" />
                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/50 animate-pulse" />
                </div>
            </div>

            {/* Message Feed */}
            <div className="flex-1 bg-black/50 p-4 overflow-y-auto text-sm space-y-3" ref={scrollRef}>
                {allItems.length === 0 && !isTyping && (
                    <div className="text-neutral-500 italic text-center mt-10">
                        <p>System Online. Ask me anything.</p>
                        <p className="text-xs mt-2 text-neutral-600">Try: "What's our total spending?" or "List vendors"</p>
                    </div>
                )}

                {/* System logs */}
                {allItems.filter(i => i.type === 'system').map((log, i) => (
                    <div key={`sys-${i}`} className="text-neutral-500 text-xs border-l-2 border-neutral-700 pl-2 font-mono">
                        <span className="text-neutral-600">[{log.timestamp || "SYS"}]</span> {log.details}
                    </div>
                ))}

                {/* Chat messages */}
                {chatMessages.map((msg, i) => (
                    <div key={`chat-${msg.id}`} className={cn(
                        "flex",
                        msg.type === 'user' ? "justify-end" : "justify-start"
                    )}>
                        <div className={cn(
                            "max-w-[85%] p-3 rounded-lg border text-sm",
                            msg.type === 'user'
                                ? "bg-neutral-800 border-neutral-700 text-white rounded-br-none"
                                : msg.type === 'agent'
                                    ? "bg-green-500/10 border-green-500/20 text-green-300 rounded-bl-none"
                                    : "bg-red-500/10 border-red-500/20 text-red-400 rounded-bl-none"
                        )}>
                            <div className="whitespace-pre-wrap leading-relaxed">
                                {msg.text}
                            </div>
                        </div>
                    </div>
                ))}

                {isTyping && (
                    <div className="flex justify-start">
                        <div className="bg-green-500/10 border border-green-500/20 text-green-500 p-3 rounded-lg text-xs animate-pulse">
                            Analyzing your ledger data...
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="p-3 bg-neutral-900 border-t border-neutral-800">
                <form onSubmit={handleCommand} className="flex gap-2">
                    <input
                        className="flex-1 bg-neutral-950 border border-neutral-700 rounded-lg px-4 py-3 text-white text-sm placeholder-neutral-500 focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500 transition-all"
                        placeholder="Ask about your finances..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        disabled={isTyping}
                    />
                    <button
                        type="submit"
                        disabled={!query.trim() || isTyping}
                        className="bg-green-600 hover:bg-green-500 text-black font-bold p-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="h-5 w-5" />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default AgentTerminal;
