import type { Metadata } from "next"
import { Geist } from "next/font/google"
import "./globals.css"
import { Providers } from "@/components/providers"
import { Toaster } from "@/components/ui/sonner"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "Cedrus — GRC Platform",
  description: "ISO 17021 audit management for certification bodies",
}

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${geistSans.variable} h-full antialiased`}>
      <body className="h-full">
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  )
}
