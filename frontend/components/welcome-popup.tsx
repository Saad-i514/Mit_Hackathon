'use client';

import * as React from 'react';
import { useState, useEffect } from 'react';
import { Network, Fingerprint, Cpu, ScanLine, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

export function WelcomePopup() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const hasSeenWelcome = localStorage.getItem('hasSeenWelcome');
    if (!hasSeenWelcome) {
      const timer = setTimeout(() => {
        setOpen(true);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleClose = () => {
    setOpen(false);
    localStorage.setItem('hasSeenWelcome', 'true');
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg p-0 overflow-hidden border-0 bg-transparent shadow-none">
        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="relative overflow-hidden bg-background/80 backdrop-blur-2xl border border-white/20 shadow-[0_0_50px_rgba(59,130,246,0.3)] rounded-2xl p-6"
            >
              {/* Background Glow */}
              <div className="absolute -top-24 -right-24 w-48 h-48 bg-blue-500/30 rounded-full blur-3xl" />
              <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-indigo-500/30 rounded-full blur-3xl" />

              <DialogHeader className="relative z-10">
                <DialogTitle className="flex items-center gap-3 text-3xl font-bold tracking-tight">
                  <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-[0_0_20px_rgba(59,130,246,0.5)]">
                    <ScanLine className="h-6 w-6 text-white" />
                  </div>
                  <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
                    Welcome to AI Scientist
                  </span>
                </DialogTitle>
                <DialogDescription className="text-base pt-4 space-y-5 text-foreground/80">
                  <p className="leading-relaxed">
                    You're about to supercharge your research. Our AI engine validates your hypotheses, 
                    conducts deep literature reviews, and generates lab-ready experiment protocols in under 90 seconds.
                  </p>
                  <div className="space-y-4 pt-2">
                    <motion.div 
                      initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}
                      className="flex items-start gap-3"
                    >
                      <div className="h-8 w-8 rounded-full bg-blue-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Network className="h-4 w-4 text-blue-400" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">Grounded in real literature</p>
                        <p className="text-sm text-muted-foreground">Uses Semantic Scholar for 200M+ papers</p>
                      </div>
                    </motion.div>
                    <motion.div 
                      initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
                      className="flex items-start gap-3"
                    >
                      <div className="h-8 w-8 rounded-full bg-indigo-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Fingerprint className="h-4 w-4 text-indigo-400" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">Verifies catalog numbers</p>
                        <p className="text-sm text-muted-foreground">Cross-references Thermo Fisher & Sigma</p>
                      </div>
                    </motion.div>
                    <motion.div 
                      initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}
                      className="flex items-start gap-3"
                    >
                      <div className="h-8 w-8 rounded-full bg-violet-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Cpu className="h-4 w-4 text-violet-400" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">Learns continuously</p>
                        <p className="text-sm text-muted-foreground">Improves via expert review feedback loops</p>
                      </div>
                    </motion.div>
                  </div>
                </DialogDescription>
              </DialogHeader>
              <div className="flex justify-end mt-8 relative z-10">
                <Button 
                  onClick={handleClose} 
                  size="lg"
                  className="w-full sm:w-auto bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-[0_0_15px_rgba(59,130,246,0.4)] transition-all duration-300 hover:shadow-[0_0_25px_rgba(59,130,246,0.6)] rounded-xl font-semibold text-white"
                >
                  Let's Supercharge Research <Zap className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
}


