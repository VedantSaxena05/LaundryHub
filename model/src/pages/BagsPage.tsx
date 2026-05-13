import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { bagsApi, type Bag, type BagLog } from "@/api/bags";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Package, History, ArrowRight } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";
import { useLanguage } from "@/i18n/LanguageContext";

const statusColor = (s: string) => {
  switch (s) {
    case "dropped": return "bg-warning text-warning-foreground";
    case "washing": return "bg-info text-info-foreground";
    case "ready": return "bg-success text-success-foreground";
    case "awaiting_id_scan": return "bg-warning text-warning-foreground";
    case "collected": return "bg-primary text-primary-foreground";
    default: return "bg-muted text-muted-foreground";
  }
};

export default function BagsPage() {
  const { token } = useAuth();
  const { t } = useLanguage();
  const [bag, setBag] = useState<Bag | null>(null);
  const [history, setHistory] = useState<Bag[]>([]);
  const [logs, setLogs] = useState<BagLog[]>([]);
  const [selectedBag, setSelectedBag] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    bagsApi.getMy(token).then(setBag).catch(() => setBag(null));
    bagsApi.getHistory(token).then(setHistory).catch(() => setHistory([]));
  }, [token]);

  const viewLogs = async (bagId: string) => {
    if (!token) return;
    setSelectedBag(bagId);
    try {
      const l = await bagsApi.getLogs(token, bagId);
      setLogs(l);
    } catch { setLogs([]); }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("bags.title")}
        description={t("bags.description")}
        icon={<Package className="w-6 h-6 text-primary-foreground" />}
      />

      {bag ? (
        <AnimatedCard delay={0.1} className="border-l-4 border-l-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-display"><Package className="h-5 w-5 text-primary" /> {t("bags.current")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Date: {bag.date}</p>
                {bag.tag_uid && <p className="text-sm text-muted-foreground">{t("bags.tag")}: {bag.tag_uid}</p>}
              </div>
              <Badge className={`${statusColor(bag.status)} rounded-lg`}>{bag.status}</Badge>
            </div>
            <div className="mt-5 flex flex-wrap items-center gap-2 text-xs">
              {["pending", "dropped", "washing", "ready", "awaiting_id_scan", "collected"].map((step, i, arr) => (
                <span key={step} className="flex items-center gap-1.5">
                  <span className={`px-3 py-1.5 rounded-xl font-medium transition-all ${bag.status === step ? "bg-primary text-primary-foreground shadow-sm" : "bg-muted text-muted-foreground"}`}>
                    {step}
                  </span>
                  {i < arr.length - 1 && <ArrowRight className="h-3 w-3 text-muted-foreground" />}
                </span>
              ))}
            </div>
          </CardContent>
        </AnimatedCard>
      ) : (
        <AnimatedCard delay={0.1}>
          <CardContent className="py-12 text-center text-muted-foreground font-medium">{t("bags.no_active")}</CardContent>
        </AnimatedCard>
      )}

      {history.length > 0 && (
        <AnimatedCard delay={0.2}>
          <CardHeader><CardTitle className="flex items-center gap-2 font-display text-lg"><History className="h-5 w-5 text-primary" /> {t("bags.history")}</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {history.map(b => (
                <div key={b.id} className="flex items-center justify-between p-4 rounded-xl bg-accent/30 border border-border/50 cursor-pointer hover:bg-accent/50 transition-all" onClick={() => viewLogs(b.id)}>
                  <div>
                    <p className="font-semibold">{b.date}</p>
                    <p className="text-xs text-muted-foreground">ID: {b.id.slice(0, 8)}...</p>
                  </div>
                  <Badge className={`${statusColor(b.status)} rounded-lg`}>{b.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </AnimatedCard>
      )}

      {selectedBag && logs.length > 0 && (
        <AnimatedCard delay={0.3}>
          <CardHeader><CardTitle className="font-display text-lg">{t("bags.status_log")}</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {logs.map(l => (
                <div key={l.id} className="flex items-center gap-3 p-3 rounded-xl bg-muted/30 text-sm">
                  <Badge variant="outline" className="rounded-lg">{l.from_status || "—"}</Badge>
                  <ArrowRight className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                  <Badge className="rounded-lg">{l.to_status}</Badge>
                  <span className="text-xs text-muted-foreground ml-auto">{new Date(l.timestamp).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </AnimatedCard>
      )}
    </div>
  );
}
