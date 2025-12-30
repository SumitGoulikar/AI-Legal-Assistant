import React from "react";

export default function ChatMessage({ message }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[80%] p-3 rounded-lg ${isUser ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-900"}`}
      >
        <div className="text-sm whitespace-pre-wrap">{message.content}</div>
      </div>
    </div>
  );
}
