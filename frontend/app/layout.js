import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata = {
  title: "ACIS - AI Competitive Intelligence",
  description: "Competitive intelligence research dashboard",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <Sidebar />
        <div className="ml-64 flex flex-col min-h-screen">
          <header className="sticky top-0 z-10 border-b border-input bg-background/95 backdrop-blur px-6 py-3 flex items-center justify-between">
            <h1 className="text-lg font-semibold">Competitive Intelligence</h1>
            <div className="text-xs text-muted-foreground">LangGraph multi-agent backend</div>
          </header>
          <main className="flex-1 p-8 space-y-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
