import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { devicesApi, type Device } from "@/api/devices";
import { CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Cpu, Plus, Trash2 } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";
import { useLanguage } from "@/i18n/LanguageContext";

export default function DevicesPage() {
  const { token, role } = useAuth();
  const { t } = useLanguage();
  const [devices, setDevices] = useState<Device[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [location, setLocation] = useState("dropoff");

  const fetchDevices = () => {
    if (!token) return;
    devicesApi.list(token).then(setDevices).catch(() => setDevices([]));
  };

  useEffect(() => { fetchDevices(); }, [token]);

  const handleCreate = async () => {
    if (!token) return;
    try {
      await devicesApi.register(token, { device_name: name, location_tag: location });
      toast.success("Device registered!"); setShowCreate(false); setName(""); fetchDevices();
    } catch (err: any) { toast.error(err.message); }
  };

  const handleDeactivate = async (id: string) => {
    if (!token) return;
    try { await devicesApi.deactivate(token, id); toast.success("Device deactivated!"); fetchDevices(); }
    catch (err: any) { toast.error(err.message); }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("devices.title")}
        description={t("devices.description")}
        icon={<Cpu className="w-6 h-6 text-primary-foreground" />}
        actions={
          role === "admin" ? (
            <Dialog open={showCreate} onOpenChange={setShowCreate}>
              <DialogTrigger asChild>
                <Button className="rounded-xl font-semibold gradient-primary border-0 text-primary-foreground hover:opacity-90">
                  <Plus className="h-4 w-4 mr-1.5" /> {t("devices.add")}
                </Button>
              </DialogTrigger>
              <DialogContent className="rounded-2xl">
                <DialogHeader><DialogTitle className="font-display">{t("devices.register")}</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <Label className="text-sm font-medium">{t("devices.name")}</Label>
                    <Input value={name} onChange={e => setName(e.target.value)} placeholder="Scanner-1" className="rounded-xl h-11" />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-sm font-medium">{t("devices.location")}</Label>
                    <Select value={location} onValueChange={setLocation}>
                      <SelectTrigger className="rounded-xl h-11"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="dropoff">{t("slots.dropoff")}</SelectItem>
                        <SelectItem value="collection">{t("slots.collection")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button onClick={handleCreate} className="w-full rounded-xl h-11 font-semibold">{t("common.register")}</Button>
                </div>
              </DialogContent>
            </Dialog>
          ) : undefined
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {devices.map((d, i) => (
          <AnimatedCard key={d.id} delay={0.1 + i * 0.05} className="group hover:scale-[1.01]">
            <CardContent className="pt-5">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Cpu className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold">{d.device_name}</p>
                    <p className="text-sm text-muted-foreground capitalize">{d.location_tag}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={d.is_active ? "default" : "secondary"} className="rounded-lg">{d.is_active ? t("common.active") : t("common.inactive")}</Badge>
                  {role === "admin" && d.is_active && (
                    <Button variant="ghost" size="icon" className="text-destructive rounded-xl hover:bg-destructive/10" onClick={() => handleDeactivate(d.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </AnimatedCard>
        ))}
        {devices.length === 0 && <p className="text-center text-muted-foreground py-12 col-span-3 font-medium">{t("devices.no_devices")}</p>}
      </div>
    </div>
  );
}
