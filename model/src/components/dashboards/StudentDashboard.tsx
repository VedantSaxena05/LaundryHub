import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { studentsApi, type StudentProfile } from "@/api/students";
import { slotsApi, type Slot } from "@/api/slots";
import { bagsApi, type Bag, BAG_STATUS_LABELS } from "@/api/bags";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, Package, User, MapPin } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";
import { useLanguage } from "@/i18n/LanguageContext";

export default function StudentDashboard() {
  const { token } = useAuth();
  const { t } = useLanguage();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [bag, setBag] = useState<Bag | null>(null);

  useEffect(() => {
    if (!token) return;
    studentsApi.getMe(token).then(setProfile).catch(() => {});
    slotsApi.getMy(token).then(setSlots).catch(() => {});
    bagsApi.getMy(token).then(setBag).catch(() => setBag(null));
  }, [token]);

  const activeSlots = slots.filter(s => s.status === "booked");

  return (
    <div className="space-y-8">
      <PageHeader
        title={`${t("student.welcome_back")}${profile ? `, ${profile.name}` : ""}!`}
        description={t("student.laundry_overview")}
        icon={<User className="w-6 h-6 text-primary-foreground" />}
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        <AnimatedCard delay={0.1} className="group hover:scale-[1.02]">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">{t("student.active_slots")}</CardTitle>
            <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/15 transition-colors">
              <Calendar className="h-5 w-5 text-primary" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-extrabold font-display">{activeSlots.length}</div>
            <p className="text-xs text-muted-foreground mt-1.5 font-medium">{t("student.bookings_this_month")}</p>
          </CardContent>
        </AnimatedCard>

        <AnimatedCard delay={0.2} className="group hover:scale-[1.02]">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">{t("student.bag_status")}</CardTitle>
            <div className="w-10 h-10 rounded-2xl bg-secondary/10 flex items-center justify-center group-hover:bg-secondary/15 transition-colors">
              <Package className="h-5 w-5 text-secondary" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-extrabold font-display capitalize">{bag ? (BAG_STATUS_LABELS[bag.status] ?? bag.status) : t("student.no_bag")}</div>
            <p className="text-xs text-muted-foreground mt-1.5 font-medium">{t("student.current_bag")}</p>
          </CardContent>
        </AnimatedCard>

        <AnimatedCard delay={0.3} className="group hover:scale-[1.02]">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground">{t("common.block")}</CardTitle>
            <div className="w-10 h-10 rounded-2xl bg-info/10 flex items-center justify-center group-hover:bg-info/15 transition-colors">
              <MapPin className="h-5 w-5 text-info" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-extrabold font-display">{profile?.block || "—"}</div>
            <p className="text-xs text-muted-foreground mt-1.5 font-medium">Room {profile?.room_number || "—"}</p>
          </CardContent>
        </AnimatedCard>
      </div>

      {activeSlots.length > 0 && (
        <AnimatedCard delay={0.4}>
          <CardHeader>
            <CardTitle className="text-lg font-display flex items-center gap-2">
              <Calendar className="h-5 w-5 text-primary" />
              {t("student.upcoming_bookings")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {activeSlots.map((slot) => (
                <div key={slot.id} className="flex items-center justify-between p-4 rounded-xl bg-accent/40 border border-border/50">
                  <div>
                    <p className="font-semibold text-sm">{slot.date}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">Slot #{slot.month_index}</p>
                  </div>
                  <Badge variant="default" className="rounded-lg text-xs">{slot.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </AnimatedCard>
      )}
    </div>
  );
}
