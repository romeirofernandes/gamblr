import React, { useState } from "react";
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
  const currentGwIdx = betsData.findIndex(gw => gw.bets.some(bet => bet.stake === 100));
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

  const realGameweekNumber = BETS_DATA[currentPage]?.gameweek;
  const totalGameweeks = BETS_DATA.length;

  return (
    <ThemeProvider defaultTheme="system" storageKey="gamblr-theme">
      <div className="min-h-screen bg-background pb-20 md:pb-8">
        <Navbar />
        <div className="max-w-5xl mx-auto py-4 md:py-8 px-3 md:px-4 pt-16 md:pt-20">
          {/* PNL Summary */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Card className="mb-6 md:mb-8 shadow-lg border-2">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <IoStatsChartOutline className="h-5 w-5 md:h-6 md:w-6 text-blue-600" />
                  <CardTitle className="text-lg md:text-2xl font-bold">P&L Summary</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
                  <div className="p-3 md:p-4 rounded-lg border-2 border-border bg-card">
                    <p className="text-[10px] md:text-xs text-muted-foreground mb-1 md:mb-2 flex items-center gap-1">
                      <IoTrophyOutline className="h-3 w-3" />
                      Total P&L
                    </p>
                    <p className={`text-xl md:text-2xl font-bold ${pnl.total >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {pnl.total >= 0 ? '+' : ''}₹{pnl.total.toFixed(2)}
                    </p>
                  </div>

                  <div className="p-3 md:p-4 rounded-lg border-2 border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950/20">
                    <p className="text-[10px] md:text-xs text-muted-foreground mb-1 md:mb-2 flex items-center gap-1">
                      <IoCheckmarkCircle className="h-3 w-3 text-green-600" />
                      Won
                    </p>
                    <p className="text-xl md:text-2xl font-bold text-green-600">{pnl.won}</p>
                  </div>

                  <div className="p-3 md:p-4 rounded-lg border-2 border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/20">
                    <p className="text-[10px] md:text-xs text-muted-foreground mb-1 md:mb-2 flex items-center gap-1">
                      <IoCloseCircle className="h-3 w-3 text-red-600" />
                      Lost
                    </p>
                    <p className="text-xl md:text-2xl font-bold text-red-600">{pnl.lost}</p>
                  </div>

                  <div className="p-3 md:p-4 rounded-lg border-2 border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950/20">
                    <p className="text-[10px] md:text-xs text-muted-foreground mb-1 md:mb-2 flex items-center gap-1">
                      <IoTimeOutline className="h-3 w-3 text-blue-600" />
                      Pending
                    </p>
                    <p className="text-xl md:text-2xl font-bold text-blue-600">{pnl.pending}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Betting Slip */}
          <AnimatePresence mode="wait">
            {currentBets && (
              <motion.div
                key={currentPage}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <Card className="mb-6 md:mb-8 shadow-lg border-2">
                  <CardHeader className="pb-3">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <CardTitle className="text-lg md:text-xl font-semibold">
                        Gameweek {currentBets.gameweek} Bets
                      </CardTitle>
                      <Badge variant="outline" className="text-xs w-fit">
                        {currentBets.bets.filter(b => b.stake > 0).length} Active
                      </Badge>
                    </div>
                  </CardHeader>
                  <Separator />
                  <CardContent className="p-3 md:p-6">
                    <div className="space-y-3">
                      {currentBets.bets.filter(b => b.stake > 0).map((bet, index) => (
                        <motion.div
                          key={bet.match_number}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: index * 0.03 }}
                          className={`p-3 md:p-4 rounded-lg border-2 transition-all ${
                            bet.result === "won"
                              ? "border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950/20"
                              : bet.result === "lost"
                              ? "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/20"
                              : "border-border bg-muted/30"
                          }`}
                        >
                          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center gap-2 text-sm md:text-base font-semibold">
                                <span className="truncate">{bet.home_team}</span>
                                <span className="text-xs text-muted-foreground shrink-0">vs</span>
                                <span className="truncate">{bet.away_team}</span>
                              </div>
                              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] md:text-xs text-muted-foreground">
                                <span>Bet: <span className="font-semibold text-foreground">{bet.bet_on}</span></span>
                                <span>Odds: <span className="font-semibold text-foreground">{bet.odds || 'TBD'}</span></span>
                                <span>Stake: <span className="font-semibold text-foreground">₹{bet.stake}</span></span>
                              </div>
                            </div>
                            <div className="flex items-center justify-between md:justify-end gap-3 pt-2 md:pt-0 border-t md:border-0">
                              {bet.result === "won" && (
                                <>
                                  <span className="text-sm font-bold text-green-600">
                                    +₹{bet.odds ? ((bet.stake * bet.odds) - bet.stake).toFixed(2) : '0.00'}
                                  </span>
                                  <IoCheckmarkCircle className="h-5 w-5 md:h-6 md:w-6 text-green-600 shrink-0" />
                                </>
                              )}
                              {bet.result === "lost" && (
                                <>
                                  <span className="text-sm font-bold text-red-600">
                                    -₹{bet.stake.toFixed(2)}
                                  </span>
                                  <IoCloseCircle className="h-5 w-5 md:h-6 md:w-6 text-red-600 shrink-0" />
                                </>
                              )}
                              {!bet.result && (
                                <>
                                  <span className="text-xs md:text-sm font-medium text-blue-600">
                                    Potential: ₹{bet.odds ? ((bet.stake * bet.odds) - bet.stake).toFixed(2) : '0.00'}
                                  </span>
                                  <IoTimeOutline className="h-5 w-5 md:h-6 md:w-6 text-blue-600 shrink-0" />
                                </>
                              )}
                            </div>
                          </div>
                        </motion.div>
                      ))}

                      {currentBets.bets.filter(b => b.stake > 0).length === 0 && (
                        <div className="text-center py-12 text-muted-foreground">
                          <IoTimeOutline className="h-10 w-10 md:h-12 md:w-12 mx-auto mb-3 opacity-50" />
                          <p className="text-sm">No active bets for this gameweek</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Pagination */}
          <div className="flex items-center justify-center gap-4 mt-6">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentPage === 0}
              size="sm"
              className="rounded-full"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex flex-col sm:flex-row items-center gap-1 sm:gap-2">
              <span className="text-xs md:text-sm text-muted-foreground font-medium">
                Gameweek {realGameweekNumber} of {totalGameweeks}
              </span>
              {currentPage === currentGwIdx && (
                <Badge className="bg-green-500 text-white text-[10px] md:text-xs border-0">Current</Badge>
              )}
            </div>
            <Button
              variant="outline"
              onClick={handleNext}
              disabled={currentPage === BETS_DATA.length - 1}
              size="sm"
              className="rounded-full"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="fixed bottom-3 right-3 md:bottom-6 md:right-6 max-w-[280px] md:max-w-xs z-50">
          <div className="p-2.5 md:p-3 rounded-lg bg-muted/95 backdrop-blur border border-border shadow-lg">
            <div className="flex items-start gap-2">
              <IoInformationCircleOutline className="h-3.5 w-3.5 md:h-4 md:w-4 text-muted-foreground mt-0.5 shrink-0" />
              <p className="text-[10px] md:text-xs text-muted-foreground leading-tight">
                Odds taken from stake.com on 1st Nov at 18:00 IST.
              </p>
            </div>
          </div>
        </div>
      </div>
    </ThemeProvider>
  );
};

export default Gamblr;