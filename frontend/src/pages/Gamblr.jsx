import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChevronLeft, ChevronRight, Brain, Cpu } from "lucide-react";
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
  const initialGwIdx = betsData.findIndex(gw => gw.gameweek === 11);
  const currentGwIdx = initialGwIdx; // Add this line
  const [currentPage, setCurrentPage] = useState(initialGwIdx >= 0 ? initialGwIdx : 0);
  const [activeTab, setActiveTab] = useState("ml");

  const BETS_DATA = betsData;
  const currentBets = BETS_DATA[currentPage];

  const calculatePNL = (bets, type = 'all') => {
    if (!bets) return { total: 0, won: 0, lost: 0, pending: 0, totalStaked: 0 };
    
    let totalPNL = 0, wonCount = 0, lostCount = 0, pendingCount = 0, totalStaked = 0;
    
    bets.forEach((gameweek) => {
      const mlBets = type === 'all' || type === 'ml' ? (gameweek.ml_bets || []) : [];
      const llmBets = type === 'all' || type === 'llm' ? (gameweek.llm_bets || []) : [];
      const allBets = [...mlBets, ...llmBets];
      
      allBets.forEach((bet) => {
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
    });
    
    return { total: totalPNL, won: wonCount, lost: lostCount, pending: pendingCount, totalStaked };
  };

  const handlePrevious = () => setCurrentPage((prev) => Math.max(0, prev - 1));
  const handleNext = () => setCurrentPage((prev) => Math.min(BETS_DATA.length - 1, prev + 1));
  
  const pnlAll = calculatePNL(BETS_DATA, 'all');
  const pnlML = calculatePNL(BETS_DATA, 'ml');
  const pnlLLM = calculatePNL(BETS_DATA, 'llm');

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
                  <IoStatsChartOutline className="h-5 w-5 md:h-6 md:w-6" />
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
                    <p className={`text-xl md:text-2xl font-bold ${pnlAll.total >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {pnlAll.total >= 0 ? '+' : ''}₹{pnlAll.total.toFixed(2)}
                    </p>
                  </div>

                  <div className="p-3 md:p-4 rounded-lg border-2 border-border bg-card">
                    <p className="text-[10px] md:text-xs text-muted-foreground mb-1 md:mb-2 flex items-center gap-1">
                      <Cpu className="h-3 w-3" />
                      ML P&L
                    </p>
                    <p className={`text-xl md:text-2xl font-bold ${pnlML.total >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {pnlML.total >= 0 ? '+' : ''}₹{pnlML.total.toFixed(2)}
                    </p>
                  </div>

                  <div className="p-3 md:p-4 rounded-lg border-2 border-border bg-card">
                    <p className="text-[10px] md:text-xs text-muted-foreground mb-1 md:mb-2 flex items-center gap-1">
                      <Brain className="h-3 w-3" />
                      LLM P&L
                    </p>
                    <p className={`text-xl md:text-2xl font-bold ${pnlLLM.total >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {pnlLLM.total >= 0 ? '+' : ''}₹{pnlLLM.total.toFixed(2)}
                    </p>
                  </div>

                  <div className="p-3 md:p-4 rounded-lg border-2 border-border bg-card">
                    <p className="text-[10px] md:text-xs text-muted-foreground mb-1 md:mb-2 flex items-center gap-1">
                      <IoTimeOutline className="h-3 w-3" />
                      Pending
                    </p>
                    <p className="text-xl md:text-2xl font-bold">{pnlAll.pending}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Betting Slip with Tabs */}
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
                  <CardHeader>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <CardTitle className="text-lg md:text-xl font-semibold">
                        Gameweek {currentBets.gameweek} Bets
                      </CardTitle>
                    </div>
                  </CardHeader>
                  <Separator />
                  <CardContent className="p-3 md:p-6">
                    
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                      <TabsList className="grid w-full grid-cols-2 mb-6">
                        <TabsTrigger value="ml" className="flex items-center gap-2">
                          <Cpu className="h-4 w-4" />
                          ML Bets ({(currentBets.ml_bets || []).filter(b => b.stake > 0).length})
                        </TabsTrigger>
                        <TabsTrigger value="llm" className="flex items-center gap-2">
                          <Brain className="h-4 w-4" />
                          LLM Bets ({(currentBets.llm_bets || []).filter(b => b.stake > 0).length})
                        </TabsTrigger>
                      </TabsList>

                      {/* ML Bets Tab */}
                      <TabsContent value="ml">
                        <div className="space-y-3">
                          {(currentBets.ml_bets || []).filter(b => b.stake > 0).map((bet, index) => (
                            <BetCard key={`ml-${bet.match_number}`} bet={bet} index={index} />
                          ))}
                          {(currentBets.ml_bets || []).filter(b => b.stake > 0).length === 0 && (
                            <EmptyBetsMessage />
                          )}
                        </div>
                      </TabsContent>

                      {/* LLM Bets Tab */}
                      <TabsContent value="llm">
                        <div className="space-y-3">
                          {(currentBets.llm_bets || []).filter(b => b.stake > 0).map((bet, index) => (
                            <BetCard key={`llm-${bet.match_number}`} bet={bet} index={index} />
                          ))}
                          {(currentBets.llm_bets || []).filter(b => b.stake > 0).length === 0 && (
                            <EmptyBetsMessage />
                          )}
                        </div>
                      </TabsContent>
                    </Tabs>
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
                <Badge className="text-[10px] md:text-xs border-0">Current</Badge>
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
                Odds taken from stake.com. ML = Machine Learning, LLM = Large Language Model predictions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </ThemeProvider>
  );
};

// Bet Card Component
const BetCard = ({ bet, index }) => (
  <motion.div
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
            <span className="text-xs md:text-sm font-medium">
              Potential: ₹{bet.odds ? ((bet.stake * bet.odds) - bet.stake).toFixed(2) : '0.00'}
            </span>
            <IoTimeOutline className="h-5 w-5 md:h-6 md:w-6 shrink-0" />
          </>
        )}
      </div>
    </div>
  </motion.div>
);

// Empty Bets Message Component
const EmptyBetsMessage = () => (
  <div className="text-center py-12 text-muted-foreground">
    <IoTimeOutline className="h-10 w-10 md:h-12 md:w-12 mx-auto mb-3 opacity-50" />
    <p className="text-sm">No active bets for this gameweek</p>
  </div>
);

export default Gamblr;