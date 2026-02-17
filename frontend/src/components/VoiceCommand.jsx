import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const VoiceCommand = ({ onCommand }) => {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const recognitionRef = useRef(null);

    useEffect(() => {
        if ('webkitSpeechRecognition' in window) {
            const recognition = new window.webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onstart = () => setIsListening(true);
            recognition.onend = () => setIsListening(false);

            recognition.onresult = (event) => {
                const transcript = Array.from(event.results)
                    .map(result => result[0])
                    .map(result => result.transcript)
                    .join('');
                setTranscript(transcript);

                if (event.results[0].isFinal) {
                    onCommand(transcript);
                }
            };

            recognitionRef.current = recognition;
        } else {
            console.warn("Speech Recognition Not Supported");
        }
    }, [onCommand]);

    const toggleListen = () => {
        if (isListening) {
            recognitionRef.current?.stop();
        } else {
            setTranscript('');
            recognitionRef.current?.start();
        }
    };

    return (
        <div className="fixed bottom-8 right-8 z-50 flex items-center gap-4">
            {transcript && (
                <div className="bg-black/80 text-white px-4 py-2 rounded-full backdrop-blur-md border border-white/10 animate-in fade-in slide-in-from-bottom-2">
                    "{transcript}"
                </div>
            )}

            <button
                onClick={toggleListen}
                className={cn(
                    "h-16 w-16 rounded-full flex items-center justify-center transition-all duration-300 shadow-2xl border-4",
                    isListening
                        ? "bg-red-500 border-red-300 scale-110 animate-pulse shadow-red-500/50"
                        : "bg-black border-white/20 hover:scale-105 hover:border-white/50"
                )}
            >
                {isListening ? (
                    <Activity className="h-8 w-8 text-white animate-bounce" />
                ) : (
                    <Mic className="h-8 w-8 text-white" />
                )}
            </button>
        </div>
    );
};
// End of file

export default VoiceCommand;
