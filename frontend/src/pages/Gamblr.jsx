import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Navbar } from "../components/Navbar";
import { ThemeProvider } from "../components/theme-provider";
import { 
  IoCheckmarkCircle, 
  IoCloseCircle, 
  IoTimeOutline,
  IoTrophyOutline,
  IoStatsChartOutline,
  IoInformationCircleOutline
} from "react-icons/io5";
import betsData from "../data/bets.json";

const Gamblr = () => {
  const currentGwIdx = betsData.findIndex(
    gw => gw.bets.some(bet => bet.stake === 100)
  );
  const [currentPage, setCurrentPage] = useState(currentGwIdx >= 0 ? currentGwIdx : 0);

  const BETS_DATA = betsData;
  const currentBets = BETS_DATA[currentPage];

  const calculatePNL = (bets) => {
    if (!bets) return { total: 0, won: 0, lost: 0, pending: 0, totalStaked: 0 };
    let totalPNL = 0, wonCount = 0, lostCount = 0, pendingCount = 0, totalStaked = 0;
    bets.forEach((bet) => {
      if (bet.stake > 0) {
        totalStaked += bet.stake;
        if (bet.result === "won") {
          totalPNL += (bet.stake * bet.odds) - bet.stake;
          wonCount++;
        } else if (bet.result === "lost") {
          totalPNL -= bet.stake;
          lostCount++;
        } else {
          pendingCount++;
        }
      }
    });
    return { total: totalPNL, won: wonCount, lost: lostCount, pending: pendingCount, totalStaked };
  };

  const handlePrevious = () => setCurrentPage((prev) => Math.max(0, prev - 1));
  const handleNext = () => setCurrentPage((prev) => Math.min(BETS_DATA.length - 1, prev + 1));
  const pnl = calculatePNL(BETS_DATA.flatMap(gw => gw.bets));

  // Find the real gameweek number for the current page
  const realGameweekNumber = BETS_DATA[currentPage]?.gameweek;
  const totalGameweeks = BETS_DATA.length;

  return (
    <ThemeProvider defaultTheme="system" storageKey="gamblr-theme">
      <div className="min-h-screen bg-background pb-8 relative">
        <Navbar />
        <div className="max-w-5xl mx-auto py-8 px-4 pt-12">
          {/* PNL Summary */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="mb-8 shadow-md border-2">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <IoStatsChartOutline className="h-6 w-6 text-primary" />
                  <CardTitle className="text-2xl font-bold">Profit & Loss Summary</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <motion.div
                    whileHover={{ y: -2 }}
                    className="p-4 rounded-lg border-2 border-border bg-card"
                  >
                    <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                      <IoTrophyOutline className="h-3 w-3" />
                      Total P&L
                    </p>
                    <p className={`text-2xl font-bold ${pnl.total >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {pnl.total >= 0 ? '+' : ''}₹{pnl.total.toFixed(2)}
                    </p>
                  </motion.div>

                  <motion.div
                    whileHover={{ y: -2 }}
                    className="p-4 rounded-lg border-2 border-green-200 dark:border-green-900"
                  >
                    <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                      <IoCheckmarkCircle className="h-3 w-3 text-green-600" />
                      Won
                    </p>
                    <p className="text-2xl font-bold text-green-600">{pnl.won}</p>
                  </motion.div>

                  <motion.div
                    whileHover={{ y: -2 }}
                    className="p-4 rounded-lg border-2 border-red-200  dark:border-red-900 "
                  >
                    <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                      <IoCloseCircle className="h-3 w-3 text-red-600" />
                      Lost
                    </p>
                    <p className="text-2xl font-bold text-red-600">{pnl.lost}</p>
                  </motion.div>

                  <motion.div
                    whileHover={{ y: -2 }}
                    className="p-4 rounded-lg border-2 border-blue-200 dark:border-blue-900"
                  >
                    <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                      <IoTimeOutline className="h-3 w-3 text-blue-400" />
                      Pending
                    </p>
                    <p className="text-2xl font-bold text-blue-400">{pnl.pending}</p>
                  </motion.div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Betting Slip */}
          <AnimatePresence mode="wait">
            {currentBets && (
              <motion.div
                key={currentPage}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{
                  type: "spring",
                  stiffness: 300,
                  damping: 30,
                }}
              >
                <Card className="mb-8 shadow-md">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xl font-semibold">
                        {currentBets.gameweek} Betting Slip
                      </CardTitle>
                      <Badge variant="outline" className="text-sm">
                        {currentBets.bets.filter(b => b.stake > 0).length} Active Bets
                      </Badge>
                    </div>
                  </CardHeader>
                  <Separator />
                  <CardContent>
                    <div className="space-y-4">
                      {currentBets.bets.filter(b => b.stake > 0).map((bet, index) => (
                        <motion.div
                          key={bet.match_number}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.03 }}
                          whileHover={{ x: 4 }}
                          className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
                            bet.result === "won"
                              ? "border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950/20"
                              : bet.result === "lost"
                              ? "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/20"
                              : "border-border bg-muted/30"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-sm font-semibold">{bet.home_team}</span>
                                <span className="text-xs text-muted-foreground">vs</span>
                                <span className="text-sm font-semibold">{bet.away_team}</span>
                              </div>
                              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                <span>Bet: <span className="font-semibold text-foreground">{bet.bet_on}</span></span>
                                <span>Odds: <span className="font-semibold text-foreground">{bet.odds || 'TBD'}</span></span>
                                <span>Stake: <span className="font-semibold text-foreground">₹{bet.stake}</span></span>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              {bet.result === "won" && (
                                <>
                                  <span className="text-sm font-bold text-green-600">
                                    +₹{bet.odds ? ((bet.stake * bet.odds) - bet.stake).toFixed(2) : '0.00'}
                                  </span>
                                  <IoCheckmarkCircle className="h-6 w-6 text-green-600" />
                                </>
                              )}
                              {bet.result === "lost" && (
                                <>
                                  <span className="text-sm font-bold text-red-600">
                                    -₹{bet.stake.toFixed(2)}
                                  </span>
                                  <IoCloseCircle className="h-6 w-6 text-red-600" />
                                </>
                              )}
                              {!bet.result && (
                                <>
                                  <span className="text-sm font-medium text-blue-400">
                                    Potential: ₹{bet.odds ? ((bet.stake * bet.odds) - bet.stake).toFixed(2) : '0.00'}
                                  </span>
                                  <IoTimeOutline className="h-6 w-6 text-blue-400" />
                                </>
                              )}
                            </div>
                          </div>
                        </motion.div>
                      ))}

                      {currentBets.bets.filter(b => b.stake > 0).length === 0 && (
                        <div className="text-center py-12 text-muted-foreground">
                          <IoTimeOutline className="h-12 w-12 mx-auto mb-3 opacity-50" />
                          <p>No active bets for this gameweek</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Pagination */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="flex items-center justify-center gap-6 mt-4"
          >
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                variant="outline"
                onClick={handlePrevious}
                disabled={currentPage === 0}
                className="rounded-full"
              >
                <ChevronLeft className="h-5 w-5" />
              </Button>
            </motion.div>
            <span className="text-sm text-muted-foreground">
              Gameweek {realGameweekNumber} of {totalGameweeks}
              {currentPage === currentGwIdx && (
                <Badge variant="outline" className="ml-2 bg-green-100 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800">
                  Current
                </Badge>
              )}
            </span>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                variant="outline"
                onClick={handleNext}
                disabled={currentPage === BETS_DATA.length - 1}
                className="rounded-full"
              >
                <ChevronRight className="h-5 w-5" />
              </Button>
            </motion.div>
          </motion.div>
        </div>

        {/* Odds Disclaimer - Bottom Right */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="fixed bottom-6 right-6 max-w-xs"
        >
          <div className="p-3 rounded-lg bg-muted/95 backdrop-blur border border-border shadow-lg">
            <div className="flex items-start gap-2">
              <IoInformationCircleOutline className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
              <p className="text-xs text-muted-foreground">
                Odds have been taken from stake.com on 1st Nov at 18:00 IST.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </ThemeProvider>
  );
};

export default Gamblr;