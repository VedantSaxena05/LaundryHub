import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { slotsApi, type SlotAvailability, type Slot } from "@/api/slots";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { toast } from "sonner";
import { Calendar, Clock, CheckCircle, XCircle, Timer } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";

export default function SlotsPage() {
  const { token } = useAuth();
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [availability, setAvailability] = useState<SlotAvailability | null>(null);
  const [mySlots, setMySlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(false);
  const [startTime, setStartTime] = useState("10:00");
  const [submissionWindow, setSubmissionWindow] = useState(30);

  const startMinutes = parseInt(startTime.split(":")[0]) * 60 + parseInt(startTime.split(":")[1] || "0");
  const maxWindow = Math.min(60, Math.max(10, 14 * 60 - startMinutes));

  useEffect(() => {
    if (submissionWindow > maxWindow) setSubmissionWindow(maxWindow);
  }, [maxWindow]);

  const fetchData = () => {
    if (!token) return;
    slotsApi.getAvailability(token, date).then(setAvailability).catch(() => setAvailability(null));
    slotsApi.getMy(token).then(setMySlots).catch(() => setMySlots([]));
  };

  useEffect(() => { fetchData(); }, [token, date]);

  const handleBook = async () => {
    if (!token) return;
    setLoading(true);
    try {
      await slotsApi.book(token, date, startTime, submissionWindow);
      toast.success("Slot booked successfully!");
      fetchData();
    } catch (err: any) {
      toast.error(err.message || "Booking failed");
    } finally { setLoading(false); }
  };

  const handleCancel = async (slotId: string) => {
    if (!token) return;
    try {
      await slotsApi.cancel(token, slotId);
      toast.success("Slot cancelled");
      fetchData();
    } catch (err: any) {
      toast.error(err.message || "Cancel failed");
    }
  };

  const formatTime = (iso?: string) => {
    if (!iso) return null;
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const endTimeLabel = () => {
    const endMin = startMinutes + submissionWindow;
    const h = String(Math.floor(endMin / 60)).padStart(2, "0");
    const m = String(endMin % 60).padStart(2, "0");
    return `${h}:${m}`;
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Book a Slot"
        description="Check availability and book your laundry slot"
        icon={<Calendar className="w-6 h-6 text-primary-foreground" />}
      />

      <AnimatedCard delay={0.1}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-display"><Calendar className="h-5 w-5 text-primary" /> Select Date & Window</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">Date</Label>
              <Input type="date" value={date} onChange={e => setDate(e.target.value)} className="h-11 rounded-xl" />
            </div>
            <div className="space-y-1.5">
              <Label className="flex items-center gap-2 text-sm font-medium"><Clock className="h-4 w-4 text-muted-foreground" /> Arrival Time</Label>
              <Input type="time" value={startTime} onChange={e => setStartTime(e.target.value)} min="10:00" max="13:50" step="600" className="h-11 rounded-xl" />
              <p className="text-xs text-muted-foreground">Between 10:00 and 13:50</p>
            </div>
          </div>
          <div className="space-y-3">
            <Label className="flex items-center gap-2 text-sm font-medium">
              <Timer className="h-4 w-4 text-muted-foreground" /> Window Duration: <span className="font-bold text-primary">{submissionWindow} min</span>
            </Label>
            <Slider value={[submissionWindow]} onValueChange={v => setSubmissionWindow(v[0])} min={10} max={maxWindow} step={5} className="w-full" />
            <p className="text-xs text-muted-foreground">
              Drop-off window: <span className="font-semibold text-foreground">{startTime} – {endTimeLabel()}</span>
            </p>
          </div>
          <Button onClick={handleBook} disabled={loading} className="w-full h-12 rounded-xl font-semibold gradient-primary border-0 text-primary-foreground hover:opacity-90 transition-all">
            {loading ? "Booking..." : "Book Slot"}
          </Button>
        </CardContent>
      </AnimatedCard>

      {availability && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {availability.blocks.map((b, i) => (
            <AnimatedCard key={b.block} delay={0.2 + i * 0.08} className="group hover:scale-[1.02]">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between font-display">
                  <span>Block {b.block}</span>
                  {b.is_available ? (
                    <Badge className="bg-success text-success-foreground rounded-lg">Available</Badge>
                  ) : (
                    <Badge variant="destructive" className="rounded-lg">Full</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground"><Clock className="h-3.5 w-3.5" /><span>Drop-off: {b.dropoff_window}</span></div>
                <div className="flex items-center gap-2 text-muted-foreground"><Clock className="h-3.5 w-3.5" /><span>Collection: {b.collection_window}</span></div>
                <div className="flex items-center justify-between pt-3 border-t border-border/50">
                  <span className="text-muted-foreground font-medium">Remaining</span>
                  <span className="font-extrabold text-xl font-display">{b.remaining} / {b.block_limit}</span>
                </div>
              </CardContent>
            </AnimatedCard>
          ))}
        </div>
      )}

      {mySlots.length > 0 && (
        <AnimatedCard delay={0.5}>
          <CardHeader><CardTitle className="font-display text-lg">My Slots</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mySlots.map(s => (
                <div key={s.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-accent/30 border border-border/50 gap-3">
                  <div className="flex items-center gap-3">
                    {s.status === "booked" ? <CheckCircle className="h-5 w-5 text-success flex-shrink-0" /> : <XCircle className="h-5 w-5 text-destructive flex-shrink-0" />}
                    <div>
                      <p className="font-semibold">{s.date}</p>
                      <p className="text-xs text-muted-foreground">
                        #{s.month_index}{s.block ? ` · Block ${s.block}` : ""}
                        {s.submission_start_time ? ` · ${s.submission_start_time}` : ""}
                        {s.submission_window_minutes ? ` (${s.submission_window_minutes}min)` : ""}
                      </p>
                      {s.submission_expires_at && s.status === "booked" && (
                        <p className="text-xs text-muted-foreground">Drop-off by {formatTime(s.submission_expires_at)}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={s.status === "booked" ? "default" : "secondary"} className="rounded-lg">{s.status}</Badge>
                    {s.status === "booked" && (
                      <Button variant="ghost" size="sm" className="text-destructive rounded-xl" onClick={() => handleCancel(s.id)}>Cancel</Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </AnimatedCard>
      )}
    </div>
  );
}
