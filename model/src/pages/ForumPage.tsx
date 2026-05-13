import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { forumApi, type ForumPost } from "@/api/forum";
import { CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { MessageSquare, ThumbsUp, Pin, Plus, Send } from "lucide-react";
import { AnimatedCard } from "@/components/AnimatedCard";
import { PageHeader } from "@/components/PageHeader";
import { useLanguage } from "@/i18n/LanguageContext";

export default function ForumPage() {
  const { token, role } = useAuth();
  const { t } = useLanguage();
  const [posts, setPosts] = useState<ForumPost[]>([]);
  const [category, setCategory] = useState<string>("all");
  const [showCreate, setShowCreate] = useState(false);
  const [replyTo, setReplyTo] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [postCat, setPostCat] = useState("general");
  const [isAnon, setIsAnon] = useState(false);
  const [replyBody, setReplyBody] = useState("");
  const [replyAnon, setReplyAnon] = useState(false);

  const fetchPosts = () => {
    if (!token) return;
    forumApi.list(token, category === "all" ? undefined : category).then(setPosts).catch(() => setPosts([]));
  };

  useEffect(() => { fetchPosts(); }, [token, category]);

  const handleCreate = async () => {
    if (!token) return;
    try {
      await forumApi.create(token, { category: postCat, title, body, is_anonymous: isAnon });
      toast.success("Post created!");
      setShowCreate(false);
      setTitle(""); setBody("");
      fetchPosts();
    } catch (err: any) { toast.error(err.message); }
  };

  const handleUpvote = async (postId: string) => {
    if (!token) return;
    try { await forumApi.upvote(token, postId); toast.success("Upvoted!"); fetchPosts(); }
    catch (err: any) { toast.error(err.message); }
  };

  const handlePin = async (postId: string) => {
    if (!token) return;
    try { await forumApi.pin(token, postId); toast.success("Post pinned!"); fetchPosts(); }
    catch (err: any) { toast.error(err.message); }
  };

  const handleReply = async () => {
    if (!token || !replyTo) return;
    try {
      await forumApi.reply(token, replyTo, { body: replyBody, is_anonymous: replyAnon });
      toast.success("Reply posted!"); setReplyTo(null); setReplyBody("");
    } catch (err: any) { toast.error(err.message); }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("forum.title")}
        description={t("forum.description")}
        icon={<MessageSquare className="w-6 h-6 text-primary-foreground" />}
        actions={
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button className="rounded-xl font-semibold gradient-primary border-0 text-primary-foreground hover:opacity-90">
                <Plus className="h-4 w-4 mr-1.5" /> {t("forum.new_post")}
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-2xl">
              <DialogHeader><DialogTitle className="font-display">{t("forum.create_post")}</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <Label className="text-sm font-medium">{t("forum.category")}</Label>
                  <Select value={postCat} onValueChange={setPostCat}>
                    <SelectTrigger className="rounded-xl"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">{t("forum.general")}</SelectItem>
                      <SelectItem value="tips">{t("forum.tips")}</SelectItem>
                      <SelectItem value="announcements">{t("forum.announcements")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-sm font-medium">{t("forum.title_field")}</Label>
                  <Input value={title} onChange={e => setTitle(e.target.value)} className="rounded-xl" />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-sm font-medium">{t("forum.body")}</Label>
                  <Textarea value={body} onChange={e => setBody(e.target.value)} rows={4} className="rounded-xl" />
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={isAnon} onCheckedChange={setIsAnon} />
                  <Label className="text-sm">{t("forum.post_anonymously")}</Label>
                </div>
                <Button onClick={handleCreate} className="w-full rounded-xl font-semibold h-11">{t("common.post")}</Button>
              </div>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="flex flex-wrap gap-2 opacity-0 animate-fade-in" style={{ animationDelay: '0.1s' }}>
        {["all", "general", "tips", "announcements"].map(c => (
          <Button key={c} variant={category === c ? "default" : "outline"} size="sm" onClick={() => setCategory(c)} className="capitalize rounded-xl font-medium">{c}</Button>
        ))}
      </div>

      <div className="space-y-4">
        {posts.map((p, i) => (
          <AnimatedCard key={p.id} delay={0.15 + i * 0.05} className="hover:scale-[1.005]">
            <CardContent className="pt-5">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    {p.is_pinned && <Pin className="h-3.5 w-3.5 text-warning" />}
                    <Badge variant="outline" className="text-xs rounded-lg capitalize">{p.category}</Badge>
                    {p.is_anonymous && <Badge variant="secondary" className="text-xs rounded-lg">{t("forum.anonymous")}</Badge>}
                  </div>
                  <h3 className="font-bold text-base">{p.title}</h3>
                  <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">{p.body}</p>
                  <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                    <span>{new Date(p.created_at).toLocaleDateString()}</span>
                    {p.author_name && !p.is_anonymous && <span>by {p.author_name}</span>}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border/50">
                <Button variant="ghost" size="sm" onClick={() => handleUpvote(p.id)} className="rounded-xl">
                  <ThumbsUp className="h-3.5 w-3.5 mr-1.5" /> {p.upvotes ?? 0}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setReplyTo(replyTo === p.id ? null : p.id)} className="rounded-xl">
                  <MessageSquare className="h-3.5 w-3.5 mr-1.5" /> {t("common.reply")}
                </Button>
                {role === "admin" && (
                  <Button variant="ghost" size="sm" onClick={() => handlePin(p.id)} className="rounded-xl">
                    <Pin className="h-3.5 w-3.5 mr-1.5" /> {t("forum.pin")}
                  </Button>
                )}
              </div>
              {replyTo === p.id && (
                <div className="mt-4 space-y-3 p-4 bg-accent/30 rounded-xl border border-border/50">
                  <Textarea value={replyBody} onChange={e => setReplyBody(e.target.value)} placeholder={t("forum.write_reply")} rows={2} className="rounded-xl" />
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Switch checked={replyAnon} onCheckedChange={setReplyAnon} />
                      <Label className="text-xs font-medium">{t("forum.anonymous")}</Label>
                    </div>
                    <Button size="sm" onClick={handleReply} className="rounded-xl"><Send className="h-3.5 w-3.5 mr-1.5" /> {t("common.reply")}</Button>
                  </div>
                </div>
              )}
            </CardContent>
          </AnimatedCard>
        ))}
        {posts.length === 0 && <p className="text-center text-muted-foreground py-12 font-medium">{t("forum.no_posts")}</p>}
      </div>
    </div>
  );
}
