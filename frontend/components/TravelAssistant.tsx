'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Bot, User, Brain, Wrench, CheckCircle, AlertCircle } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

interface TravelAssistantProps {
  sessionId: string;
}

interface Status {
  status: string;
  details: string;
  timestamp: string;
}

export function TravelAssistant({ sessionId }: TravelAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentStatus, setCurrentStatus] = useState<Status | null>(null);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStatus]);

  // WebSocket 连接
  const connectWebSocket = useCallback(() => {
    if (ws) {
      ws.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
    
    const newWs = new WebSocket(wsUrl);

    newWs.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setCurrentStatus({
        status: 'connected',
        details: '已连接到智能助手',
        timestamp: new Date().toISOString()
      });
    };

    newWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'status') {
        setCurrentStatus({
          status: data.status,
          details: data.details,
          timestamp: data.timestamp
        });
        
        if (data.status === 'completed') {
          setIsLoading(false);
        }
      } else if (data.type === 'travel_plan') {
        const newMessage: Message = {
          role: 'assistant',
          content: data.content,
          timestamp: data.timestamp
        };
        setMessages(prev => [...prev, newMessage]);
        setIsLoading(false);
        setCurrentStatus(null);
      } else if (data.type === 'error') {
        const errorMessage: Message = {
          role: 'system',
          content: `错误: ${data.content}`,
          timestamp: data.timestamp
        };
        setMessages(prev => [...prev, errorMessage]);
        setIsLoading(false);
        setCurrentStatus({
          status: 'error',
          details: data.content,
          timestamp: data.timestamp
        });
      }
    };

    newWs.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setCurrentStatus({
        status: 'disconnected',
        details: '连接已断开',
        timestamp: new Date().toISOString()
      });
    };

    newWs.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
      setCurrentStatus({
        status: 'error',
        details: '连接出错',
        timestamp: new Date().toISOString()
      });
    };

    setWs(newWs);
  }, [sessionId]);

  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [connectWebSocket]);

  const sendMessage = async () => {
    if (!input.trim() || !isConnected || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setInput('');

    // 通过 WebSocket 发送消息
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'travel_request',
        content: userMessage.content
      }));
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'thinking':
        return <Brain className="h-4 w-4 animate-pulse" />;
      case 'calling_tools':
      case 'tool_calling':
        return <Wrench className="h-4 w-4 animate-spin" />;
      case 'processing':
        return <Bot className="h-4 w-4 animate-bounce" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4" />;
      case 'error':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Bot className="h-4 w-4" />;
    }
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'thinking':
        return 'status-thinking';
      case 'calling_tools':
      case 'tool_calling':
        return 'status-calling-tools';
      case 'processing':
        return 'status-processing';
      case 'completed':
        return 'status-completed';
      case 'error':
        return 'status-error';
      default:
        return 'status-indicator';
    }
  };

  const formatMessage = (content: string) => {
    // 简单的 Markdown 格式化
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>');
  };

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      {/* 聊天头部 */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Bot className="h-6 w-6" />
            <div>
              <h3 className="font-semibold">智能旅行助手</h3>
              <p className="text-sm opacity-90">
                {isConnected ? '在线' : '离线'} • 会话 ID: {sessionId.slice(0, 8)}...
              </p>
            </div>
          </div>
          {isConnected && (
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
          )}
        </div>
      </div>

      {/* 消息区域 */}
      <div className="h-96 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">
              您好！我是您的专属旅行助手。请告诉我您的旅行需求，我来为您制定完美的行程计划！
            </p>
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-2 max-w-2xl mx-auto">
              <button
                onClick={() => setInput('我想在杭州玩3天，预算5000元，喜欢文化古迹和美食')}
                className="text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm transition-colors"
              >
                💰 杭州3天游，预算5000元
              </button>
              <button
                onClick={() => setInput('帮我规划一个北京周末两日游，重点是亲子活动')}
                className="text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm transition-colors"
              >
                👨‍👩‍👧‍👦 北京亲子两日游
              </button>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`message-bubble ${
              message.role === 'user' ? 'message-user' : 
              message.role === 'assistant' ? 'message-assistant' : 'message-system'
            }`}>
              <div className="flex items-start space-x-2">
                {message.role === 'assistant' && <Bot className="h-5 w-5 mt-0.5 flex-shrink-0" />}
                {message.role === 'user' && <User className="h-5 w-5 mt-0.5 flex-shrink-0" />}
                <div 
                  className="flex-1"
                  dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
                />
              </div>
              <div className="text-xs opacity-70 mt-2">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {/* 状态指示器 */}
        {currentStatus && currentStatus.status !== 'connected' && (
          <div className="flex justify-start">
            <div className={`status-indicator ${getStatusClass(currentStatus.status)}`}>
              {getStatusIcon(currentStatus.status)}
              <span>{currentStatus.details}</span>
              {currentStatus.status === 'thinking' && <span className="loading-dots"></span>}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              isConnected 
                ? "描述您的旅行需求，比如：我想去北京玩3天，预算3000元..." 
                : "连接中..."
            }
            disabled={!isConnected || isLoading}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || !isConnected || isLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 flex items-center space-x-2"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <Send className="h-5 w-5" />
            )}
            <span className="hidden sm:inline">发送</span>
          </button>
        </div>
        
        {!isConnected && (
          <div className="mt-2 text-center">
            <button
              onClick={connectWebSocket}
              className="text-sm text-blue-600 hover:text-blue-800 underline"
            >
              重新连接
            </button>
          </div>
        )}
      </div>
    </div>
  );
} 