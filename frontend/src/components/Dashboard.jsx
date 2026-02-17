import React, { useState, useEffect, useRef } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Upload, AlertTriangle, CheckCircle, Wallet, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import AgentTerminal from './AgentTerminal';
import VoiceCommand from './VoiceCommand';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

// Initial Budget (Default)
const DEFAULT_BUDGET = 50000;

const API_URL = "/api";

const Dashboard = () => {
    const [logs, setLogs] = useState([]);
    const [ledger, setLedger] = useState([]);
    const [agentStatus, setAgentStatus] = useState("checking");
    const [file, setFile] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [budget, setBudget] = useState(DEFAULT_BUDGET);
    const [isEditingBudget, setIsEditingBudget] = useState(false);
    const fileInputRef = useRef(null);

    // Derived KPIs
    const totalSpent = ledger.reduce((acc, item) => {
        const amount = parseFloat(String(item.amount).replace(/[^0-9.-]+/g, ""));
        return acc + (isNaN(amount) ? 0 : amount);
    }, 0);

    // Dynamic Burn Rate (Avg Daily Spend * 30)
    // 1. Group by Date
    const dailySpend = ledger.reduce((acc, item) => {
        const date = item.date;
        const amount = parseFloat(String(item.amount).replace(/[^0-9.-]+/g, ""));
        if (!isNaN(amount)) {
            acc[date] = (acc[date] || 0) + amount;
        }
        return acc;
    }, {});

    // 2. Format for Chart
    const burnRateData = Object.keys(dailySpend)
        .sort() // Sort by date
        .slice(-7) // Last 7 days
        .map(date => ({
            name: new Date(date).toLocaleDateString('en-US', { weekday: 'short' }),
            amount: dailySpend[date]
        }));

    // If no data, show empty placeholder or just 0
    if (burnRateData.length === 0) {
        burnRateData.push({ name: 'Today', amount: 0 });
    }

    // 3. Calculate Burn Rate (Monthly Projection)
    const daysTracked = Object.keys(dailySpend).length || 1;
    const avgDaily = totalSpent / daysTracked;
    const projectedBurn = avgDaily * 30;

    const cashOnHand = budget - totalSpent;
    const pendingCount = ledger.filter(i => i.status === "Pending").length;

    // Initial Fetch & Polling
    useEffect(() => {
        fetchLedger();
        checkAgentHealth();

        const interval = setInterval(async () => {
            fetchLogs();
            checkAgentHealth();
        }, 3000); // Poll every 3s
        return () => clearInterval(interval);
    }, []);

    const fetchLedger = async () => {
        try {
            const res = await fetch(`${API_URL}/ledger`);
            const data = await res.json();
            if (data.status === "success") {
                setLedger(data.data);
            }
        } catch (e) {
            console.error("Failed to fetch ledger", e);
        }
    };

    const fetchLogs = async () => {
        try {
            const res = await fetch(`${API_URL}/agent/status`);
            const data = await res.json();
            if (data.logs) setLogs(data.logs);
        } catch (e) {
            console.error("Polling logs failed", e);
        }
    }

    const checkAgentHealth = async () => {
        try {
            const res = await fetch(`${API_URL}/agent/health`);
            const data = await res.json();

            const visionActive = data.components?.vision === "active";
            const dbActive = data.components?.database === "active";

            console.log("Health Data:", data);

            if (visionActive && dbActive) {
                setAgentStatus("active");
            } else if (visionActive || dbActive) {
                setAgentStatus("limited");
            } else {
                console.warn("Agent Offline Logic Triggered", { visionActive, dbActive });
                setAgentStatus("offline"); // Or inactive
            }
        } catch (e) {
            console.error("Agent Health Check Failed:", e);
            setAgentStatus("offline");
        }
    };

    const handleFileUpload = async (e) => {
        const selectedFile = e.target.files?.[0];
        if (!selectedFile) return;

        setFile(selectedFile);
        setIsProcessing(true);

        // Simulate immediate feedback
        setLogs(prev => [...prev, { id: Date.now(), details: `Uploading ${selectedFile.name}...`, action: "upload" }]);

        const formData = new FormData();
        formData.append("file", selectedFile);

        try {
            const res = await fetch(`${API_URL}/upload`, {
                method: "POST",
                body: formData
            });
            const data = await res.json();

            if (data.status === "success") {
                if (data.status === "success") {
                    // Refresh ledger from backend instead of local append to ensure sync
                    fetchLedger();
                }
            }
        } catch (err) {
            console.error(err);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleVoiceCommand = async (text) => {
        console.log("Voice Command:", text);
        // Hacky Voice Logic
        if (text.toLowerCase().includes("upload")) {
            fileInputRef.current?.click();
        }
        if (text.toLowerCase().includes("risk") || text.toLowerCase().includes("audit")) {
            await fetch(`${API_URL}/agent/run`, { method: "POST" });
        }
        if (text.toLowerCase().includes("email")) {
            await fetch(`${API_URL}/simulation/event`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ type: "email", details: "Drafted email to Client X" })
            });
        }
    };

    const handleCreateInvoice = async () => {
        await fetch(`${API_URL}/simulation/event`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type: "invoice", details: "Generated new invoice #INV-2024-001 for $1,500" })
        });
        // Poll immediately to show log
        fetchLogs();
    };

    const handleFreezeSpending = async () => {
        await fetch(`${API_URL}/simulation/event`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type: "alert", details: "⛔ SPENDING FROZEN via Manual Override" })
        });
        fetchLogs();
    };

    return (
        <div className="min-h-screen bg-neutral-950 text-white p-8 font-sans">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-neutral-400 bg-clip-text text-transparent">
                        Balance AI
                    </h1>
                    <p className="text-neutral-400">Autonomous Financial Controller</p>
                </div>
                <div className="flex gap-4">
                    <Button variant="outline" className="text-black border-neutral-800 hover:bg-neutral-900 hover:text-white transition-colors"
                        onClick={() => fetch(`${API_URL}/agent/run`, { method: "POST" })}
                    >
                        <Activity className="mr-2 h-4 w-4" /> Run Audit
                    </Button>
                    <div className={cn(
                        "flex items-center gap-2 px-4 py-2 rounded-full border transition-colors",
                        agentStatus === "active" ? "bg-green-500/10 border-green-500/20" :
                            agentStatus === "limited" ? "bg-yellow-500/10 border-yellow-500/20" : "bg-red-500/10 border-red-500/20"
                    )}>
                        <div className={cn(
                            "w-2 h-2 rounded-full animate-pulse",
                            agentStatus === "active" ? "bg-green-500" :
                                agentStatus === "limited" ? "bg-yellow-500" : "bg-red-500"
                        )} />
                        <span className={cn(
                            "text-sm font-medium",
                            agentStatus === "active" ? "text-green-500" :
                                agentStatus === "limited" ? "text-yellow-500" : "text-red-500"
                        )}>
                            {agentStatus === "active" ? "Agent Active" :
                                agentStatus === "limited" ? "Partial Mode" : "Agent Offline"}
                        </span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-8">
                {/* Left Column: Dashboard & Chart */}
                <div className="col-span-8 space-y-8">
                    {/* KPI Cards */}
                    <div className="grid grid-cols-3 gap-4">
                        {[
                            { label: "Cash on Hand", value: `₹${cashOnHand.toLocaleString()}`, icon: Wallet, color: "text-white" },
                            { label: "Projected Burn (Mo)", value: `₹${Math.round(projectedBurn).toLocaleString()}`, icon: Activity, color: "text-red-400" },
                            { label: "Pending Invoices", value: pendingCount, icon: AlertTriangle, color: "text-yellow-400" },
                        ].map((kpi, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.1 }}
                                className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl"
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <span className="text-neutral-500 text-sm font-medium">{kpi.label}</span>
                                    <kpi.icon className={cn("h-5 w-5", kpi.color)} />
                                </div>
                                <div className="text-2xl font-bold flex items-center gap-2">
                                    {kpi.label === "Cash on Hand" ? (
                                        isEditingBudget ? (
                                            <input
                                                type="number"
                                                className="bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-sm w-32 text-white"
                                                value={budget}
                                                onChange={(e) => setBudget(parseFloat(e.target.value))}
                                                onBlur={() => setIsEditingBudget(false)}
                                                autoFocus
                                            />
                                        ) : (
                                            <span onClick={() => kpi.label === "Cash on Hand" && setIsEditingBudget(true)} className="cursor-pointer hover:underline decoration-dashed decoration-neutral-600 underline-offset-4" title="Click to edit starting balance">
                                                {kpi.value}
                                            </span>
                                        )
                                    ) : (
                                        kpi.value
                                    )}
                                </div>
                            </motion.div>
                        ))}
                    </div>

                    {/* Chart Area */}
                    <div className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl h-[300px]">
                        <h3 className="text-lg font-medium mb-4">Cash Flow Velocity</h3>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={burnRateData}>
                                <defs>
                                    <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                <XAxis dataKey="name" stroke="#666" />
                                <YAxis stroke="#666" />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#171717', border: '1px solid #333' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Area type="monotone" dataKey="amount" stroke="#22c55e" fillOpacity={1} fill="url(#colorAmount)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Ledger Table */}
                    <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
                        <div className="p-6 border-b border-neutral-800 flex justify-between items-center">
                            <h3 className="text-lg font-medium">Recent Transactions</h3>
                            <div className="relative">
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    className="hidden"
                                    onChange={handleFileUpload}
                                    accept="image/*,application/pdf"
                                />
                                <label
                                    onClick={() => fileInputRef.current?.click()}
                                    className="cursor-pointer flex items-center gap-2 text-sm text-neutral-400 hover:text-white transition-colors"
                                >
                                    <Upload className="h-4 w-4" /> Upload Receipt
                                </label>
                            </div>
                        </div>
                        <table className="w-full text-left text-sm">
                            <thead className="bg-neutral-950 text-neutral-400">
                                <tr>
                                    <th className="p-4 font-medium">Date</th>
                                    <th className="p-4 font-medium">Vendor</th>
                                    <th className="p-4 font-medium">Description</th>
                                    <th className="p-4 font-medium">Category</th>
                                    <th className="p-4 font-medium">Amount</th>
                                    <th className="p-4 font-medium">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-neutral-800">
                                {ledger.map((item, i) => (
                                    <motion.tr
                                        key={i}
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="hover:bg-neutral-800/50 transition-colors"
                                    >
                                        <td className="p-4 text-neutral-400">{item.date}</td>
                                        <td className="p-4 font-medium">{item.vendor}</td>
                                        <td className="p-4 text-neutral-400 text-xs max-w-[200px] truncate" title={item.description}>{item.description}</td>
                                        <td className="p-4">
                                            <span className="px-2 py-1 bg-neutral-800 rounded-md text-xs">{item.category}</span>
                                        </td>
                                        <td className="p-4">₹{String(item.amount).replace('$', '')}</td>
                                        <td className="p-4">
                                            <span className={cn(
                                                "px-2 py-1 rounded-full text-xs font-medium flex items-center w-fit gap-1",
                                                item.status === "Paid" ? "bg-green-500/10 text-green-500" : "bg-yellow-500/10 text-yellow-500"
                                            )}>
                                                {item.status === "Paid" ? <CheckCircle className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
                                                {item.status}
                                            </span>
                                        </td>
                                    </motion.tr>
                                ))}
                            </tbody>
                        </table>
                        {ledger.length === 0 && (
                            <div className="p-8 text-center text-neutral-500">
                                No transactions found. Upload a receipt to get started.
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Column: Agent & Tools */}
                <div className="col-span-4 space-y-8">
                    <AgentTerminal logs={logs} />

                    {/* Quick Actions (Mock) */}
                    <div className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl space-y-4">
                        <h3 className="text-sm font-medium text-neutral-400 uppercase tracking-widest">Manual Override</h3>
                        <div className="space-y-2">
                            <Button variant="secondary" className="w-full justify-start text-sm" onClick={handleCreateInvoice}>
                                Create New Invoice
                            </Button>
                            <Button variant="secondary" className="w-full justify-start text-sm" onClick={() => handleVoiceCommand("email")}>
                                Send Reminders
                            </Button>
                            <Button variant="destructive" className="w-full justify-start text-sm bg-red-900/20 text-red-400 hover:bg-red-900/40" onClick={handleFreezeSpending}>
                                Freeze Spending
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            <VoiceCommand onCommand={handleVoiceCommand} />
        </div>
    );
};

export default Dashboard;
