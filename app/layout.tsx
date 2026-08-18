import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "起飞场 LaunchDeck — Vibe Coder 产品首发与互助社区",
  description: "发布你的作品，换取真实体验与有效反馈。先一起跨过冷启动，再各凭本事起飞。",
  icons: { icon: "/favicon.svg", shortcut: "/favicon.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
