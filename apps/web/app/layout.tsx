import "./globals.css";
import { ReactNode } from "react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import Toast from "../components/Toast";

export const metadata = {
  title: "Meeting Summarizer",
  description: "WhisperX + local LLM summarizer",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen flex flex-col">
          <Header />
          <main className="flex-1 container py-6">{children}</main>
          <Toast />
          <Footer />
        </div>
      </body>
    </html>
  );
}
