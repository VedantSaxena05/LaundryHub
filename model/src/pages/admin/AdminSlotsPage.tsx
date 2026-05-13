import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { slotsApi } from "@/api/slots";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Settings, TimerOff, Calendar } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";
import { useLanguage } from "@/i18n/LanguageContext";

export default function AdminSlotsPage() {
  const { token } = useAuth();
  const { t } = useLanguage();
  const [block, setBlock] = useState("A");
  const [limit, setLimit] = useState("50");
  const [expiring, setExpiring] = useState(false);

  const handleUpdate = async () => {
    if (!token) return;
    try {
      await slotsApi.updateBlockLimit(token, block, parseInt(limit));
      toast.success(`Block ${block} limit updated to ${limit}!`);
    } catch (err: any) { toast.error(err.message); }
  };

  const handleExpireLapsed = async () => {
    if (!token) return;
    setExpiring(true);
    try {
      const result = await slotsApi.expireLapsed(token);
      toast.success(`Expired ${result.expired_slots} lapsed slot(s)`);
    } catch (err: any) { toast.error(err.message || "Failed to expire lapsed slots"); }
    finally { setExpiring(false); }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("admin_slots.title")}
        description={t("admin_slots.description")}
        icon={<Calendar className="w-6 h-6 text-primary-foreground" />}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl">
        <AnimatedCard delay={0.1}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-display"><Settings className="h-5 w-5 text-primary" /> {t("admin_slots.update_limit")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">{t("common.block")}</Label>
              <Select value={block} onValueChange={setBlock}>
                <SelectTrigger className="rounded-xl h-11"><SelectValue /></SelectTrigger>
                <SelectContent>{["A","B","C","D","E"].map(b => <SelectItem key={b} value={b}>{t("common.block")} {b}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">{t("admin_slots.new_limit")}</Label>
              <Input type="number" value={limit} onChange={e => setLimit(e.target.value)} min="1" className="rounded-xl h-11" />
            </div>
            <Button onClick={handleUpdate} className="w-full rounded-xl h-11 font-semibold">{t("admin_slots.update")}</Button>
          </CardContent>
        </AnimatedCard>

        <AnimatedCard delay={0.2}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-display"><TimerOff className="h-5 w-5 text-destructive" /> {t("admin_slots.expire_title")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground leading-relaxed">
              {t("admin_slots.expire_desc")}
            </p>
            <Button onClick={handleExpireLapsed} disabled={expiring} variant="destructive" className="w-full rounded-xl h-11 font-semibold">
              {expiring ? t("admin_slots.processing") : t("admin_slots.expire_btn")}
            </Button>
          </CardContent>
        </AnimatedCard>
      </div>
    </div>
  );
}
