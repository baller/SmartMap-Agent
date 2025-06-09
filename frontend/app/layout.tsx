import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "智能旅行助手",
  description: "基于 AI 的智能旅行规划助手，为您制定完美的旅行计划",
  keywords: "旅行规划, AI助手, 行程安排, 旅游攻略",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
} 