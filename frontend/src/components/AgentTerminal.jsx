import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

const AgentTerminal = ({ logs = [] }) => {
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="w-full bg-black/90 text-green-400 font-mono p-4 rounded-lg border border-green-500/30 shadow-[0_0_15px_rgba(0,255,0,0.1)] h-[300px] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between border-b border-green-500/20 pb-2 mb-2">
                <span className="text-xs uppercase tracking-widest text-green-600">Balance AI // Kernel v1.0</span>
                <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-red-500/50" />
                    <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
                    <div className="w-2 h-2 rounded-full bg-green-500/50" />
                </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 scrollbar-hide" ref={scrollRef}>
                <AnimatePresence>
                    {logs.length === 0 && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-green-800 italic"
                        >
                            Waiting for input...
                        </motion.div>
                    )}
                    {logs.map((log, i) => (
                        <motion.div
                            key={log.id || i}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.3 }}
                            className="text-sm"
                        >
                            <span className="text-green-600 mr-2">[{log.timestamp || new Date().toLocaleTimeString()}]</span>
                            <span className={cn(
                                log.action === 'simulation' ? "text-yellow-400" : "text-green-300"
                            )}>
                                {">"} {log.details}
                            </span>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            {/* Blinking Cursor */}
            <div className="mt-2 h-4 w-2 bg-green-500 animate-pulse" />
        </div>
    );
};

export default AgentTerminal;
