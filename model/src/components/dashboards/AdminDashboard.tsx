import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { adminApi, type OverviewAnalytics } from "@/api/admin";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Shirt, Calendar, Package, BarChart3 } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";
import { useLanguage } from "@/i18n/LanguageContext";

export default function AdminDashboard() {
  const { token } = useAuth();
  const { t } = useLanguage();
  const [overview, setOverview] = useState<OverviewAnalytics | null>(null);

  useEffect(() => {
    if (!token) return;
    adminApi.getOverview(token).then(setOverview).catch(() => {});
  }, [token]);

  const stats = [
    { label: t("admin.active_students"), value: overview?.active_students, icon: Users, iconBg: "bg-primary/10", iconColor: "text-primary" },
    { label: t("admin.active_staff"), value: overview?.active_staff, icon: Shirt, iconBg: "bg-secondary/10", iconColor: "text-secondary" },
    { label: t("admin.slots_booked_today"), value: overview?.slots_booked_today, icon: Calendar, iconBg: "bg-info/10", iconColor: "text-info" },
    { label: t("admin.bags_in_flight"), value: overview?.bags_in_flight, icon: Package, iconBg: "bg-warning/10", iconColor: "text-warning" },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("admin.dashboard_title")}
        description={t("admin.system_overview")}
        icon={<BarChart3 className="w-6 h-6 text-primary-foreground" />}
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

      {overview?.block_usage_today && (
        <AnimatedCard delay={0.5}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-display text-lg">
              <BarChart3 className="h-5 w-5 text-primary" /> {t("admin.block_usage_today")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(overview.block_usage_today).map(([block, data]) => (
                <div key={block} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-semibold">{t("common.block")} {block}</span>
                    <span className="text-muted-foreground font-medium">{data.booked} / {data.limit}</span>
                  </div>
                  <Progress value={data.limit > 0 ? (data.booked / data.limit) * 100 : 0} className="h-2.5 rounded-full" />
                </div>
              ))}
            </div>
          </CardContent>
        </AnimatedCard>
      )}
    </div>
  );
}
