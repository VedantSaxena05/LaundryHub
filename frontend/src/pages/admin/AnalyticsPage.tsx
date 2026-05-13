import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { adminApi, type SlotAnalytics, type BagAnalytics, type NotificationAnalytics } from "@/api/admin";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { BarChart3, Package, Bell } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";

export default function AnalyticsPage() {
  const { token } = useAuth();
  const today = new Date();
  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split("T")[0];
  const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split("T")[0];

  const [fromDate, setFromDate] = useState(monthStart);
  const [toDate, setToDate] = useState(monthEnd);
  const [slotData, setSlotData] = useState<SlotAnalytics | null>(null);
  const [bagData, setBagData] = useState<BagAnalytics | null>(null);
  const [notifData, setNotifData] = useState<NotificationAnalytics | null>(null);

  const fetchAll = () => {
    if (!token) return;
    adminApi.getSlotAnalytics(token, fromDate, toDate).then(setSlotData).catch(() => {});
    adminApi.getBagAnalytics(token).then(setBagData).catch(() => {});
    adminApi.getNotificationAnalytics(token, fromDate, toDate).then(setNotifData).catch(() => {});
  };

  useEffect(() => { fetchAll(); }, [token]);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Analytics"
        description="Detailed system analytics and reports"
        icon={<BarChart3 className="w-6 h-6 text-primary-foreground" />}
      />

      <AnimatedCard delay={0.1}>
        <CardContent className="pt-5">
          <div className="flex items-end gap-4 flex-wrap">
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">From</Label>
              <Input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} className="h-11 rounded-xl" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">To</Label>
              <Input type="date" value={toDate} onChange={e => setToDate(e.target.value)} className="h-11 rounded-xl" />
            </div>
            <Button onClick={fetchAll} className="rounded-xl h-11 font-semibold">Refresh</Button>
          </div>
        </CardContent>
      </AnimatedCard>

      {slotData && (
        <AnimatedCard delay={0.2}>
          <CardHeader><CardTitle className="flex items-center gap-2 font-display text-lg"><BarChart3 className="h-5 w-5 text-primary" /> Slot Analytics</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 mb-6">
              {[
                { label: "Total Booked", value: slotData.total_booked },
                { label: "Used", value: slotData.used },
                { label: "Cancelled", value: slotData.cancelled },
                { label: "Missed", value: slotData.missed },
                { label: "Utilisation", value: `${(slotData.utilisation_rate * 100).toFixed(1)}%` },
              ].map(item => (
                <div key={item.label} className="text-center p-4 rounded-2xl bg-accent/30 border border-border/50">
                  <p className="text-3xl font-extrabold font-display">{item.value}</p>
                  <p className="text-xs text-muted-foreground font-medium mt-1">{item.label}</p>
                </div>
              ))}
            </div>
            <h4 className="font-semibold font-display mb-3">By Block</h4>
            <div className="space-y-4">
              {Object.entries(slotData.by_block).map(([block, data]) => (
                <div key={block} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-semibold">Block {block}</span>
                    <span className="text-muted-foreground">{data.used} / {data.total_booked} (limit: {data.limit_per_day}/day)</span>
                  </div>
                  <Progress value={data.total_booked > 0 ? (data.used / data.total_booked) * 100 : 0} className="h-2.5 rounded-full" />
                </div>
              ))}
            </div>
          </CardContent>
        </AnimatedCard>
      )}

      {bagData && (
        <AnimatedCard delay={0.3}>
          <CardHeader><CardTitle className="flex items-center gap-2 font-display text-lg"><Package className="h-5 w-5 text-primary" /> Bag Status Distribution</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
              {Object.entries(bagData).map(([status, count]) => (
                <div key={status} className="text-center p-4 rounded-2xl bg-accent/30 border border-border/50">
                  <p className="text-3xl font-extrabold font-display">{count}</p>
                  <p className="text-xs text-muted-foreground capitalize font-medium mt-1">{status}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </AnimatedCard>
      )}

      {notifData && (
        <AnimatedCard delay={0.4}>
          <CardHeader><CardTitle className="flex items-center gap-2 font-display text-lg"><Bell className="h-5 w-5 text-primary" /> Notification Analytics</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Total Sent", value: notifData.total_sent },
                { label: "FCM Success", value: notifData.fcm_success },
                { label: "FCM Failure", value: notifData.fcm_failure },
                { label: "Success Rate", value: `${(notifData.success_rate * 100).toFixed(1)}%` },
              ].map(item => (
                <div key={item.label} className="text-center p-4 rounded-2xl bg-accent/30 border border-border/50">
                  <p className="text-3xl font-extrabold font-display">{item.value}</p>
                  <p className="text-xs text-muted-foreground font-medium mt-1">{item.label}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </AnimatedCard>
      )}
    </div>
  );
}
