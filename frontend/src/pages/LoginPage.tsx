import React, { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { authApi, type StudentRegisterData, type StaffRegisterData } from "@/api/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Shirt, User, Shield, Settings } from "lucide-react";
import { getBaseUrl, setBaseUrl } from "@/api/client";

type LoginRole = "student" | "staff" | "admin";

export default function LoginPage() {
  const { login, setAuthFromResponse } = useAuth();
  const [tab, setTab] = useState<"login" | "register">("login");
  const [loading, setLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [apiUrl, setApiUrl] = useState(getBaseUrl());

  const [loginRole, setLoginRole] = useState<LoginRole>("student");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");

  const [regNum, setRegNum] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [block, setBlock] = useState("A");
  const [floor, setFloor] = useState("1");
  const [room, setRoom] = useState("");
  const [lang, setLang] = useState("en");

  const [staffName, setStaffName] = useState("");
  const [empId, setEmpId] = useState("");
  const [staffPhone, setStaffPhone] = useState("");
  const [staffPassword, setStaffPassword] = useState("");
  const [staffRole, setStaffRole] = useState<"staff" | "admin">("staff");

  const [registerType, setRegisterType] = useState<"student" | "staff">("student");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login({ identifier, password, role: loginRole });
      toast.success("Logged in successfully!");
    } catch (err: any) {
      toast.error(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleStudentRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data: StudentRegisterData = {
        registration_number: regNum, name, email,
        phone_number: phone, password: regPassword,
        block, floor: parseInt(floor), room_number: room,
        language_preference: lang,
      };
      const resp = await authApi.registerStudent(data);
      setAuthFromResponse(resp);
      toast.success("Registration successful!");
    } catch (err: any) {
      toast.error(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const handleStaffRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data: StaffRegisterData = {
        name: staffName, employee_id: empId,
        phone_number: staffPhone, password: staffPassword,
        role: staffRole,
      };
      const resp = await authApi.registerStaff(data);
      setAuthFromResponse(resp);
      toast.success("Registration successful!");
    } catch (err: any) {
      toast.error(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveUrl = () => {
    setBaseUrl(apiUrl);
    toast.success("API URL updated!");
    setShowSettings(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-primary/5 blur-3xl animate-pulse-soft" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-secondary/5 blur-3xl animate-pulse-soft" style={{ animationDelay: '1s' }} />
      </div>

      <div className="w-full max-w-md space-y-8 relative z-10">
        {/* Logo */}
        <div className="text-center space-y-3 opacity-0 animate-fade-in">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl gradient-primary shadow-elevated animate-float">
            <Shirt className="w-10 h-10 text-primary-foreground" />
          </div>
          <h1 className="text-4xl font-extrabold font-display text-gradient tracking-tight">LaundryHub</h1>
          <p className="text-muted-foreground text-sm font-medium">Smart Campus Laundry Management</p>
        </div>

        {/* Card */}
        <Card className="shadow-elevated border-border/50 opacity-0 animate-fade-in-up overflow-hidden" style={{ animationDelay: '0.15s' }}>
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl font-display">Welcome</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setShowSettings(!showSettings)} className="rounded-xl hover:bg-accent">
                <Settings className="w-4 h-4" />
              </Button>
            </div>
            {showSettings && (
              <div className="space-y-2 pt-2 animate-fade-in">
                <Label className="text-xs">API Base URL</Label>
                <div className="flex gap-2">
                  <Input value={apiUrl} onChange={e => setApiUrl(e.target.value)} placeholder="http://localhost:8000" className="text-sm" />
                  <Button size="sm" onClick={handleSaveUrl} className="rounded-xl">Save</Button>
                </div>
              </div>
            )}
          </CardHeader>
          <CardContent>
            <Tabs value={tab} onValueChange={v => setTab(v as "login" | "register")}>
              <TabsList className="grid w-full grid-cols-2 mb-6 h-11 rounded-xl bg-muted/60">
                <TabsTrigger value="login" className="rounded-lg font-semibold text-sm data-[state=active]:shadow-sm">Sign In</TabsTrigger>
                <TabsTrigger value="register" className="rounded-lg font-semibold text-sm data-[state=active]:shadow-sm">Register</TabsTrigger>
              </TabsList>

              <TabsContent value="login" className="animate-fade-in">
                <form onSubmit={handleLogin} className="space-y-5">
                  <div className="space-y-2">
                    <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Sign in as</Label>
                    <div className="grid grid-cols-3 gap-2">
                      {(["student", "staff", "admin"] as LoginRole[]).map(r => (
                        <Button key={r} type="button" variant={loginRole === r ? "default" : "outline"} size="sm"
                          onClick={() => setLoginRole(r)} className="capitalize rounded-xl text-xs h-10 font-semibold transition-all duration-200">
                          {r === "student" && <User className="w-3.5 h-3.5 mr-1.5" />}
                          {r === "staff" && <Shirt className="w-3.5 h-3.5 mr-1.5" />}
                          {r === "admin" && <Shield className="w-3.5 h-3.5 mr-1.5" />}
                          {r}
                        </Button>
                      ))}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">{loginRole === "student" ? "Email" : "Employee ID"}</Label>
                    <Input value={identifier} onChange={e => setIdentifier(e.target.value)}
                      placeholder={loginRole === "student" ? "your@email.com" : "EMP001"} required className="h-11 rounded-xl" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Password</Label>
                    <Input type="password" value={password} onChange={e => setPassword(e.target.value)} required className="h-11 rounded-xl" />
                  </div>
                  <Button type="submit" className="w-full h-12 rounded-xl font-semibold text-sm gradient-primary border-0 text-primary-foreground hover:opacity-90 transition-all duration-200" disabled={loading}>
                    {loading ? "Signing in..." : "Sign In"}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register" className="animate-fade-in">
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-2">
                    <Button type="button" variant={registerType === "student" ? "default" : "outline"} size="sm"
                      onClick={() => setRegisterType("student")} className="rounded-xl h-10 font-semibold">Student</Button>
                    <Button type="button" variant={registerType === "staff" ? "default" : "outline"} size="sm"
                      onClick={() => setRegisterType("staff")} className="rounded-xl h-10 font-semibold">Staff / Admin</Button>
                  </div>

                  {registerType === "student" ? (
                    <form onSubmit={handleStudentRegister} className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Reg. Number</Label>
                          <Input value={regNum} onChange={e => setRegNum(e.target.value)} placeholder="22BCE0001" required className="h-10 rounded-xl text-sm" />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Name</Label>
                          <Input value={name} onChange={e => setName(e.target.value)} required className="h-10 rounded-xl text-sm" />
                        </div>
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs font-medium">Email</Label>
                        <Input type="email" value={email} onChange={e => setEmail(e.target.value)} required className="h-10 rounded-xl text-sm" />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Phone</Label>
                          <Input value={phone} onChange={e => setPhone(e.target.value)} placeholder="9123456789" required className="h-10 rounded-xl text-sm" />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Password</Label>
                          <Input type="password" value={regPassword} onChange={e => setRegPassword(e.target.value)} required className="h-10 rounded-xl text-sm" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Language</Label>
                          <Select value={lang} onValueChange={setLang}>
                            <SelectTrigger className="h-10 rounded-xl text-sm"><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="en">English</SelectItem>
                              <SelectItem value="hi">Hindi</SelectItem>
                              <SelectItem value="ta">Tamil</SelectItem>
                              <SelectItem value="te">Telugu</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Block</Label>
                          <Select value={block} onValueChange={setBlock}>
                            <SelectTrigger className="h-10 rounded-xl text-sm"><SelectValue /></SelectTrigger>
                            <SelectContent>{["A","B","C","D","E"].map(b => <SelectItem key={b} value={b}>Block {b}</SelectItem>)}</SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Floor</Label>
                          <Select value={floor} onValueChange={setFloor}>
                            <SelectTrigger className="h-10 rounded-xl text-sm"><SelectValue /></SelectTrigger>
                            <SelectContent>{["1","2","3","4","5"].map(f => <SelectItem key={f} value={f}>Floor {f}</SelectItem>)}</SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Room</Label>
                          <Input value={room} onChange={e => setRoom(e.target.value)} placeholder="101" required className="h-10 rounded-xl text-sm" />
                        </div>
                      </div>
                      <Button type="submit" className="w-full h-11 rounded-xl font-semibold text-sm gradient-primary border-0 text-primary-foreground hover:opacity-90 transition-all" disabled={loading}>
                        {loading ? "Registering..." : "Create Account"}
                      </Button>
                    </form>
                  ) : (
                    <form onSubmit={handleStaffRegister} className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Name</Label>
                          <Input value={staffName} onChange={e => setStaffName(e.target.value)} required className="h-10 rounded-xl text-sm" />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Employee ID</Label>
                          <Input value={empId} onChange={e => setEmpId(e.target.value)} placeholder="EMP001" required className="h-10 rounded-xl text-sm" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Phone</Label>
                          <Input value={staffPhone} onChange={e => setStaffPhone(e.target.value)} required className="h-10 rounded-xl text-sm" />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs font-medium">Password</Label>
                          <Input type="password" value={staffPassword} onChange={e => setStaffPassword(e.target.value)} required className="h-10 rounded-xl text-sm" />
                        </div>
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs font-medium">Role</Label>
                        <Select value={staffRole} onValueChange={v => setStaffRole(v as "staff" | "admin")}>
                          <SelectTrigger className="h-10 rounded-xl text-sm"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="staff">Staff</SelectItem>
                            <SelectItem value="admin">Admin</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <Button type="submit" className="w-full h-11 rounded-xl font-semibold text-sm gradient-primary border-0 text-primary-foreground hover:opacity-90 transition-all" disabled={loading}>
                        {loading ? "Registering..." : "Create Account"}
                      </Button>
                    </form>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
