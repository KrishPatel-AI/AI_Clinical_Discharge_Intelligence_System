"use client";

import React, { useEffect, useState } from "react";
import { Button } from "@heroui/react";
import { useTheme } from "next-themes";
import { Sun, Moon } from "lucide-react";

export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button isIconOnly size="sm" variant="light" aria-label="Toggle theme">
        <div className="w-4 h-4" />
      </Button>
    );
  }

  const isDark = resolvedTheme === "dark" || theme === "dark";

  return (
    <Button
      isIconOnly
      size="sm"
      variant="flat"
      color="default"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      onPress={() => setTheme(isDark ? "light" : "dark")}
      className="text-foreground-600 hover:text-foreground"
    >
      {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
    </Button>
  );
}
