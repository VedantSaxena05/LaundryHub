import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { adminApi, type AdminStudent } from "@/api/admin";
import { CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Users, UserX, Search } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";

export default function AdminStudentsPage() {
  const { token } = useAuth();
  const [students, setStudents] = useState<AdminStudent[]>([]);
  const [search, setSearch] = useState("");

  const fetchStudents = () => {
    if (!token) return;
    adminApi.listStudents(token).then(setStudents).catch(() => setStudents([]));
  };

  useEffect(() => { fetchStudents(); }, [token]);

  const handleDeactivate = async (id: string) => {
    if (!token) return;
    try {
      await fetch(`${localStorage.getItem("laundry_api_base_url") || "http://localhost:8000"}/students/${id}`, {
        method: "DELETE", headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Student deactivated!"); fetchStudents();
    } catch (err: any) { toast.error(err.message); }
  };

  const filtered = students.filter(s =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.registration_number.toLowerCase().includes(search.toLowerCase()) ||
    s.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8">
      <PageHeader
        title="Student Management"
        description={`${students.length} students registered`}
        icon={<Users className="w-6 h-6 text-primary-foreground" />}
      />

      <div className="relative opacity-0 animate-fade-in" style={{ animationDelay: '0.1s' }}>
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by name, reg number, or email..." className="pl-11 h-12 rounded-xl" />
      </div>

      <div className="space-y-3">
        {filtered.map((s, i) => (
          <AnimatedCard key={s.id} delay={0.15 + i * 0.03}>
            <CardContent className="pt-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-2xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Users className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold">{s.name}</p>
                    <p className="text-xs text-muted-foreground">{s.registration_number} · {s.email} · Block {s.block}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={s.is_active ? "default" : "secondary"} className="rounded-lg">{s.is_active ? "Active" : "Inactive"}</Badge>
                  {s.is_active && (
                    <Button variant="ghost" size="sm" className="text-destructive rounded-xl hover:bg-destructive/10" onClick={() => handleDeactivate(s.id)}>
                      <UserX className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </AnimatedCard>
        ))}
      </div>
    </div>
  );
}
