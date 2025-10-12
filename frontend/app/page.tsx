"use client";

import { useState, useEffect, useRef, FormEvent, ChangeEvent } from "react";

interface Message {
  role: string;
  text: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: input,
          history: messages.filter(m => m.role !== "system"), // Only send user/bot history
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const botMessage: Message = { role: "bot", text: data.reply };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "Error: Could not connect to the backend." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const loadYesterdayHistory = async () => {
    setIsLoading(true);
    try {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const year = yesterday.getFullYear();
      const month = yesterday.getMonth() + 1;
      const day = yesterday.getDate();

      const response = await fetch(
        `${API_BASE_URL}/api/history?year=${year}&month=${month}&day=${day}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const history = await response.json();
      if (history.length === 0) {
        setMessages([{ role: "bot", text: "No chat history from yesterday." }]);
      } else {
        setMessages(history);
      }
    } catch (error) {
      console.error("Error loading history:", error);
      setMessages([
        { role: "bot", text: "Error: Could not load yesterday's history." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/clear_history`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      setMessages([]);
    } catch (error) {
      console.error("Error clearing chat:", error);
      setMessages([
        { role: "bot", text: "Error: Could not clear chat history." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      {/* Header */}
      <header className="bg-[#d313d6] text-white p-4 text-center text-2xl font-bold shadow-md">
        🍕 Pizza OrderBot
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg shadow ${msg.role === "user"
                  ? "bg-[#d313d6] text-white" : "bg-[#d313d6] dark:bg-gray-700"}
              `}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg shadow bg-gray-300 dark:bg-gray-700">
              <div className="flex items-center space-x-1">
                <span className="text-sm">Typing</span>
                <div className="flex space-x-1">
                  <div className="w-1 h-1 bg-gray-600 rounded-full animate-bounce"></div>
                  <div className="w-1 h-1 bg-gray-600 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-1 h-1 bg-gray-600 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input and Buttons Area */}
      <form onSubmit={sendMessage} className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row gap-2">
        <input
          type="text"
          value={input}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 p-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#b50fb8] dark:bg-gray-700 dark:text-gray-100"
          disabled={isLoading}
        />
        <div className="flex gap-2">
          <button
            type="submit"
            className="bg-[#d313d6] hover:bg-[#b50fb8] text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            disabled={isLoading}
          >
            Send
          </button>
          <button
            type="button"
            onClick={loadYesterdayHistory}
            className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
            disabled={isLoading}
          >
            Load Yesterday
          </button>
          <button
            type="button"
            onClick={clearChat}
            className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50"
            disabled={isLoading}
          >
            Clear Chat
          </button>
        </div>
      </form>
    </div>
  );
}
