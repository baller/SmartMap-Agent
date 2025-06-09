'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Bot, User, Brain, Wrench, CheckCircle, AlertCircle } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  isStreaming?: boolean;
}

interface TravelAssistantProps {
  sessionId: string;
}

interface Status {
  status: string;
  details: string;
  timestamp: string;
}

interface ToolCall {
  id: string;
  function_name: string;
  arguments: string;
  status: 'calling' | 'success' | 'error' | 'not_found';
  result?: string;
  error?: string;
}

interface StreamingMessage {
  content: string;
  isComplete: boolean;
}



interface ThinkingStage {
  id: string;
  type: 'thinking' | 'tool_calling' | 'tool_result' | 'processing';
  title: string;
  content: string;
  timestamp: string;
  isActive: boolean;
  isCompleted: boolean;
  toolCall?: {
    name: string;
    status: 'calling' | 'success' | 'error';
    result?: string;
    error?: string;
  };
}

export function TravelAssistant({ sessionId }: TravelAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentStatus, setCurrentStatus] = useState<Status | null>(null);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [streamingMessage, setStreamingMessage] = useState<StreamingMessage | null>(null);
  const [currentToolCalls, setCurrentToolCalls] = useState<ToolCall[]>([]);

  const [thinkingStages, setThinkingStages] = useState<ThinkingStage[]>([]);
  const [showReasoning, setShowReasoning] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const reasoningEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const scrollReasoningToBottom = () => {
    reasoningEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentStatus]);

  useEffect(() => {
    if (showReasoning) {
      scrollReasoningToBottom();
    }
  }, [thinkingStages, showReasoning]);

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
          // 将流式消息添加到正式消息列表
          if (streamingMessage && streamingMessage.content) {
            const newMessage: Message = {
              role: 'assistant',
              content: streamingMessage.content,
              timestamp: data.timestamp
            };
            setMessages(prev => [...prev, newMessage]);
          }
          setStreamingMessage(null);
          setCurrentToolCalls([]);
          // 完成所有思考阶段
          setThinkingStages(prev => 
            prev.map(stage => ({ 
              ...stage, 
              isActive: false, 
              isCompleted: true 
            }))
          );
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
        setStreamingMessage(null);
        setCurrentToolCalls([]);
        setThinkingStages([]);
      } else if (data.type === 'stream') {
        // 处理流式数据
        if (data.stream_type === 'reasoning') {
          setThinkingStages(prev => {
            // 检查是否是新的思考阶段开始的标识
            const isNewStageMarker = data.data.includes('用户请求：') || 
                                   data.data.includes('🔧 开始调用工具') ||
                                   data.data.includes('📝 处理工具返回的信息');
            
            const now = new Date().toISOString();
            
            if (isNewStageMarker) {
              // 创建新的思考阶段
              const newStage: ThinkingStage = {
                id: `thinking-${Date.now()}`,
                type: 'thinking',
                title: '🤔 AI 思考中',
                content: data.data,
                timestamp: now,
                isActive: true,
                isCompleted: false
              };
              return [...prev, newStage];
            } else {
              // 对于现有阶段，只有当最后一个阶段是思考阶段且未完成时才更新
              const lastStage = prev[prev.length - 1];
              if (lastStage && lastStage.type === 'thinking' && !lastStage.isCompleted) {
                // 避免重复内容：检查新内容是否已经包含在现有内容中
                const newContent = lastStage.content.includes(data.data) 
                  ? lastStage.content 
                  : lastStage.content + data.data;
                
                return prev.map((stage, index) => 
                  index === prev.length - 1
                    ? { ...stage, content: newContent, timestamp: now }
                    : stage
                );
              }
              // 如果没有活跃的思考阶段，创建新的
              const newStage: ThinkingStage = {
                id: `thinking-${Date.now()}`,
                type: 'thinking',
                title: '🤔 AI 思考中',
                content: data.data,
                timestamp: now,
                isActive: true,
                isCompleted: false
              };
              return [...prev, newStage];
            }
          });
        } else if (data.stream_type === 'content') {
          // 标记当前思考阶段完成
          setThinkingStages(prev => 
            prev.map((stage, index) => 
              index === prev.length - 1 && stage.type === 'thinking'
                ? { ...stage, isActive: false, isCompleted: true }
                : stage
            )
          );
          
          setStreamingMessage(prev => ({
            content: (prev?.content || '') + data.data,
            isComplete: false
          }));
        } else if (data.stream_type === 'tool_calls_start') {
          // 工具调用开始，完成当前思考阶段
          setThinkingStages(prev => 
            prev.map((stage, index) => 
              index === prev.length - 1
                ? { ...stage, isActive: false, isCompleted: true }
                : stage
            )
          );
          
          // 为每个工具调用创建阶段
          const toolCalls = data.data.tool_calls.map((tc: any) => ({
            id: tc.id,
            function_name: tc.function_name,
            arguments: tc.arguments,
            status: 'calling' as const
          }));
          setCurrentToolCalls(toolCalls);
          
          // 添加工具调用阶段
          setThinkingStages(prev => {
            const now = new Date().toISOString();
            const newStages = toolCalls.map((tc: any, index: number) => ({
              id: `tool-${tc.id}`,
              type: 'tool_calling' as const,
              title: `🔧 调用工具: ${tc.function_name}`,
              content: `正在调用 ${tc.function_name}...`,
              timestamp: now,
              isActive: index === 0, // 只有第一个工具是活跃的
              isCompleted: false,
              toolCall: {
                name: tc.function_name,
                status: 'calling' as const
              }
            }));
            return [...prev, ...newStages];
          });
        } else if (data.stream_type === 'tool_call_detail') {
          // 更新工具调用详情
          setCurrentToolCalls(prev => 
            prev.map(tc => 
              tc.id === data.data.tool_call_id 
                ? { ...tc, status: data.data.status }
                : tc
            )
          );
        } else if (data.stream_type === 'tool_call_result') {
          // 更新工具调用结果
          setCurrentToolCalls(prev => 
            prev.map(tc => 
              tc.id === data.data.tool_call_id 
                ? { 
                    ...tc, 
                    status: data.data.status,
                    result: data.data.result,
                    error: data.data.error
                  }
                : tc
            )
          );
          
          // 更新对应的工具调用阶段
          setThinkingStages(prev => 
            prev.map(stage => {
              if (stage.id === `tool-${data.data.tool_call_id}`) {
                const isSuccess = data.data.status === 'success';
                return {
                  ...stage,
                  title: `${isSuccess ? '✅' : '❌'} ${stage.toolCall?.name}`,
                  content: isSuccess 
                    ? `✅ 成功获取信息：${data.data.result?.slice(0, 100)}${data.data.result?.length > 100 ? '...' : ''}`
                    : `❌ 调用失败：${data.data.error}`,
                  isActive: false,
                  isCompleted: true,
                  toolCall: {
                    ...stage.toolCall!,
                    status: data.data.status,
                    result: data.data.result,
                    error: data.data.error
                  }
                };
              }
              return stage;
            })
          );
          
          // 激活下一个工具调用（如果有的话）
          setThinkingStages(prev => {
            const currentIndex = prev.findIndex(s => s.id === `tool-${data.data.tool_call_id}`);
            if (currentIndex >= 0 && currentIndex < prev.length - 1) {
              const nextStage = prev[currentIndex + 1];
              if (nextStage.type === 'tool_calling') {
                return prev.map((stage, index) => 
                  index === currentIndex + 1
                    ? { ...stage, isActive: true }
                    : stage
                );
              }
            }
            return prev;
          });
        }
      } else if (data.type === 'error') {
        const errorMessage: Message = {
          role: 'system',
          content: `错误: ${data.content}`,
          timestamp: data.timestamp
        };
        setMessages(prev => [...prev, errorMessage]);
        setIsLoading(false);
        setStreamingMessage(null);
        setCurrentToolCalls([]);
        setThinkingStages([]);
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
    <div className="max-w-6xl mx-auto bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
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
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowReasoning(!showReasoning)}
              className="px-3 py-1 bg-white/20 rounded-lg text-xs hover:bg-white/30 transition-colors"
            >
              {showReasoning ? '隐藏思考过程' : '显示思考过程'}
            </button>
            {isConnected && (
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
            )}
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-300px)] min-h-[600px]">
        {/* 主对话区域 */}
        <div className={`flex-1 flex flex-col ${showReasoning ? 'w-2/3' : 'w-full'}`}>
          {/* 消息区域 */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
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

            {/* 流式消息显示 */}
            {streamingMessage && (
              <div className="flex justify-start">
                <div className="message-bubble message-assistant">
                  <div className="flex items-start space-x-2">
                    <Bot className="h-5 w-5 mt-0.5 flex-shrink-0" />
                    <div 
                      className="flex-1"
                      dangerouslySetInnerHTML={{ __html: formatMessage(streamingMessage.content) }}
                    />
                    <div className="animate-pulse text-blue-500">▋</div>
                  </div>
                </div>
              </div>
            )}

                    {/* 工具调用显示（仅在隐藏reasoning时显示） */}
        {!showReasoning && currentToolCalls.length > 0 && (
          <div className="flex justify-start">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md">
              <div className="flex items-center space-x-2 mb-3">
                <Wrench className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">正在调用工具</span>
              </div>
              <div className="space-y-2">
                {currentToolCalls.map((toolCall, index) => (
                  <div key={index} className="text-sm">
                    <div className="flex items-center space-x-2">
                      <div className={`w-3 h-3 rounded-full ${
                        toolCall.status === 'calling' ? 'bg-yellow-400 animate-pulse' :
                        toolCall.status === 'success' ? 'bg-green-400' :
                        'bg-red-400'
                      }`} />
                      <span className="font-mono text-blue-700">{toolCall.function_name}</span>
                    </div>
                    {toolCall.result && (
                      <div className="ml-5 mt-1 text-xs text-gray-600 bg-gray-100 rounded p-2">
                        {toolCall.result}
                      </div>
                    )}
                    {toolCall.error && (
                      <div className="ml-5 mt-1 text-xs text-red-600 bg-red-50 rounded p-2">
                        错误: {toolCall.error}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

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
    </div>

        {/* 思考过程区域 */}
        {showReasoning && (
          <div className="w-1/3 border-l border-gray-200 bg-gray-50 flex flex-col">
            <div className="p-4 border-b border-gray-200 bg-white">
              <div className="flex items-center space-x-2">
                <Brain className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold text-gray-800">AI 思考过程</h3>
              </div>
              <p className="text-xs text-gray-500 mt-1">实时显示AI的推理和决策过程</p>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {thinkingStages.length > 0 ? (
                <div className="space-y-3">
                  {thinkingStages.map((stage, index) => (
                    <div key={stage.id} className={`transition-all duration-300 ${
                      stage.isActive ? 'ring-2 ring-purple-200' : ''
                    }`}>
                      {stage.type === 'thinking' && (
                        <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                          <div className="flex items-center space-x-2 mb-2">
                            <div className={`w-2 h-2 rounded-full ${
                              stage.isActive ? 'bg-purple-400 animate-pulse' : 
                              stage.isCompleted ? 'bg-green-400' : 'bg-gray-400'
                            }`} />
                            <span className="text-xs font-medium text-purple-800">
                              {stage.title}
                            </span>
                            <span className="text-xs text-gray-500">
                              {new Date(stage.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <div className="text-sm text-purple-700 whitespace-pre-wrap leading-relaxed">
                            {stage.content}
                            {stage.isActive && <span className="animate-pulse text-purple-500">▋</span>}
                          </div>
                        </div>
                      )}
                      
                      {stage.type === 'tool_calling' && (
                        <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                          <div className="flex items-center space-x-2 mb-2">
                            <div className={`w-2 h-2 rounded-full ${
                              stage.isActive ? 'bg-blue-400 animate-pulse' : 
                              stage.isCompleted ? 
                                (stage.toolCall?.status === 'success' ? 'bg-green-400' : 'bg-red-400') : 
                                'bg-gray-400'
                            }`} />
                            <span className="text-xs font-medium text-blue-800">
                              {stage.title}
                            </span>
                            <span className="text-xs text-gray-500">
                              {new Date(stage.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <div className="text-sm text-blue-700">
                            {stage.content}
                            {stage.isActive && <span className="animate-pulse text-blue-500">▋</span>}
                          </div>
                          {stage.toolCall?.result && (
                            <div className="mt-2 text-xs text-gray-600 bg-white rounded p-2 border">
                              <strong>结果：</strong>{stage.toolCall.result}
                            </div>
                          )}
                          {stage.toolCall?.error && (
                            <div className="mt-2 text-xs text-red-600 bg-red-50 rounded p-2 border border-red-200">
                              <strong>错误：</strong>{stage.toolCall.error}
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* 添加连接线，除了最后一个阶段 */}
                      {index < thinkingStages.length - 1 && (
                        <div className="flex justify-center py-2">
                          <div className="w-px h-4 bg-gray-300"></div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Brain className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-400">等待AI开始思考...</p>
                </div>
              )}
              <div ref={reasoningEndRef} />
            </div>
          </div>
        )}
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