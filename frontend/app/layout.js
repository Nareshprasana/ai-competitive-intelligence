import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export const metadata = {
  title: "ACIS - AI Competitive Intelligence System",
  description: "Enterprise competitive intelligence research, evidence validation & strategic report workspace",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-foreground antialiased selection:bg-primary/10 selection:text-primary">
        <AuthProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="ml-64 flex flex-col flex-1 min-w-0">
              <Header />
              <main className="flex-1 p-8 space-y-6 max-w-7xl w-full mx-auto">
                {children}
              </main>
            </div>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
