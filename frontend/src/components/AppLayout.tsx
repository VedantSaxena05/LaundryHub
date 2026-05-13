import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { NavLink } from "@/components/NavLink";
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

const studentLinks = [
  { title: "Dashboard", url: "/dashboard", icon: Home },
  { title: "Book Slot", url: "/slots", icon: Calendar },
  { title: "My Bags", url: "/bags", icon: Package },
  { title: "Forum", url: "/forum", icon: MessageSquare },
  { title: "Lost & Found", url: "/lost-found", icon: Search },
];

const staffLinks = [
  { title: "Dashboard", url: "/dashboard", icon: Home },
  { title: "Today's Ops", url: "/staff/today", icon: Clock },
  { title: "Delays", url: "/staff/delays", icon: Ban },
  { title: "Blocked Dates", url: "/staff/blocked-dates", icon: Calendar },
  { title: "RFID Scan", url: "/staff/rfid", icon: Tag },
  { title: "Devices", url: "/staff/devices", icon: Cpu },
  { title: "Forum", url: "/forum", icon: MessageSquare },
];

const adminLinks = [
  { title: "Dashboard", url: "/dashboard", icon: Home },
  { title: "Analytics", url: "/admin/analytics", icon: BarChart3 },
  { title: "Students", url: "/admin/students", icon: Users },
  { title: "Staff", url: "/admin/staff", icon: Shield },
  { title: "Devices", url: "/admin/devices", icon: Cpu },
  { title: "Slots Config", url: "/admin/slots", icon: Calendar },
  { title: "Today's Ops", url: "/staff/today", icon: Clock },
  { title: "Delays", url: "/staff/delays", icon: Ban },
  { title: "Blocked Dates", url: "/staff/blocked-dates", icon: Calendar },
  { title: "RFID Scan", url: "/staff/rfid", icon: Tag },
  { title: "Forum", url: "/forum", icon: MessageSquare },
];

function AppSidebarContent() {
  const { role, logout } = useAuth();
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const navigate = useNavigate();

  const links = role === "admin" ? adminLinks : role === "staff" ? staffLinks : studentLinks;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <Sidebar collapsible="icon" className="border-r-0">
      <SidebarContent className="flex flex-col h-full bg-sidebar">
        <div className="p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl gradient-primary flex items-center justify-center flex-shrink-0 shadow-card">
            <Shirt className="w-5 h-5 text-primary-foreground" />
          </div>
          {!collapsed && <span className="font-extrabold font-display text-gradient text-xl tracking-tight">LaundryHub</span>}
        </div>
        <SidebarGroup className="flex-1">
          <SidebarGroupLabel className="px-4 text-[10px] uppercase tracking-widest font-bold text-muted-foreground/70">
            {!collapsed && (role === "admin" ? "Admin" : role === "staff" ? "Staff" : "Student")}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="px-2 space-y-1">
              {links.map((item, i) => (
                <SidebarMenuItem key={item.url + item.title} style={{ animationDelay: `${i * 0.03}s` }} className="opacity-0 animate-fade-in">
                  <SidebarMenuButton asChild>
                    <NavLink to={item.url} end className="rounded-xl px-3 py-2.5 hover:bg-accent/60 transition-all duration-200 group" activeClassName="bg-accent text-accent-foreground font-semibold shadow-sm">
                      <item.icon className="mr-3 h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                      {!collapsed && <span className="text-sm">{item.title}</span>}
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
            {!collapsed && <span className="ml-2 text-sm font-medium">Sign Out</span>}
          </Button>
        </div>
      </SidebarContent>
    </Sidebar>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { role } = useAuth();

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <AppSidebarContent />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-16 flex items-center border-b border-border/50 bg-card/80 glass px-4 md:px-6 gap-3 sticky top-0 z-30">
            <SidebarTrigger className="rounded-xl" />
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse-soft" />
              <span className="text-sm font-semibold text-muted-foreground capitalize">{role} Portal</span>
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
