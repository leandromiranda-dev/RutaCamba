import type { ReactNode } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { LogOut, MapPin, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ToastProvider } from "@/components/ui/toast";
import { clearSession, getSession } from "@/lib/session";
import Login from "@/pages/Login";
import Tour from "@/pages/Tour";
import Admin from "@/pages/Admin";

function ProtectedLayout({ children }: { children: ReactNode }) {
  const nav = useNavigate();
  const loc = useLocation();
  const session = getSession();

  if (!session) {
    return <Navigate to="/" replace state={{ from: loc.pathname }} />;
  }

  const logout = () => {
    clearSession();
    nav("/", { replace: true });
  };

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 border-b border-border bg-background/80 backdrop-blur safe-top">
        <div className="mx-auto flex w-full max-w-md items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="grid h-9 w-9 place-items-center rounded-lg bg-primary/20">
              <MapPin className="h-5 w-5 text-primary" />
            </div>
            <div className="leading-tight">
              <p className="text-sm font-bold">{session.identity}</p>
              <Badge
                variant={session.role === "admin" ? "default" : "secondary"}
                className="mt-0.5"
              >
                {session.role === "admin" && (
                  <ShieldCheck className="mr-1 h-3 w-3" />
                )}
                {session.role}
              </Badge>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={logout} aria-label="Salir">
            <LogOut className="h-5 w-5" />
          </Button>
        </div>
      </header>
      <main className="px-4 py-5 safe-bottom">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route
          path="/tour"
          element={
            <ProtectedLayout>
              <Tour />
            </ProtectedLayout>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedLayout>
              <Admin />
            </ProtectedLayout>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ToastProvider>
  );
}
