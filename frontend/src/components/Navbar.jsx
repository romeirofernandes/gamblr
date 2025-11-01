import React from "react";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "./theme-provider";
import { motion } from "framer-motion";

export function Navbar() {
  const { theme, setTheme } = useTheme();

  return (
    <motion.nav
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 20,
      }}
      className="sticky top-4 z-50 mx-auto max-w-5xl px-4"
    >
      <div className="rounded-full border bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60 shadow-lg">
        <div className="flex h-14 items-center justify-between px-6">
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="font-heading text-xl font-bold tracking-tight"
          >
            gamblr.
          </motion.div>

          <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              className="rounded-full"
            >
              <motion.div
                initial={false}
                animate={{ rotate: theme === "dark" ? 180 : 0 }}
                transition={{ duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
              >
                {theme === "light" ? (
                  <Sun className="h-5 w-5" />
                ) : (
                  <Moon className="h-5 w-5" />
                )}
              </motion.div>
              <span className="sr-only">Toggle theme</span>
            </Button>
          </motion.div>
        </div>
      </div>
    </motion.nav>
  );
}