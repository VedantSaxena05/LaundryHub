import { Button } from "@/components/ui/button";
import { useLanguage } from "@/i18n/LanguageContext";

export function LanguageToggle() {
  const { language, setLanguage } = useLanguage();

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={() => setLanguage(language === "en" ? "ta" : "en")}
      className="rounded-xl text-xs font-semibold h-8 px-3 min-w-[52px]"
    >
      {language === "en" ? "தமிழ்" : "EN"}
    </Button>
  );
}
