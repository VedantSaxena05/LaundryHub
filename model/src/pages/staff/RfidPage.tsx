import { useEffect, useState, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { rfidApi, type RfidTag, type ScanResult } from "@/api/devices";
import { devicesApi, type Device } from "@/api/devices";
import { BAG_STATUS_LABELS } from "@/api/bags";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Tag, Scan, Link, Unlink, CreditCard, Package } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";
import { useLanguage } from "@/i18n/LanguageContext";

export default function RfidPage() {
  const { token } = useAuth();
  const { t } = useLanguage();
  const [tags, setTags] = useState<RfidTag[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);

  // Enrollment
  const [linkTag, setLinkTag] = useState("");
  const [linkStudent, setLinkStudent] = useState("");
  const [linkType, setLinkType] = useState<"bag" | "id_card">("bag");

  // Scan
  const [scanTag, setScanTag] = useState("");
  const [scanDevice, setScanDevice] = useState("");
  const [scanType, setScanType] = useState("dropoff");
  const [lastScan, setLastScan] = useState<ScanResult | null>(null);
  /** Stored bag_id from pickup_bag step for the pickup_id follow-up */
  const [pendingBagId, setPendingBagId] = useState<string | null>(null);
  /**
   * Use a ref to always hold the latest pendingBagId value so that
   * handleScan (which closes over state) reads the committed value
   * rather than a stale snapshot.
   */
  const pendingBagIdRef = useRef<string | null>(null);

  // Keep ref in sync with state
  useEffect(() => {
    pendingBagIdRef.current = pendingBagId;
  }, [pendingBagId]);

  const fetchData = () => {
    if (!token) return;
    rfidApi.listTags(token).then(setTags).catch(() => setTags([]));
    devicesApi.list(token).then(setDevices).catch(() => setDevices([]));
  };

  useEffect(() => { fetchData(); }, [token]);

  const handleLink = async () => {
    if (!token) return;
    try {
      if (linkType === "bag") {
        await rfidApi.linkBagTag(token, { tag_uid: linkTag, student_id: linkStudent });
      } else {
        await rfidApi.linkIdCard(token, { tag_uid: linkTag, student_id: linkStudent });
      }
      toast.success(`${linkType === "bag" ? "Bag tag" : "ID card"} linked!`);
      setLinkTag(""); setLinkStudent(""); fetchData();
    } catch (err: any) { toast.error(err.message); }
  };

  const handleUnlink = async (tagUid: string) => {
    if (!token) return;
    try {
      await rfidApi.unlinkTag(token, tagUid);
      toast.success("Tag unlinked!");
      fetchData();
    } catch (err: any) { toast.error(err.message); }
  };

  const handleScan = async () => {
    if (!token) return;
    try {
      const scanData: { tag_uid: string; device_id: string; scan_type: string; bag_id?: string } = {
        tag_uid: scanTag,
        device_id: scanDevice,
        scan_type: scanType,
      };

      // For pickup_id, read bag_id from the ref so we always get the
      // latest committed value, even if the state setter hasn't caused
      // a re-render yet when this closure was created.
      if (scanType === "pickup_id") {
        const bagId = pendingBagIdRef.current;
        if (!bagId) {
          toast.error("No pending bag found. Please scan the bag tag first (Step 1).");
          return;
        }
        scanData.bag_id = bagId;
      }

      const result = await rfidApi.scan(token, scanData);
      setLastScan(result);

      if (result.result === "success") {
        toast.success(result.message);
        // After successful pickup_bag, store bag_id and auto-switch to pickup_id
        if (scanType === "pickup_bag" && result.bag_id) {
          pendingBagIdRef.current = result.bag_id;   // update ref immediately
          setPendingBagId(result.bag_id);
          setScanType("pickup_id");
          setScanTag(""); // Clear for ID card UID
          toast.info("Now scan the student's college ID card to confirm pickup.");
        }
        // After successful pickup_id, clear the pending state
        if (scanType === "pickup_id") {
          pendingBagIdRef.current = null;
          setPendingBagId(null);
        }
      } else {
        toast.warning(result.message);
      }
    } catch (err: any) { toast.error(err.message); }
  };

  const activeDevices = devices.filter(d => d.is_active);

  const scanResultVariant = (result: string) => {
    switch (result) {
      case "success": return "default";
      case "wrong_state": return "secondary";
      default: return "destructive";
    }
  };

  const tagTypeLabel = (type: string) => type === "id_card" ? "ID Card" : "Bag Tag";

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("rfid.title")}
        description="Enroll tags & ID cards, process scans"
        icon={<Tag className="w-6 h-6 text-primary-foreground" />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Enrollment Card */}
        <AnimatedCard delay={0.1}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-display"><Link className="h-5 w-5 text-primary" /> Enroll Tag / ID Card</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">Type</Label>
              <Select value={linkType} onValueChange={(v) => setLinkType(v as "bag" | "id_card")}>
                <SelectTrigger className="rounded-xl h-11"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="bag">
                    <span className="flex items-center gap-2"><Package className="h-4 w-4" /> Bag Tag</span>
                  </SelectItem>
                  <SelectItem value="id_card">
                    <span className="flex items-center gap-2"><CreditCard className="h-4 w-4" /> College ID Card</span>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">{t("rfid.tag_uid")}</Label>
              <Input value={linkTag} onChange={e => setLinkTag(e.target.value)} placeholder={linkType === "bag" ? "A1B2C3D4" : "E5F6A7B8"} className="rounded-xl h-11" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">{t("rfid.student_id")}</Label>
              <Input value={linkStudent} onChange={e => setLinkStudent(e.target.value)} placeholder="UUID" className="rounded-xl h-11" />
            </div>
            <Button onClick={handleLink} className="w-full rounded-xl h-11 font-semibold">
              {linkType === "bag" ? "Link Bag Tag" : "Link ID Card"}
            </Button>
          </CardContent>
        </AnimatedCard>

        {/* Scan Card */}
        <AnimatedCard delay={0.2}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-display"><Scan className="h-5 w-5 text-primary" /> Process Scan</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Pickup flow indicator */}
            {pendingBagId && (
              <div className="p-3 rounded-xl bg-warning/10 border border-warning/30 text-sm">
                <span className="font-semibold text-warning">Step 2 of 2:</span>{" "}
                <span className="text-muted-foreground">Scan student's college ID card to confirm pickup.</span>
              </div>
            )}
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">
                {scanType === "pickup_id" ? "ID Card UID" : "Tag UID"}
              </Label>
              <Input value={scanTag} onChange={e => setScanTag(e.target.value)} placeholder={scanType === "pickup_id" ? "E5F6A7B8" : "A1B2C3D4"} className="rounded-xl h-11" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">{t("rfid.device")}</Label>
              <Select value={scanDevice} onValueChange={setScanDevice}>
                <SelectTrigger className="rounded-xl h-11"><SelectValue placeholder="Select device" /></SelectTrigger>
                <SelectContent>
                  {activeDevices.map(d => <SelectItem key={d.id} value={d.id}>{d.device_name} ({d.location_tag})</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">{t("rfid.scan_type")}</Label>
              <Select value={scanType} onValueChange={(v) => {
                setScanType(v);
                if (v !== "pickup_id") {
                  pendingBagIdRef.current = null;
                  setPendingBagId(null);
                }
              }}>
                <SelectTrigger className="rounded-xl h-11"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="dropoff">Drop-off</SelectItem>
                  <SelectItem value="ready">Ready</SelectItem>
                  <SelectItem value="pickup_bag">Pickup — Bag Tag (Step 1)</SelectItem>
                  <SelectItem value="pickup_id">Pickup — ID Card (Step 2)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleScan} className="w-full rounded-xl h-11 font-semibold">Process Scan</Button>

            {lastScan && (
              <div className="mt-4 p-4 rounded-xl bg-accent/30 border border-border/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold">Last Scan Result</span>
                  <Badge variant={scanResultVariant(lastScan.result)}>{lastScan.result}</Badge>
                </div>
                <p className="text-sm text-muted-foreground">{lastScan.message}</p>
                {lastScan.student_name && (
                  <p className="text-sm"><span className="font-medium">Student:</span> {lastScan.student_name}</p>
                )}
                {lastScan.bag_status && (
                  <p className="text-sm"><span className="font-medium">Bag Status:</span> {BAG_STATUS_LABELS[lastScan.bag_status] ?? lastScan.bag_status}</p>
                )}
                {lastScan.pickup_tapped_by_student_name && (
                  <p className="text-sm"><span className="font-medium">ID Tapped By:</span> {lastScan.pickup_tapped_by_student_name}</p>
                )}
              </div>
            )}
          </CardContent>
        </AnimatedCard>
      </div>

      {/* Linked Tags */}
      <AnimatedCard delay={0.3}>
        <CardHeader><CardTitle className="flex items-center gap-2 font-display text-lg"><Tag className="h-5 w-5 text-primary" /> Linked Tags</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-3">
            {tags.map(t => (
              <div key={t.tag_uid} className="flex items-center justify-between p-4 rounded-xl bg-accent/30 border border-border/50">
                <div className="flex items-center gap-3">
                  {t.tag_type === "id_card" ? (
                    <CreditCard className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Package className="h-4 w-4 text-muted-foreground" />
                  )}
                  <div>
                    <span className="font-mono font-semibold">{t.tag_uid}</span>
                    <Badge variant="outline" className="ml-2 rounded-lg text-xs">{tagTypeLabel(t.tag_type)}</Badge>
                    {t.student_id && (
                      <span className="text-sm text-muted-foreground ml-3">Student: {t.student_id.slice(0, 8)}...</span>
                    )}
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={() => handleUnlink(t.tag_uid)} className="rounded-xl">
                  <Unlink className="h-4 w-4 text-muted-foreground" />
                </Button>
              </div>
            ))}
            {tags.length === 0 && <p className="text-center text-muted-foreground py-8 font-medium">No tags linked yet</p>}
          </div>
        </CardContent>
      </AnimatedCard>
    </div>
  );
}