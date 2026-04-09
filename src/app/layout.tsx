import type { Metadata } from "next";
import { Manrope, Noto_Sans_KR } from "next/font/google";
import "./globals.css";

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-manrope"
});

const notoSansKr = Noto_Sans_KR({
  subsets: ["latin"],
  variable: "--font-noto-sans-kr",
  weight: ["400", "500", "700"]
});

export const metadata: Metadata = {
  title: "My Info Site",
  description: "공기업 채용, 인턴 공고, 청년 지원금 정보를 모아보는 개인용 대시보드"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body
        className={`${manrope.variable} ${notoSansKr.variable} font-[var(--font-noto-sans-kr)] antialiased`}
      >
        {children}
      </body>
    </html>
  );
}