import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface AnimatedCardProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}

export function AnimatedCard({ children, className, delay = 0 }: AnimatedCardProps) {
  return (
    <Card
      className={cn(
        "shadow-card hover:shadow-card-hover transition-all duration-300 border-border/50 opacity-0 animate-fade-in-up",
        className
      )}
      style={{ animationDelay: `${delay}s` }}
    >
      {children}
    </Card>
  );
}
