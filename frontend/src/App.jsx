import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Brain, Cpu } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Navbar } from "./components/Navbar";
import { ThemeProvider } from "./components/theme-provider";
import { IoInformationCircleOutline } from "react-icons/io5";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function TeamCell({ name }) {
  return (
    <div className="flex items-center gap-2">
      <img
        src={`/${name.toLowerCase().replace(/[^a-z0-9]/g, "")}.svg`}
        alt={name}
        className="w-6 h-6 md:w-8 md:h-8 rounded-full border shrink-0"
        onError={(e) => {
          e.target.style
          .display = 'none';
        }}
      />
      <span className="text-xs md:text-sm font-medium truncate">{name}</span>
    </div>
  );
}

function getHighlightClass(match) {
  if (!match.result || !match.predicted_score) return "";
  const resultScore = match.result.replace(/\s/g, "");
  const predictedScore = match.predicted_score.replace(/\s/g, "");
  
  if (resultScore === predictedScore) {
    return "bg-yellow-50 dark:bg-yellow-950/20 border-l-4 border-yellow-500";
  }
  
  const [resHome, resAway] = resultScore.split("-").map(Number);
  const [predHome, predAway] = predictedScore.split("-").map(Number);
  
  if (
    (resHome > resAway && predHome > predAway) ||
    (resHome < resAway && predHome < predAway) ||
    (resHome === resAway && predHome === predAway)
  ) {
    return "bg-green-50 dark:bg-green-950/20 border-l-4 border-green-500";
  }
  
  return "bg-red-50 dark:bg-red-950/20 border-l-4 border-red-500";
}

function Probabilities({ match }) {
  if (match.home_win_probability === undefined) return <span className="text-xs text-muted-foreground">-</span>;

  const probs = [
    { label: "H", value: match.home_win_probability, key: "home" },
    { label: "D", value: match.draw_probability, key: "draw" },
    { label: "A", value: match.away_win_probability, key: "away" },
  ];
  
  // Check if it's approximately a draw (all probabilities near 0.33)
  const isDraw = Math.abs(match.home_win_probability - 0.33) < 0.05 && 
                 Math.abs(match.draw_probability - 0.33) < 0.05 && 
                 Math.abs(match.away_win_probability - 0.33) < 0.05;
  
  const maxValue = isDraw ? match.draw_probability : Math.max(...probs.map(p => p.value));

  return (
    <div className="flex gap-2">
      {probs.map((p) => (
        <div
          key={p.key}
          className={`px-2 py-1 rounded text-xs font-medium ${
            p.value === maxValue
              ? "bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-400"
              : "bg-muted text-muted-foreground"
          }`}
        >
          {p.label}: {(p.value * 100).toFixed(0)}%
        </div>
      ))}
    </div>
  );
}

function LLMPredictions({ predictions }) {
  if (!predictions || predictions.length === 0) {
    return <span className="text-xs text-muted-foreground">No predictions</span>;
  }

  return (
    <div className="space-y-2">
      {predictions.map((pred, idx) => (
        <div key={idx} className="text-xs space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-[10px] capitalize">
              {pred.llm_source}
            </Badge>
            <Badge variant="outline" className="font-mono text-[10px]">
              {pred.predicted_score}
            </Badge>
            <span className="text-[10px] text-muted-foreground">
              ({(pred.confidence * 100).toFixed(0)}%)
            </span>
          </div>
          <div className="flex gap-2">
            <span className="text-green-600">H: {(pred.home_win_probability * 100).toFixed(0)}%</span>
            <span className="text-yellow-600">D: {(pred.draw_probability * 100).toFixed(0)}%</span>
            <span className="text-red-600">A: {(pred.away_win_probability * 100).toFixed(0)}%</span>
          </div>
        </div>
      ))}
    </div>
  );
}

