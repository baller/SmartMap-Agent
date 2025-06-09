'use client';

import { useState, useEffect } from 'react';
import { TravelAssistant } from '@/components/TravelAssistant';
import { Header } from '@/components/Header';
import { Welcome } from '@/components/Welcome';

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 创建新会话
    createSession();
  }, []);

  const createSession = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
      } else {
        console.error('Failed to create session');
      }
    } catch (error) {
      console.error('Error creating session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const resetSession = () => {
    setSessionId(null);
    createSession();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">正在初始化旅行助手...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Header onReset={resetSession} />
      <main className="container mx-auto px-4 py-8">
        {sessionId ? (
          <TravelAssistant sessionId={sessionId} />
        ) : (
          <Welcome onCreateSession={createSession} />
        )}
      </main>
    </div>
  );
} 