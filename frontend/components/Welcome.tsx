'use client';

import { useState } from 'react';
import { MapPin, Calendar, DollarSign, Users } from 'lucide-react';

interface WelcomeProps {
  onCreateSession: () => void;
}

export function Welcome({ onCreateSession }: WelcomeProps) {
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateSession = async () => {
    setIsCreating(true);
    await onCreateSession();
    setIsCreating(false);
  };

  return (
    <div className="max-w-4xl mx-auto text-center">
      {/* 主标题区域 */}
      <div className="mb-12">
        <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
          开启你的
          <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            智能旅行
          </span>
          之旅
        </h2>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
          基于最新 AI 技术，为您制定个性化的旅行计划。从景点推荐到行程安排，一切都为您量身定制。
        </p>
      </div>

      {/* 功能特色 */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow duration-300">
          <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
            <MapPin className="h-6 w-6 text-blue-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">智能推荐</h3>
          <p className="text-gray-600 text-sm">
            基于实时数据推荐最佳景点、餐厅和活动
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow duration-300">
          <div className="bg-green-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
            <Calendar className="h-6 w-6 text-green-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">行程规划</h3>
          <p className="text-gray-600 text-sm">
            自动生成最优路线，节省时间和精力
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow duration-300">
          <div className="bg-purple-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
            <DollarSign className="h-6 w-6 text-purple-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">预算估算</h3>
          <p className="text-gray-600 text-sm">
            智能预算计算，让每一分钱都花得值
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow duration-300">
          <div className="bg-orange-100 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
            <Users className="h-6 w-6 text-orange-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">个性定制</h3>
          <p className="text-gray-600 text-sm">
            根据您的偏好和需求量身定制
          </p>
        </div>
      </div>

      {/* 示例问题 */}
      <div className="bg-white rounded-xl p-8 shadow-lg border border-gray-100 mb-12">
        <h3 className="text-2xl font-semibold text-gray-900 mb-6">您可以这样问我：</h3>
        <div className="grid md:grid-cols-2 gap-4 text-left">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-gray-700">"我想在杭州玩3天，预算5000元，喜欢文化古迹和美食"</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-gray-700">"帮我规划一个北京周末两日游，重点是亲子活动"</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-gray-700">"我要去上海出差，顺便旅游一天，推荐路线"</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-gray-700">"春节期间去成都，有什么特色活动推荐？"</p>
          </div>
        </div>
      </div>

      {/* 开始按钮 */}
      <button
        onClick={handleCreateSession}
        disabled={isCreating}
        className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-xl text-lg font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
      >
        {isCreating ? (
          <span className="flex items-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            正在准备...
          </span>
        ) : (
          '开始规划旅行'
        )}
      </button>

      <p className="text-gray-500 text-sm mt-4">
        完全免费使用，无需注册
      </p>
    </div>
  );
}