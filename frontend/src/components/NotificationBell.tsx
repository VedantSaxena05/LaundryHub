import { Bell, BellOff, BellRing, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { usePushNotifications } from "@/hooks/usePushNotifications";
import { toast } from "sonner";

export function NotificationBell() {
  const { state, error, subscribe, unsubscribe } = usePushNotifications();

  const handleClick = async () => {
    if (state === "subscribed") {
      await unsubscribe();
      toast.success("Notifications disabled");
    } else if (state === "unsubscribed" || state === "prompt" || state === "error") {
      await subscribe();
      if (Notification.permission !== "denied") {
        toast.success("Notifications enabled!");
      }
    } else if (state === "denied") {
      toast.error("Notifications blocked. Please enable them in your browser settings.");
    }
  };

  if (state === "unsupported") return null;

  const tooltipText =
    state === "loading" ? "Loading..." :
    state === "subscribed" ? "Notifications on — click to disable" :
    state === "denied" ? "Notifications blocked in browser" :
    state === "error" ? (error || "Error — click to retry") :
    "Enable notifications";

  const icon =
    state === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> :
    state === "subscribed" ? <BellRing className="h-4 w-4 text-primary" /> :
    state === "denied" ? <BellOff className="h-4 w-4 text-muted-foreground" /> :
    <Bell className="h-4 w-4" />;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleClick}
            disabled={state === "loading" || state === "denied"}
            className="rounded-xl relative"
          >
            {icon}
            {state === "subscribed" && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-primary animate-pulse" />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p className="text-xs">{tooltipText}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
