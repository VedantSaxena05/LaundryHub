import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { staffApi, type TodaySummary } from "@/api/staff";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, Package, CheckCircle, Clock } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";

export default function StaffDashboard() {
  const { token } = useAuth();
  const [today, setToday] = useState<TodaySummary | null>(null);

  useEffect(() => {
    if (!token) return;
    staffApi.getToday(token).then(setToday).catch(() => {});
  }, [token]);

  const stats = [
    { label: "Total Booked", value: today?.total_booked, icon: Calendar, iconBg: "bg-primary/10", iconColor: "text-primary" },
    { label: "Bags Dropped", value: today?.bags_dropped, icon: Package, iconBg: "bg-warning/10", iconColor: "text-warning" },
    { label: "Bags Ready", value: today?.bags_ready, icon: CheckCircle, iconBg: "bg-success/10", iconColor: "text-success" },
    { label: "Collected", value: today?.bags_collected, icon: Clock, iconBg: "bg-info/10", iconColor: "text-info" },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Staff Dashboard"
        description="Today's operations at a glance"
        icon={<Clock className="w-6 h-6 text-primary-foreground" />}
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        {stats.map((stat, i) => (
          <AnimatedCard key={stat.label} delay={0.1 + i * 0.1} className="group hover:scale-[1.02]">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-semibold text-muted-foreground">{stat.label}</CardTitle>
              <div className={`w-10 h-10 rounded-2xl ${stat.iconBg} flex items-center justify-center transition-colors`}>
                <stat.icon className={`h-5 w-5 ${stat.iconColor}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-extrabold font-display">{stat.value ?? "—"}</div>
            </CardContent>
          </AnimatedCard>
        ))}
      </div>
    </div>
  );
}
