'use client';

import { MapPin, RotateCcw } from 'lucide-react';

interface HeaderProps {
  onReset: () => void;
}

export function Header({ onReset }: HeaderProps) {
  return (
    <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
              <MapPin className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">智能旅行助手</h1>
              <p className="text-sm text-gray-500">AI 驱动的个性化旅行规划</p>
            </div>
          </div>
          
          <button
            onClick={onReset}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors duration-200"
            title="重新开始"
          >
            <RotateCcw className="h-4 w-4" />
            <span className="text-sm">重新开始</span>
          </button>
        </div>
      </div>
    </header>
  );
} 