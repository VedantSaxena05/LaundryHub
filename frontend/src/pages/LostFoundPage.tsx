import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { lostFoundApi, type LostFoundPost } from "@/api/lostFound";
import { CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Search, Plus, CheckCircle, MapPin, Palette } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";

export default function LostFoundPage() {
  const { token } = useAuth();
  const [posts, setPosts] = useState<LostFoundPost[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [showCreate, setShowCreate] = useState(false);

  const [postType, setPostType] = useState<"lost" | "found">("lost");
  const [description, setDescription] = useState("");
  const [color, setColor] = useState("");
  const [location, setLocation] = useState("");

  const fetchPosts = () => {
    if (!token) return;
    lostFoundApi.list(token, filter === "all" ? undefined : filter, false).then(setPosts).catch(() => setPosts([]));
  };

  useEffect(() => { fetchPosts(); }, [token, filter]);

  const handleCreate = async () => {
    if (!token) return;
    try {
      await lostFoundApi.create(token, { post_type: postType, item_description: description, color, last_seen_location: location });
      toast.success("Post created!");
      setShowCreate(false);
      setDescription(""); setColor(""); setLocation("");
      fetchPosts();
    } catch (err: any) { toast.error(err.message); }
  };

  const handleResolve = async (id: string) => {
    if (!token) return;
    try { await lostFoundApi.resolve(token, id); toast.success("Marked as resolved!"); fetchPosts(); }
    catch (err: any) { toast.error(err.message); }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Lost & Found"
        description="Report lost items or found items"
        icon={<Search className="w-6 h-6 text-primary-foreground" />}
        actions={
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="rounded-xl font-semibold gradient-primary border-0 text-primary-foreground hover:opacity-90">
                <Plus className="h-4 w-4 mr-1.5" /> Report Item
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-2xl">
              <DialogHeader><DialogTitle className="font-display">Report an Item</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <Label className="text-sm font-medium">Type</Label>
                  <Select value={postType} onValueChange={v => setPostType(v as "lost" | "found")}>
                    <SelectTrigger className="rounded-xl"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="lost">Lost</SelectItem>
                      <SelectItem value="found">Found</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-sm font-medium">Description</Label>
                  <Textarea value={description} onChange={e => setDescription(e.target.value)} rows={3} placeholder="Describe the item..." className="rounded-xl" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label className="text-sm font-medium">Color</Label>
                    <Input value={color} onChange={e => setColor(e.target.value)} placeholder="blue" className="rounded-xl" />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-sm font-medium">Last Seen</Label>
                    <Input value={location} onChange={e => setLocation(e.target.value)} placeholder="Block A laundry" className="rounded-xl" />
                  </div>
                </div>
                <Button onClick={handleCreate} className="w-full rounded-xl font-semibold h-11">Submit Report</Button>
              </div>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="flex flex-wrap gap-2 opacity-0 animate-fade-in" style={{ animationDelay: '0.1s' }}>
        {["all", "lost", "found"].map(f => (
          <Button key={f} variant={filter === f ? "default" : "outline"} size="sm" onClick={() => setFilter(f)} className="capitalize rounded-xl font-medium">{f}</Button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {posts.map((p, i) => (
          <AnimatedCard key={p.id} delay={0.15 + i * 0.05} className="group hover:scale-[1.01]">
            <CardContent className="pt-5">
              <div className="flex items-start justify-between mb-3">
                <Badge variant={p.post_type === "lost" ? "destructive" : "default"} className="capitalize rounded-lg">{p.post_type}</Badge>
                {p.resolved && <Badge variant="secondary" className="rounded-lg"><CheckCircle className="h-3 w-3 mr-1" /> Resolved</Badge>}
              </div>
              <p className="font-semibold">{p.item_description}</p>
              <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-muted-foreground">
                <span className="flex items-center gap-1"><Palette className="h-3.5 w-3.5" /> {p.color}</span>
                <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {p.last_seen_location}</span>
              </div>
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-border/50">
                <span className="text-xs text-muted-foreground">{new Date(p.created_at).toLocaleDateString()}</span>
                {!p.resolved && (
                  <Button variant="outline" size="sm" onClick={() => handleResolve(p.id)} className="rounded-xl">
                    <CheckCircle className="h-3.5 w-3.5 mr-1.5" /> Resolve
                  </Button>
                )}
              </div>
            </CardContent>
          </AnimatedCard>
        ))}
        {posts.length === 0 && <p className="text-center text-muted-foreground py-12 col-span-2 font-medium">No items reported</p>}
      </div>
    </div>
  );
}
