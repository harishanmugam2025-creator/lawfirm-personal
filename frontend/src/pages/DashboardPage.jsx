import { useState, useEffect } from "react";
import { useAuth } from "@/context/useAuth";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getDashboardSummary } from "@/services/dashboard";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Scale,
  LogOut,
  FileText,
  Search,
  BarChart3,
  ShieldCheck,
  Users,
  Settings,
  Briefcase,
  Crown,
  ChevronDown,
  Clock,
  TrendingUp,
  FolderOpen,
  Workflow,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  FileWarning,
} from "lucide-react";

/* ── role config ── */
const roleConfig = {
  paralegal: {
    label: "Paralegal",
    icon: Users,
    color: "text-blue-500",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    quickActions: [
      { icon: Search, label: "Legal Research", desc: "AI-powered case law search", link: "/research" },
      { icon: FileText, label: "Draft Documents", desc: "Generate templates via AI", link: "/documents" },
      { icon: Workflow, label: "Workflows", desc: "View compliance execution", link: "/workflows" },
    ],
  },
  associate: {
    label: "Associate",
    icon: Briefcase,
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    quickActions: [
      { icon: Workflow, label: "Workflow Builder", desc: "Design compliance logic", link: "/workflows" },
      { icon: FileText, label: "Case Management", desc: "Review active filings", link: "/documents" },
      { icon: BarChart3, label: "Analytics", desc: "Monitor case performance", link: "/analytics/case-performance" },
    ],
  },
  partner: {
    label: "Partner",
    icon: Crown,
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    quickActions: [
      { icon: BarChart3, label: "Firm Analytics", desc: "Revenue & KPI review", link: "/firm-analytics" },
      { icon: Workflow, label: "All Workflows", desc: "Audit active workflows", link: "/workflows" },
      { icon: Users, label: "Team Overview", desc: "Manage associate loads", link: "/team-overview" },
    ],
  },
  it_admin: {
    label: "IT Admin",
    icon: Settings,
    color: "text-violet-500",
    bg: "bg-violet-500/10",
    border: "border-violet-500/20",
    quickActions: [
      { icon: Users, label: "User Management", desc: "Manage users & roles", link: "/system/users" },
      { icon: ShieldCheck, label: "RBAC Policies", desc: "Manage OPA rules", link: "/system/rbac" },
      { icon: BarChart3, label: "Audit Logs", desc: "Review system activity", link: "/audit-logs" },
    ],
  },
};

const statCards = [
  { label: "Active Compliance Cases", value: "24", icon: FolderOpen, trend: "Up 3 from last week", status: "good", color: "text-blue-500", bg: "bg-blue-500/10", glow: "shadow-blue-500/10" },
  { label: "Pending Reviews", value: "7", icon: Clock, trend: "Requires attention", status: "warning", color: "text-amber-500", bg: "bg-amber-500/10", glow: "shadow-amber-500/10" },
  { label: "Documents Analyzed", value: "1,242", icon: FileText, trend: "142 scanned today", status: "neutral", color: "text-indigo-500", bg: "bg-indigo-500/10", glow: "shadow-indigo-500/10" },
  { label: "AI Accuracy Score", value: "98.4%", icon: TrendingUp, trend: "Consistent performance", status: "good", color: "text-emerald-500", bg: "bg-emerald-500/10", glow: "shadow-emerald-500/10" },
];

