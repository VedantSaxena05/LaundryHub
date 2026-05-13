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

export default function AdminSlotsPage() {
  const { token } = useAuth();
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
        title="Slots Configuration"
        description="Manage per-block daily slot limits and expiry"
        icon={<Calendar className="w-6 h-6 text-primary-foreground" />}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl">
        <AnimatedCard delay={0.1}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-display"><Settings className="h-5 w-5 text-primary" /> Update Block Limit</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">Block</Label>
              <Select value={block} onValueChange={setBlock}>
                <SelectTrigger className="rounded-xl h-11"><SelectValue /></SelectTrigger>
                <SelectContent>{["A","B","C","D","E"].map(b => <SelectItem key={b} value={b}>Block {b}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">New Daily Limit</Label>
              <Input type="number" value={limit} onChange={e => setLimit(e.target.value)} min="1" className="rounded-xl h-11" />
            </div>
            <Button onClick={handleUpdate} className="w-full rounded-xl h-11 font-semibold">Update Limit</Button>
          </CardContent>
        </AnimatedCard>

        <AnimatedCard delay={0.2}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-display"><TimerOff className="h-5 w-5 text-destructive" /> Expire Lapsed Slots</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground leading-relaxed">
              Cancel all booked slots whose submission window has expired without a bag drop-off, freeing capacity for other students.
            </p>
            <Button onClick={handleExpireLapsed} disabled={expiring} variant="destructive" className="w-full rounded-xl h-11 font-semibold">
              {expiring ? "Processing..." : "Expire Lapsed Slots"}
            </Button>
          </CardContent>
        </AnimatedCard>
      </div>
    </div>
  );
}
