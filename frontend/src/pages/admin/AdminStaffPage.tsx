import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { adminApi, type AdminStaff } from "@/api/admin";
import { CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Shield, UserX } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";

export default function AdminStaffPage() {
  const { token } = useAuth();
  const [staff, setStaff] = useState<AdminStaff[]>([]);

  const fetchStaff = () => {
    if (!token) return;
    adminApi.listStaff(token, false).then(setStaff).catch(() => setStaff([]));
  };

  useEffect(() => { fetchStaff(); }, [token]);

  const handleDeactivate = async (id: string) => {
    if (!token) return;
    try { await adminApi.deactivateStaff(token, id); toast.success("Staff deactivated!"); fetchStaff(); }
    catch (err: any) { toast.error(err.message); }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Staff Management"
        description={`${staff.length} staff members`}
        icon={<Shield className="w-6 h-6 text-primary-foreground" />}
      />

      <div className="space-y-3">
        {staff.map((s, i) => (
          <AnimatedCard key={s.id} delay={0.1 + i * 0.04}>
            <CardContent className="pt-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-2xl bg-secondary/10 flex items-center justify-center flex-shrink-0">
                    <Shield className="h-5 w-5 text-secondary" />
                  </div>
                  <div>
                    <p className="font-semibold">{s.name}</p>
                    <p className="text-xs text-muted-foreground">{s.employee_id} · {s.role}</p>
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