const ICON_MAP = {
  FolderOpen,
  Clock,
  FileText,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  Settings,
  FileWarning,
  ShieldCheck,
  Search,
  Workflow
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0, 
    transition: { 
      type: "spring", stiffness: 300, damping: 24 
    }
  },
};

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAllActivity, setShowAllActivity] = useState(false);

  const cfg = roleConfig[user?.role] || roleConfig.paralegal;
  const RoleIcon = cfg.icon;

  useEffect(() => {
    async function loadData() {
      try {
        const result = await getDashboardSummary();
        setData(result);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const initials = user?.email
    ? user.email.substring(0, 2).toUpperCase()
    : "U";

  return (
    <div className="relative flex min-h-screen flex-col bg-background overflow-hidden selection:bg-primary/30">
      
      {/* ── Background Effects ── */}
      <div className="fixed inset-0 pointer-events-none z-0 flex justify-center items-start overflow-hidden">
         <div className="absolute top-[-15%] left-[10%] w-[40%] h-[40%] rounded-full bg-primary/10 blur-[120px] mix-blend-screen opacity-50 duration-10000" />
         <div className="absolute bottom-[-10%] right-[5%] w-[30%] h-[30%] rounded-full bg-blue-500/10 blur-[100px] mix-blend-screen opacity-50 duration-10000" />
      </div>

      {/* ── Top bar ── */}
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/60 backdrop-blur-xl supports-backdrop-filter:bg-background/60 transition-all duration-300">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 group cursor-pointer" onClick={() => navigate("/")}>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 transition-colors group-hover:bg-primary/20 shadow-inner">
              <Scale className="h-5 w-5 text-primary" />
            </div>
            <span className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-linear-to-r from-foreground to-foreground/70">
              Veritas AI
            </span>
          </div>

          <div className="flex items-center gap-4">
            <ThemeToggle />
            <div className="hidden h-5 w-px bg-border sm:block" />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex h-10 items-center gap-2 px-3 hover:bg-muted/50 rounded-full border border-transparent hover:border-border/50 transition-all">
                  <Avatar className="h-7 w-7 border border-border/50 shadow-sm">
                    <AvatarFallback className={`${cfg.bg} ${cfg.color} text-[10px] font-bold`}>
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden max-w-[150px] truncate text-sm font-semibold sm:inline-block">
                    {user?.email}
                  </span>
                  <ChevronDown className="h-4 w-4 text-muted-foreground opacity-50" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-64 backdrop-blur-2xl bg-background/80 border-border/50 shadow-2xl rounded-xl">
                <DropdownMenuLabel className="font-normal p-3">
                  <div className="flex flex-col space-y-2">
                    <p className="truncate text-sm font-bold text-foreground" title={user?.email}>
                      {user?.email}
                    </p>
                    <div className="flex items-center gap-2">
                      <div className={`p-1 rounded-md ${cfg.bg}`}>
                        <RoleIcon className={`h-3 w-3 ${cfg.color}`} />
                      </div>
                      <p className="text-xs text-muted-foreground capitalize font-medium">
                        {cfg.label} Workspace
                      </p>
                    </div>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="opacity-50" />
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive focus:bg-destructive/10 cursor-pointer p-3 rounded-lg mx-1 my-1 font-medium"
                  onClick={handleLogout}
                >
                  <LogOut className="mr-2 h-4 w-4" /> Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* ── Main content ── */}
      <main className="relative z-10 mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
        
        <motion.div
           variants={containerVariants}
           initial="hidden"
           animate="visible"
        >
            {/* Greeting Section */}
            <motion.div variants={itemVariants} className="mb-8">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-2xl border border-border/50 bg-card/40 p-6 backdrop-blur-xl shadow-sm">
                    <div className="space-y-1.5">
                        <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl text-foreground">
                        Welcome back, {user?.email ? <span className="text-transparent bg-clip-text bg-linear-to-r from-primary to-purple-500">{user.email.split("@")[0]}</span> : "User"}
                        </h1>
                        <p className="text-base text-muted-foreground">
                        You have <span className="font-semibold text-foreground">{data?.greeting_reviews || 0} pending reviews</span> that require your attention today.
                        </p>
                    </div>
                    <div className="flex items-center self-start sm:self-auto">
                        <Badge variant="outline" className={`flex w-fit items-center gap-1.5 px-3 py-1.5 text-sm rounded-full ${cfg.color} ${cfg.bg} ${cfg.border} backdrop-blur-md`}>
                            <RoleIcon className="h-4 w-4" />
                            <span className="font-semibold">{cfg.label} Access</span>
                        </Badge>
                    </div>
                </div>
            </motion.div>

            {/* Stat cards row */}
            <motion.div variants={itemVariants} className="mb-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {(data?.stat_cards || statCards).map((s) => {
                const Icon = ICON_MAP[s.icon] || FolderOpen;
                return (
                    <Card key={s.label} className={`group relative h-full border-border/40 bg-card/40 backdrop-blur-xl transition-all duration-300 hover:bg-card/60 hover:-translate-y-1 shadow-sm hover:shadow-lg ${s.glow}`}>
                        <div className={`absolute inset-x-0 -top-px h-px w-full bg-linear-to-r from-transparent via-${s.color.split('-')[1]}-500/30 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100`} />
                        <CardContent className="flex flex-col gap-4 p-5">
                        <div className="flex items-start justify-between">
                            <div className={`flex h-10 w-10 items-center justify-center rounded-xl shadow-inner ${s.bg}`}>
                                <Icon className={`h-5 w-5 ${s.color}`} />
                            </div>
                            {/* Status indicator pill */}
                            {s.status === 'warning' && (
                                <span className="relative flex h-2.5 w-2.5">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500"></span>
                                </span>
                            )}
                            {s.status === 'good' && (
                                <div className="flex h-2 w-2 rounded-full bg-emerald-500/50" />
                            )}
                        </div>
                        <div className="space-y-1 mt-2">
                            <p className="text-3xl font-extrabold tracking-tight text-foreground">{loading ? "..." : s.value}</p>
                            <p className="text-sm font-medium text-muted-foreground">{s.label}</p>
                        </div>
                        <div className="mt-auto pt-4 border-t border-border/30 flex items-center gap-2">
                            <TrendingUp className={`h-3.5 w-3.5 ${s.status === 'warning' ? 'text-amber-500/70' : 'text-muted-foreground/50'}`} />
                            <p className={`text-[11px] font-bold uppercase tracking-wide ${s.status === 'warning' ? 'text-amber-500/90' : 'text-muted-foreground/70'}`}>
                                {s.trend}
                            </p>
                        </div>
                        </CardContent>
                    </Card>
                );
            })}
            </motion.div>

            {/* ── Two Column Layout for Details ── */}
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
            
                {/* Left Column: Recent Activity (Takes up 2/3) */}
                <motion.div variants={itemVariants} className="lg:col-span-2 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-2xl font-bold tracking-tight text-foreground">Activity Log</h2>
                        <Button 
                            variant="outline" 
                            size="sm" 
                            className="rounded-full h-8 px-4 text-xs font-semibold"
                            onClick={() => setShowAllActivity(true)}
                        >
                            View All
                        </Button>
                    </div>
                    
                    <div className="rounded-2xl border border-border/50 bg-card/40 backdrop-blur-xl shadow-lg overflow-hidden">
                        <div className="divide-y divide-border/30">
                            {loading ? (
                                <div className="p-8 text-center text-muted-foreground font-medium">Loading recent activity...</div>
                            ) : (data?.recent_activity || []).length === 0 ? (
                                <div className="p-8 text-center text-muted-foreground font-medium">No recent activity detected.</div>
                            ) : (data.recent_activity).map((activity) => {
                                const Icon = ICON_MAP[activity.icon] || CheckCircle2;
                                return (
                                    <div key={activity.id} className="group flex flex-col sm:flex-row sm:items-center justify-between p-4 sm:p-5 hover:bg-muted/30 transition-all duration-300 gap-4 cursor-pointer relative overflow-hidden">
                                        <div className="absolute inset-y-0 left-0 w-1 bg-transparent transition-colors duration-300 group-hover:bg-primary/50" />
                                        <div className="flex items-center gap-4 relative z-10 pl-2">
                                            <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl shadow-sm border ${activity.bg} ${activity.border} transition-transform duration-300 group-hover:scale-110`}>
                                                <Icon className={`h-5 w-5 ${activity.color}`} />
                                            </div>
                                            <div>
                                                <p className="text-sm font-bold text-foreground transition-colors group-hover:text-primary">{activity.title}</p>
                                                <p className="text-[13px] font-medium text-muted-foreground mt-1">{activity.type}</p>
                                            </div>
                                        </div>
                                        <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-2 w-full sm:w-auto mt-2 sm:mt-0 pt-2 sm:pt-0 border-t border-border/20 sm:border-t-0 ml-16 sm:ml-0 relative z-10">
                                            <Badge variant="outline" className={`px-2.5 py-0.5 text-[10px] uppercase font-bold tracking-wider rounded-md ${activity.bg} ${activity.color} ${activity.border}`}>
                                                {activity.status}
                                            </Badge>
                                            <p className="text-[11px] text-muted-foreground font-semibold flex items-center gap-1.5 pt-1">
                                                <Clock className="h-3.5 w-3.5 opacity-70" /> {activity.time}
                                            </p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </motion.div>

                {/* Right Column: Quick Actions & Health */}
                <motion.div variants={itemVariants} className="space-y-6">
                    <h2 className="text-2xl font-bold tracking-tight text-foreground">Workspace</h2>
                    <div className="grid gap-3">
                        {cfg.quickActions.map((action) => (
                            <div
                                key={action.label}
                                className="group flex cursor-pointer items-center gap-4 rounded-2xl border border-border/40 bg-card/60 backdrop-blur-xl p-4 shadow-sm transition-all duration-300 hover:border-primary/40 hover:shadow-md hover:bg-card/80"
                                onClick={() => action.link && navigate(action.link)}
                            >
                                <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-border/30 shadow-inner ${cfg.bg} transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-3`}>
                                    <action.icon className={`h-5 w-5 ${cfg.color}`} />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-bold text-foreground transition-colors group-hover:text-primary">{action.label}</p>
                                    <p className="text-xs font-medium text-muted-foreground mt-1 line-clamp-1">{action.desc}</p>
                                </div>
                                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted/50 transition-colors group-hover:bg-primary/10">
                                    <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* System Health Card */}
                    <div className="mt-8 rounded-2xl border border-border/40 bg-card/60 backdrop-blur-xl p-6 shadow-lg relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-[40px] pointer-events-none" />
                        <div className="flex items-center justify-between mb-6 relative z-10">
                            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                                <ActivityPulse /> System Status
                            </h3>
                            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[10px] font-bold uppercase tracking-wider">
                                Optimal
                            </Badge>
                        </div>
                        <div className="space-y-5 relative z-10">
                            {(data?.system_status || []).map((status) => {
                                const Icon = ICON_MAP[status.icon] || ShieldCheck;
                                return (
                                    <div key={status.name}>
                                        <div className="flex justify-between items-end mb-2">
                                            <span className="text-[13px] text-muted-foreground font-semibold flex items-center gap-1.5"><Icon className="w-3.5 h-3.5"/> {status.name}</span>
                                            <span className="text-[13px] font-bold text-foreground">{loading ? "..." : status.status === "Active" ? `${status.percentage}%` : status.status}</span>
                                        </div>
                                        <div className="h-2 w-full bg-muted/50 rounded-full overflow-hidden shadow-inner">
                                            <motion.div 
                                                initial={{ width: 0 }} 
                                                animate={{ width: loading ? 0 : `${status.percentage}%` }} 
                                                transition={{ duration: 1, delay: 0.5 }}
                                                className={`h-full ${status.color} rounded-full`} 
                                            />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </motion.div>

            </div>
        </motion.div>
      </main>

      {/* ── Activity Log Modal ── */}
      <AnimatePresence>
        {showAllActivity && (
          <div className="fixed inset-0 z-50 flex items-start justify-end">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-background/60 backdrop-blur-sm"
              onClick={() => setShowAllActivity(false)}
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="relative h-full w-full max-w-md border-l border-border bg-card shadow-2xl overflow-hidden flex flex-col"
            >
              <div className="p-6 border-b border-border/50 flex items-center justify-between bg-muted/20">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
                    <Clock className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">Activity Log</h3>
                    <p className="text-xs text-muted-foreground">Comprehensive system audit</p>
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setShowAllActivity(false)} className="rounded-full">
                  <X className="h-4 w-4" />
                </Button>
              </div>

              <div className="flex-1 overflow-y-auto p-2">
                <div className="space-y-1">
                  {loading ? (
                    <div className="flex justify-center py-12">
                      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>
                  ) : (data?.recent_activity || []).length === 0 ? (
                    <p className="p-8 text-center text-sm text-muted-foreground">No activities found.</p>
                  ) : (
                    data.recent_activity.map((activity) => {
                      const Icon = ICON_MAP[activity.icon] || CheckCircle2;
                      return (
                        <div 
                          key={activity.id} 
                          className="flex items-center gap-4 p-4 rounded-xl hover:bg-muted/30 transition-colors border border-transparent hover:border-border/40"
                        >
                          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${activity.bg} ${activity.border}`}>
                            <Icon className={`h-4 w-4 ${activity.color}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-bold text-foreground truncate">{activity.title}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-[11px] font-medium text-muted-foreground">{activity.type}</span>
                              <span className="h-1 w-1 rounded-full bg-border" />
                              <span className="text-[11px] font-medium text-muted-foreground">{activity.time}</span>
                            </div>
                          </div>
                          <Badge variant="outline" className={`px-2 py-0.5 text-[9px] uppercase font-bold rounded-md ${activity.bg} ${activity.color} ${activity.border}`}>
                            {activity.status}
                          </Badge>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
              
              <div className="p-4 border-t border-border/50 bg-muted/10">
                <Button variant="outline" className="w-full rounded-xl gap-2 font-bold" onClick={() => navigate("/audit-logs")}>
                  Full Audit Trail <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ActivityPulse() {
    return (
        <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
        </span>
    )
}
