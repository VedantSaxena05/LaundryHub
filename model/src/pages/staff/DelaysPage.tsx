import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { staffApi, type Delay } from "@/api/staff";
import { CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { AlertTriangle, Plus, Bell, Ban } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";
import { useLanguage } from "@/i18n/LanguageContext";

export default function DelaysPage() {
  const { token } = useAuth();
  const { t } = useLanguage();
  const [delays, setDelays] = useState<Delay[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [reason, setReason] = useState("machine_repair");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [note, setNote] = useState("");

  const fetchDelays = () => {
    if (!token) return;
    staffApi.listDelays(token).then(setDelays).catch(() => setDelays([]));
  };

  useEffect(() => { fetchDelays(); }, [token]);

  const handleCreate = async () => {
    if (!token) return;
    try {
      await staffApi.reportDelay(token, { reason, affected_date: date, note: note || undefined });
      toast.success("Delay reported!");
      setShowCreate(false); setNote(""); fetchDelays();
    } catch (err: any) { toast.error(err.message); }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("delays.title")}
        description={t("delays.description")}
        icon={<Ban className="w-6 h-6 text-primary-foreground" />}
        actions={
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="rounded-xl font-semibold gradient-primary border-0 text-primary-foreground hover:opacity-90">
                <Plus className="h-4 w-4 mr-1.5" /> {t("delays.report")}
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-2xl">
              <DialogHeader><DialogTitle className="font-display">{t("delays.report_a")}</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <Label className="text-sm font-medium">{t("delays.reason")}</Label>
                  <Select value={reason} onValueChange={setReason}>
                    <SelectTrigger className="rounded-xl"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="machine_repair">{t("delays.machine_repair")}</SelectItem>
                      <SelectItem value="water_shortage">{t("delays.water_shortage")}</SelectItem>
                      <SelectItem value="power_cut">{t("delays.power_cut")}</SelectItem>
                      <SelectItem value="staff_shortage">{t("delays.staff_shortage")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-sm font-medium">{t("delays.affected_date")}</Label>
                  <Input type="date" value={date} onChange={e => setDate(e.target.value)} className="rounded-xl h-11" />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-sm font-medium">{t("delays.note")}</Label>
                  <Textarea value={note} onChange={e => setNote(e.target.value)} rows={2} className="rounded-xl" />
                </div>
                <Button onClick={handleCreate} className="w-full rounded-xl h-11 font-semibold">{t("delays.submit_report")}</Button>
              </div>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="space-y-4">
        {delays.map((d, i) => (
          <AnimatedCard key={d.id} delay={0.1 + i * 0.05}>
            <CardContent className="pt-5">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-warning/10 flex items-center justify-center flex-shrink-0">
                    <AlertTriangle className="h-5 w-5 text-warning" />
                  </div>
                  <div>
                    <p className="font-semibold capitalize">{d.reason.replace("_", " ")}</p>
                    <p className="text-sm text-muted-foreground">{d.affected_date}</p>
                    {d.note && <p className="text-sm mt-1.5">{d.note}</p>}
                  </div>
                </div>
                <Badge variant={d.notification_sent ? "default" : "secondary"} className="rounded-lg self-start">
                  <Bell className="h-3 w-3 mr-1" />
                  {d.notification_sent ? t("delays.notified") : t("delays.no_notification")}
                </Badge>
              </div>
            </CardContent>
          </AnimatedCard>
        ))}
        {delays.length === 0 && <p className="text-center text-muted-foreground py-12 font-medium">{t("delays.no_delays")}</p>}
      </div>
    </div>
  );
}
