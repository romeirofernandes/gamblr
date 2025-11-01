import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Navbar } from "./components/Navbar";
import { ThemeProvider } from "./components/theme-provider";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/gameweeks";

function TeamCell({ name }) {
  return (
    <motion.div
      className="flex items-center gap-2"
      whileHover={{ x: 4 }}
      transition={{ type: "spring", stiffness: 400, damping: 10 }}
    >
      <img
        src={`/${name.toLowerCase().replace(/[^a-z0-9]/g, "")}.svg`}
        alt={name}
        className="w-8 h-8 rounded-full border"
        onError={(e) => {
          e.target.style.display = 'none';
        }}
      />
      <span>{name}</span>
    </motion.div>
  );
}

function Probabilities({ match }) {
  if (match.home_win_probability === undefined) return <span className="text-muted-foreground">-</span>;

  // Find which probability is highest
  const probs = [
    {
      label: match.home_team,
      value: match.home_win_probability,
      key: "home",
    },
    {
      label: "Draw",
      value: match.draw_probability,
      key: "draw",
    },
    {
      label: match.away_team,
      value: match.away_win_probability,
      key: "away",
    },
  ];
  const maxValue = Math.max(...probs.map(p => p.value));

  return (
    <div className="flex flex-col gap-0.5 text-xs">
      {probs.map((p, idx) => (
        <motion.span
          key={p.key}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 + idx * 0.1 }}
          className={
            p.value === maxValue
              ? "font-semibold text-green-600"
              : "text-muted-foreground"
          }
        >
          {p.label}: {(p.value * 100).toFixed(1)}%
        </motion.span>
      ))}
    </div>
  );
}

const App = () => {
  const [gameweeks, setGameweeks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);

  useEffect(() => {
    fetch(API_URL)
      .then((res) => res.json())
      .then((data) => {
        setGameweeks(data);
        // Set current page to current gameweek
        const currentGwIndex = data.findIndex(gw => gw.is_current);
        if (currentGwIndex !== -1) {
          setCurrentPage(currentGwIndex);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handlePrevious = () => {
    setCurrentPage((prev) => Math.max(0, prev - 1));
  };

  const handleNext = () => {
    setCurrentPage((prev) => Math.min(gameweeks.length - 1, prev + 1));
  };

  if (loading) {
    return (
      <ThemeProvider defaultTheme="system" storageKey="gamblr-theme">
        <div className="flex h-screen items-center justify-center">
          <Spinner className="size-8" />
        </div>
      </ThemeProvider>
    );
  }

  const currentGameweek = gameweeks[currentPage];

  return (
    <ThemeProvider defaultTheme="system" storageKey="gamblr-theme">
      <div className="h-screen bg-background pb-8">
        <Navbar />
        
        <div className="max-w-5xl mx-auto py-8 px-4 pt-12">
          <AnimatePresence mode="wait">
            {currentGameweek && (
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
                  <CardHeader className="flex flex-row items-center gap-4">
                    <CardTitle className="text-xl font-semibold">
                      Gameweek {currentGameweek.round_number}
                    </CardTitle>
                    {currentGameweek.is_current && (
                      <Badge variant="outline" className="bg-green-100 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800">
                        Current
                      </Badge>
                    )}
                    {currentGameweek.all_completed && (
                      <Badge variant="secondary" className="bg-muted text-muted-foreground">
                        Completed
                      </Badge>
                    )}
                  </CardHeader>
                  <Separator />
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Date</TableHead>
                          <TableHead>Home</TableHead>
                          <TableHead></TableHead>
                          <TableHead>Away</TableHead>
                          <TableHead>Result</TableHead>
                          <TableHead>Prediction</TableHead>
                          <TableHead>Probabilities</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {currentGameweek.matches.map((match, index) => (
                          <motion.tr
                            key={match.match_number}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="border-b transition-colors hover:bg-muted/50"
                          >
                            <TableCell>{match.date}</TableCell>
                            <TableCell>
                              <TeamCell name={match.home_team} />
                            </TableCell>
                            <TableCell className="text-center text-muted-foreground">vs</TableCell>
                            <TableCell>
                              <TeamCell name={match.away_team} />
                            </TableCell>
                            <TableCell>
                              {match.result ? (
                                <Badge variant="outline" className="bg-accent text-accent-foreground">
                                  {match.result}
                                </Badge>
                              ) : (
                                <span className="text-muted-foreground">-</span>
                              )}
                            </TableCell>
                            <TableCell>
                              {match.predicted_score ? (
                                <Badge variant="secondary">{match.predicted_score}</Badge>
                              ) : (
                                <span className="text-muted-foreground">-</span>
                              )}
                            </TableCell>
                            <TableCell>
                              <Probabilities match={match} />
                            </TableCell>
                          </motion.tr>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

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
              Gameweek {currentPage + 1} of {gameweeks.length}
            </span>

            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                variant="outline"
                onClick={handleNext}
                disabled={currentPage === gameweeks.length - 1}
                className="rounded-full"
              >
                <ChevronRight className="h-5 w-5" />
              </Button>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </ThemeProvider>
  );
};

export default App;