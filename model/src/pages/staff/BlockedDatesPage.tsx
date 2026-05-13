import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { staffApi, type BlockedDate } from "@/api/staff";
import { CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { CalendarOff, Plus, Trash2, Calendar } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";
import { useLanguage } from "@/i18n/LanguageContext";

export default function BlockedDatesPage() {
  const { token, role } = useAuth();
  const { t } = useLanguage();
  const [dates, setDates] = useState<BlockedDate[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [date, setDate] = useState("");
  const [reason, setReason] = useState("");

  const fetchDates = () => {
    if (!token) return;
    staffApi.listBlockedDates(token).then(setDates).catch(() => setDates([]));
  };

  useEffect(() => { fetchDates(); }, [token]);

  const handleAdd = async () => {
    if (!token) return;
    try {
      await staffApi.addBlockedDate(token, { date, reason });
      toast.success("Date blocked!");
      setShowCreate(false); setDate(""); setReason(""); fetchDates();
    } catch (err: any) { toast.error(err.message); }
  };

  const handleRemove = async (d: string) => {
    if (!token) return;
    try { await staffApi.removeBlockedDate(token, d); toast.success("Date unblocked!"); fetchDates(); }
    catch (err: any) { toast.error(err.message); }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("blocked.title")}
        description={t("blocked.description")}
        icon={<Calendar className="w-6 h-6 text-primary-foreground" />}
        actions={
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="rounded-xl font-semibold gradient-primary border-0 text-primary-foreground hover:opacity-90">
                <Plus className="h-4 w-4 mr-1.5" /> {t("blocked.block_date")}
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-2xl">
              <DialogHeader><DialogTitle className="font-display">{t("blocked.block_a_date")}</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <Label className="text-sm font-medium">{t("common.date")}</Label>
                  <Input type="date" value={date} onChange={e => setDate(e.target.value)} className="rounded-xl h-11" />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-sm font-medium">{t("blocked.reason")}</Label>
                  <Input value={reason} onChange={e => setReason(e.target.value)} placeholder="National holiday" className="rounded-xl h-11" />
                </div>
                <Button onClick={handleAdd} className="w-full rounded-xl h-11 font-semibold">{t("blocked.block_date")}</Button>
              </div>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {dates.map((d, i) => (
          <AnimatedCard key={d.date} delay={0.1 + i * 0.05} className="group hover:scale-[1.01]">
            <CardContent className="pt-5">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-destructive/10 flex items-center justify-center flex-shrink-0">
                    <CalendarOff className="h-5 w-5 text-destructive" />
                  </div>
                  <div>
                    <p className="font-semibold">{d.date}</p>
                    <p className="text-sm text-muted-foreground">{d.reason}</p>
                  </div>
                </div>
                {role === "admin" && (
                  <Button variant="ghost" size="icon" className="text-destructive rounded-xl hover:bg-destructive/10" onClick={() => handleRemove(d.date)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </CardContent>
          </AnimatedCard>
        ))}
        {dates.length === 0 && <p className="text-center text-muted-foreground py-12 col-span-3 font-medium">{t("blocked.no_dates")}</p>}
      </div>
    </div>
  );
}
