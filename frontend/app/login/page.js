"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Compass, Lock, Mail, ArrowRight } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert } from "@/components/ui/alert";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (isAuthenticated) {
    router.push("/");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (err) {
      setError(err.message || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-[75vh] items-center justify-center">
      <Card className="w-full max-w-md shadow-md">
        <CardHeader className="space-y-2 text-center pb-6">
          <div className="mx-auto p-2.5 rounded-xl bg-primary text-primary-foreground w-fit shadow-xs">
            <Compass className="h-6 w-6" />
          </div>
          <CardTitle className="text-xl font-bold tracking-tight">Sign in to ACIS</CardTitle>
          <p className="text-xs text-muted-foreground">
            Enterprise AI Competitive Intelligence & Evidence Review
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive" title="Sign In Error">
                {error}
              </Alert>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs font-medium">
                Email address
              </Label>
              <div className="relative">
                <Input
                  id="email"
                  type="email"
                  placeholder="analyst@enterprise.com"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-9 text-xs"
                />
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-xs font-medium">
                Password
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••••••"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-9 text-xs"
                />
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              </div>
            </div>

            <Button type="submit" disabled={loading} className="w-full text-xs gap-2">
              {loading ? "Authenticating…" : "Sign In"}
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </form>

          <div className="mt-6 pt-4 border-t text-center text-[11px] text-muted-foreground">
            Role-Based Access Control • Tenant Isolation • HttpOnly Token Security
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