const App = () => {
  const [mlGameweeks, setMlGameweeks] = useState([]);
  const [llmGameweeks, setLlmGameweeks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);
  const [predictionMode, setPredictionMode] = useState("ml"); // "ml" or "llm"

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}`).then(res => res.json()),
      fetch(`${API_URL}/llm`).then(res => res.json())
    ])
      .then(([mlData, llmData]) => {
        setMlGameweeks(mlData);
        setLlmGameweeks(llmData);
        const currentGwIndex = mlData.findIndex(gw => gw.is_current);
        if (currentGwIndex !== -1) {
          setCurrentPage(currentGwIndex);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handlePrevious = () => setCurrentPage((prev) => Math.max(0, prev - 1));
  const handleNext = () => setCurrentPage((prev) => Math.min(mlGameweeks.length - 1, prev + 1));

  if (loading) {
    return (
      <ThemeProvider defaultTheme="system" storageKey="gamblr-theme">
        <div className="flex h-screen items-center justify-center">
          <Spinner className="size-8" />
        </div>
      </ThemeProvider>
    );
  }

  const currentGameweek = predictionMode === "ml" ? mlGameweeks[currentPage] : llmGameweeks[currentPage];

  return (
    <ThemeProvider defaultTheme="system" storageKey="gamblr-theme">
      <div className="h-screen bg-background pb-20 md:pb-8">
        <Navbar />
        
        <div className="max-w-5xl mx-auto py-4 md:py-8 px-3 md:px-4 pt-16 md:pt-20">
          <AnimatePresence mode="wait">
            {currentGameweek && (
              <motion.div
                key={`${currentPage}-${predictionMode}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <Card className="shadow-lg border-2">
                  <CardHeader>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
                        <CardTitle className="text-lg md:text-2xl font-bold">
                          Gameweek {currentGameweek.round_number}
                        </CardTitle>
                        <div className="flex gap-2">
                          {currentGameweek.is_current && (
                            <Badge className="bg-green-500 text-white border-0">Current</Badge>
                          )}
                          {currentGameweek.all_completed && (
                            <Badge variant="secondary">Completed</Badge>
                          )}
                        </div>
                      </div>
                      
                      {/* ML/LLM Toggle Button */}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPredictionMode(mode => mode === "ml" ? "llm" : "ml")}
                        className="flex items-center gap-2"
                      >
                        {predictionMode === "ml" ? (
                          <>
                            <Cpu className="h-4 w-4" />
                            <span className="text-xs">ML Mode</span>
                          </>
                        ) : (
                          <>
                            <Brain className="h-4 w-4" />
                            <span className="text-xs">LLM Mode</span>
                          </>
                        )}
                      </Button>
                    </div>
                  </CardHeader>
                  <Separator />
                  <CardContent className="px-4">
                    {/* Desktop View */}
                    <div className="hidden md:block overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b bg-muted/30">
                            <th className="text-left p-3 text-xs font-semibold text-muted-foreground">Date</th>
                            <th className="text-left p-3 text-xs font-semibold text-muted-foreground">Home</th>
                            <th className="text-center p-3 text-xs font-semibold text-muted-foreground">vs</th>
                            <th className="text-left p-3 text-xs font-semibold text-muted-foreground">Away</th>
                            <th className="text-left p-3 text-xs font-semibold text-muted-foreground">Result</th>
                            <th className="text-left p-3 text-xs font-semibold text-muted-foreground">
                              {predictionMode === "ml" ? "Prediction" : "LLM Predictions"}
                            </th>
                            {predictionMode === "ml" && (
                              <th className="text-left p-3 text-xs font-semibold text-muted-foreground">Probabilities</th>
                            )}
                          </tr>
                        </thead>
                        <tbody>
                          {currentGameweek.matches.map((match, index) => (
                            <motion.tr
                              key={match.match_number}
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ delay: index * 0.03 }}
                              className={`border-b hover:bg-muted/20 transition-colors ${predictionMode === "ml" ? getHighlightClass(match) : ""}`}
                            >
                              <td className="p-3 py-5 text-xs text-muted-foreground whitespace-nowrap">{match.date}</td>
                              <td className="p-3"><TeamCell name={match.home_team} /></td>
                              <td className="p-3 text-center text-xs text-muted-foreground">vs</td>
                              <td className="p-3"><TeamCell name={match.away_team} /></td>
                              <td className="p-3">
                                {match.result ? (
                                  <Badge variant="outline" className="font-mono text-xs">{match.result}</Badge>
                                ) : (
                                  <span className="text-xs text-muted-foreground">-</span>
                                )}
                              </td>
                              <td className="p-3">
                                {predictionMode === "ml" ? (
                                  match.predicted_score ? (
                                    <Badge variant="secondary" className="font-mono text-xs">{match.predicted_score}</Badge>
                                  ) : (
                                    <span className="text-xs text-muted-foreground">-</span>
                                  )
                                ) : (
                                  <LLMPredictions predictions={match.llm_predictions} />
                                )}
                              </td>
                              {predictionMode === "ml" && (
                                <td className="p-3">
                                  <Probabilities match={match} />
                                </td>
                              )}
                            </motion.tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Mobile View */}
                    <div className="md:hidden divide-y">
                      {currentGameweek.matches.map((match, index) => (
                        <motion.div
                          key={match.match_number}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: index * 0.03 }}
                          className={`p-4 ${predictionMode === "ml" ? getHighlightClass(match) : ""}`}
                        >
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-xs text-muted-foreground">{match.date}</span>
                            <div className="flex gap-2">
                              {match.result && (
                                <Badge variant="outline" className="font-mono text-xs">{match.result}</Badge>
                              )}
                              {predictionMode === "ml" && match.predicted_score && (
                                <Badge variant="secondary" className="font-mono text-xs">{match.predicted_score}</Badge>
                              )}
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <TeamCell name={match.home_team} />
                            </div>
                            <div className="flex items-center justify-between">
                              <TeamCell name={match.away_team} />
                            </div>
                          </div>
                          {predictionMode === "ml" && match.home_win_probability !== undefined && (
                            <div className="mt-3 pt-3 border-t">
                              <Probabilities match={match} />
                            </div>
                          )}
                          {predictionMode === "llm" && (
                            <div className="mt-3 pt-3 border-t">
                              <LLMPredictions predictions={match.llm_predictions} />
                            </div>
                          )}
                        </motion.div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

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
            <span className="text-xs md:text-sm text-muted-foreground font-medium">
              Gameweek {currentPage + 1} of {mlGameweeks.length}
            </span>
            <Button
              variant="outline"
              onClick={handleNext}
              disabled={currentPage === mlGameweeks.length - 1}
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
                {predictionMode === "ml" 
                  ? "Score predictions and win probabilities are generated by two separate ML models."
                  : "LLM predictions are generated by Groq 3.1-8b-instant model."}
              </p>
            </div>
          </div>
        </div>
      </div>
    </ThemeProvider>
  );
};

export default App;