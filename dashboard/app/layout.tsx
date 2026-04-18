import type { Metadata } from "next"
import localFont from "next/font/local"
import "./globals.css"
import { Sidebar } from "@/components/layout/Sidebar"
import { Topbar } from "@/components/layout/Topbar"

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
})
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
})

export const metadata: Metadata = {
  title: "AROP — AI Observability",
  description: "AI Reliability & Observability Platform",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} bg-slate-950 text-slate-200 antialiased`}>
        <Sidebar />
        <div className="ml-56 min-h-screen flex flex-col">
          <Topbar />
          <main className="flex-1 px-6 py-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
