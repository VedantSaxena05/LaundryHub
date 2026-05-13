import { useEffect, useState } from "react";
import { studentsApi, type StudentProfile } from "@/api/students";
import { useAuth } from "@/contexts/AuthContext";
import { AnimatedCard } from "@/components/AnimatedCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Edit3, Save, UserCircle2, X } from "lucide-react";
import { toast } from "sonner";

interface StudentProfileSectionProps {
  profile: StudentProfile | null;
  onProfileUpdated: (profile: StudentProfile) => void;
  delay?: number;
}

interface StudentProfileForm {
  name: string;
  email: string;
  phone_number: string;
  block: string;
  floor: string;
  room_number: string;
}

const toFormState = (profile: StudentProfile | null): StudentProfileForm => ({
  name: profile?.name ?? "",
  email: profile?.email ?? "",
  phone_number: profile?.phone_number ?? "",
  block: profile?.block ?? "",
  floor: profile?.floor ? String(profile.floor) : "",
  room_number: profile?.room_number ?? "",
});

export function StudentProfileSection({ profile, onProfileUpdated, delay = 0.4 }: StudentProfileSectionProps) {
  const { token } = useAuth();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<StudentProfileForm>(() => toFormState(profile));

  useEffect(() => {
    setForm(toFormState(profile));
  }, [profile]);

  const handleChange = (field: keyof StudentProfileForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleCancel = () => {
    setEditing(false);
    setForm(toFormState(profile));
  };

  const handleSave = async () => {
    if (!token || !profile) return;

    const floorValue = Number(form.floor);
    if (!form.name.trim() || !form.email.trim() || !form.phone_number.trim() || !form.block.trim() || !form.room_number.trim()) {
      toast.error("Please fill in all required profile fields.");
      return;
    }

    if (Number.isNaN(floorValue)) {
      toast.error("Floor must be a valid number.");
      return;
    }

    setSaving(true);

    try {
      const updated = await studentsApi.updateMe(token, {
        name: form.name.trim(),
        email: form.email.trim(),
        phone_number: form.phone_number.trim(),
        block: form.block.trim().toUpperCase(),
        floor: floorValue,
        room_number: form.room_number.trim(),
      });

      onProfileUpdated(updated);
      setEditing(false);
      toast.success("Profile updated successfully.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to update profile.");
    } finally {
      setSaving(false);
    }
  };

  if (!profile) {
    return (
      <AnimatedCard delay={delay}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-display text-lg">
            <UserCircle2 className="h-5 w-5 text-primary" />
            Student Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">Loading your profile...</CardContent>
      </AnimatedCard>
    );
  }

  return (
    <AnimatedCard delay={delay}>
      <CardHeader className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 font-display text-lg">
            <UserCircle2 className="h-5 w-5 text-primary" />
            Student Profile
          </CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">Manage your contact and hostel details.</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Badge className={profile.is_active ? "bg-success text-success-foreground" : "bg-muted text-muted-foreground"}>
            {profile.is_active ? "Active" : "Inactive"}
          </Badge>

          {editing ? (
            <>
              <Button type="button" variant="outline" className="rounded-xl" onClick={handleCancel} disabled={saving}>
                <X className="h-4 w-4" />
                Cancel
              </Button>
              <Button type="button" className="rounded-xl" onClick={handleSave} disabled={saving}>
                <Save className="h-4 w-4" />
                {saving ? "Saving..." : "Save Changes"}
              </Button>
            </>
          ) : (
            <Button type="button" variant="outline" className="rounded-xl" onClick={() => setEditing(true)}>
              <Edit3 className="h-4 w-4" />
              Edit Profile
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {editing ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            <div className="space-y-1.5">
              <Label htmlFor="student-name">Full Name</Label>
              <Input id="student-name" value={form.name} onChange={(event) => handleChange("name", event.target.value)} className="rounded-xl" />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="student-email">Email</Label>
              <Input id="student-email" type="email" value={form.email} onChange={(event) => handleChange("email", event.target.value)} className="rounded-xl" />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="student-phone">Phone Number</Label>
              <Input id="student-phone" value={form.phone_number} onChange={(event) => handleChange("phone_number", event.target.value)} className="rounded-xl" />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="student-block">Block</Label>
              <Input
                id="student-block"
                maxLength={1}
                value={form.block}
                onChange={(event) => handleChange("block", event.target.value.toUpperCase())}
                className="rounded-xl"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="student-floor">Floor</Label>
              <Input
                id="student-floor"
                type="number"
                value={form.floor}
                onChange={(event) => handleChange("floor", event.target.value)}
                className="rounded-xl"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="student-room">Room Number</Label>
              <Input id="student-room" value={form.room_number} onChange={(event) => handleChange("room_number", event.target.value)} className="rounded-xl" />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="student-registration">Registration Number</Label>
              <Input id="student-registration" value={profile.registration_number} disabled className="rounded-xl" />
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {[
              { label: "Full Name", value: profile.name },
              { label: "Registration Number", value: profile.registration_number },
              { label: "Email", value: profile.email },
              { label: "Phone Number", value: profile.phone_number },
              { label: "Hostel Block", value: `${profile.block} · Floor ${profile.floor}` },
              { label: "Room Number", value: profile.room_number },
            ].map((item) => (
              <div key={item.label} className="rounded-2xl border border-border/50 bg-accent/30 p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">{item.label}</p>
                <p className="mt-2 text-sm font-semibold text-foreground">{item.value}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </AnimatedCard>
  );
}