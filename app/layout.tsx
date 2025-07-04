import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css" // Import your global CSS

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Stock Analysis App",
  description: "ADF Test for Stock Data",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
