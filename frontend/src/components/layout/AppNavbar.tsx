"use client";

import React, { useEffect, useState } from "react";
import {
  Navbar,
  NavbarBrand,
  NavbarContent,
  NavbarItem,
  NavbarMenuToggle,
  NavbarMenu,
  NavbarMenuItem,
  Link,
  Chip,
} from "@heroui/react";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./ThemeToggle";
import { Activity, FileText, History } from "lucide-react";
import { checkHealth } from "@/lib/api";

export function AppNavbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const pathname = usePathname();

  useEffect(() => {
    let isMounted = true;
    const verifyHealth = async () => {
      try {
        const res = await checkHealth();
        if (isMounted) setBackendOnline(res.status === "ok");
      } catch {
        if (isMounted) setBackendOnline(false);
      }
    };
    verifyHealth();
    const interval = setInterval(verifyHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const navItems = [
    { name: "New Review", href: "/", icon: FileText },
    { name: "Review History", href: "/reviews", icon: History },
  ];

  return (
    <Navbar
      isBordered
      isMenuOpen={isMenuOpen}
      onMenuOpenChange={setIsMenuOpen}
      maxWidth="full"
      className="bg-background/80 backdrop-blur-md px-2 sm:px-6"
    >
      <NavbarContent justify="start">
        <NavbarMenuToggle
          aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          className="sm:hidden"
        />
        <NavbarBrand className="gap-2">
          <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
            <Activity className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <Link
              href="/"
              className="font-semibold text-foreground tracking-tight text-base sm:text-lg"
            >
              Clinical Discharge Intelligence
            </Link>
            <span className="text-[10px] text-foreground-400 font-normal leading-none hidden sm:inline">
              Advisory Review & Guideline Grounding
            </span>
          </div>
        </NavbarBrand>
      </NavbarContent>

      <NavbarContent className="hidden sm:flex gap-4" justify="center">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <NavbarItem key={item.href} isActive={isActive}>
              <Link
                href={item.href}
                color={isActive ? "primary" : "foreground"}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-medium text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-foreground-600 hover:text-foreground hover:bg-default-100"
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </Link>
            </NavbarItem>
          );
        })}
      </NavbarContent>

      <NavbarContent justify="end" className="gap-3">
        {backendOnline !== null && (
          <NavbarItem className="hidden md:flex">
            <Chip
              size="sm"
              variant="dot"
              color={backendOnline ? "success" : "danger"}
              className="border-none text-xs"
            >
              {backendOnline ? "Backend Connected" : "Backend Offline"}
            </Chip>
          </NavbarItem>
        )}
        <NavbarItem>
          <ThemeToggle />
        </NavbarItem>
      </NavbarContent>

      <NavbarMenu className="pt-4 gap-2">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <NavbarMenuItem key={item.href}>
              <Link
                href={item.href}
                color={isActive ? "primary" : "foreground"}
                className="w-full flex items-center gap-2 py-2 text-base font-medium"
                onPress={() => setIsMenuOpen(false)}
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </Link>
            </NavbarMenuItem>
          );
        })}
        {backendOnline !== null && (
          <NavbarMenuItem className="pt-2">
            <Chip
              size="sm"
              variant="dot"
              color={backendOnline ? "success" : "danger"}
            >
              {backendOnline ? "Backend Connected" : "Backend Offline"}
            </Chip>
          </NavbarMenuItem>
        )}
      </NavbarMenu>
    </Navbar>
  );
}
