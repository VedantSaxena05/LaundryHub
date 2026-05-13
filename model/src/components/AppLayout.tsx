import { useAuth } from "@/contexts/AuthContext";
import { useLanguage } from "@/i18n/LanguageContext";
import { useNavigate } from "react-router-dom";
import { NavLink } from "@/components/NavLink";
import { LanguageToggle } from "@/components/LanguageToggle";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarProvider, SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import {
  Shirt, Calendar, Package, MessageSquare, Search, BarChart3, Users, Shield,
  Clock, Ban, Cpu, Tag, LogOut, Home,
} from "lucide-react";
import type { TranslationKey } from "@/i18n/translations";

const studentLinks: { titleKey: TranslationKey; url: string; icon: any }[] = [
  { titleKey: "nav.dashboard", url: "/dashboard", icon: Home },
  { titleKey: "nav.book_slot", url: "/slots", icon: Calendar },
  { titleKey: "nav.my_bags", url: "/bags", icon: Package },
  { titleKey: "nav.forum", url: "/forum", icon: MessageSquare },
  { titleKey: "nav.lost_found", url: "/lost-found", icon: Search },
];

const staffLinks: { titleKey: TranslationKey; url: string; icon: any }[] = [
  { titleKey: "nav.dashboard", url: "/dashboard", icon: Home },
  { titleKey: "nav.today_ops", url: "/staff/today", icon: Clock },
  { titleKey: "nav.delays", url: "/staff/delays", icon: Ban },
  { titleKey: "nav.blocked_dates", url: "/staff/blocked-dates", icon: Calendar },
  { titleKey: "nav.rfid_scan", url: "/staff/rfid", icon: Tag },
  { titleKey: "nav.devices", url: "/staff/devices", icon: Cpu },
  { titleKey: "nav.forum", url: "/forum", icon: MessageSquare },
];

const adminLinks: { titleKey: TranslationKey; url: string; icon: any }[] = [
  { titleKey: "nav.dashboard", url: "/dashboard", icon: Home },
  { titleKey: "nav.analytics", url: "/admin/analytics", icon: BarChart3 },
  { titleKey: "nav.students", url: "/admin/students", icon: Users },
  { titleKey: "nav.staff", url: "/admin/staff", icon: Shield },
  { titleKey: "nav.devices", url: "/admin/devices", icon: Cpu },
  { titleKey: "nav.slots_config", url: "/admin/slots", icon: Calendar },
  { titleKey: "nav.today_ops", url: "/staff/today", icon: Clock },
  { titleKey: "nav.delays", url: "/staff/delays", icon: Ban },
  { titleKey: "nav.blocked_dates", url: "/staff/blocked-dates", icon: Calendar },
  { titleKey: "nav.rfid_scan", url: "/staff/rfid", icon: Tag },
  { titleKey: "nav.forum", url: "/forum", icon: MessageSquare },
];

function AppSidebarContent() {
  const { role, logout } = useAuth();
  const { t } = useLanguage();
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const navigate = useNavigate();

  const links = role === "admin" ? adminLinks : role === "staff" ? staffLinks : studentLinks;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const roleLabel = role === "admin" ? t("role.admin") : role === "staff" ? t("role.staff") : t("role.student");

  return (
    <Sidebar collapsible="icon" className="border-r-0">
      <SidebarContent className="flex flex-col h-full bg-sidebar">
        <div className="p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl gradient-primary flex items-center justify-center flex-shrink-0 shadow-card">
            <Shirt className="w-5 h-5 text-primary-foreground" />
          </div>
          {!collapsed && <span className="font-extrabold font-display text-gradient text-xl tracking-tight">{t("app.name")}</span>}
        </div>
        <SidebarGroup className="flex-1">
          <SidebarGroupLabel className="px-4 text-[10px] uppercase tracking-widest font-bold text-muted-foreground/70">
            {!collapsed && roleLabel}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="px-2 space-y-1">
              {links.map((item, i) => (
                <SidebarMenuItem key={item.url + item.titleKey} style={{ animationDelay: `${i * 0.03}s` }} className="opacity-0 animate-fade-in">
                  <SidebarMenuButton asChild>
                    <NavLink to={item.url} end className="rounded-xl px-3 py-2.5 hover:bg-accent/60 transition-all duration-200 group" activeClassName="bg-accent text-accent-foreground font-semibold shadow-sm">
                      <item.icon className="mr-3 h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                      {!collapsed && <span className="text-sm">{t(item.titleKey)}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <div className="p-3 border-t border-border/50">
          <Button variant="ghost" size={collapsed ? "icon" : "default"} onClick={handleLogout}
            className="w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10 rounded-xl transition-all">
            <LogOut className="h-4 w-4" />
            {!collapsed && <span className="ml-2 text-sm font-medium">{t("nav.sign_out")}</span>}
          </Button>
        </div>
      </SidebarContent>
    </Sidebar>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { role } = useAuth();
  const { t } = useLanguage();

  const roleLabel = role === "admin" ? t("role.admin") : role === "staff" ? t("role.staff") : t("role.student");

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <AppSidebarContent />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-16 flex items-center border-b border-border/50 bg-card/80 glass px-4 md:px-6 gap-3 sticky top-0 z-30">
            <SidebarTrigger className="rounded-xl" />
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse-soft" />
              <span className="text-sm font-semibold text-muted-foreground">{roleLabel} {t("role.portal")}</span>
            </div>
            <div className="ml-auto">
              <LanguageToggle />
            </div>
          </header>
          <main className="flex-1 p-4 md:p-8 overflow-auto">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
