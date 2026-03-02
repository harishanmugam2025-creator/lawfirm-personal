import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '@/context/useAuth';
import { workflowService } from '@/services/workflows';
import { ThemeToggle } from '@/components/ThemeToggle';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import {
  Scale,
  ArrowLeft,
  Plus,
  Workflow,
  Loader2,
  Calendar,
  Trash2,
  Search,
  Filter,
  MoreVertical,
  Activity,
  Play
} from 'lucide-react';

import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.06, duration: 0.35 },
  }),
};

export default function WorkflowsPage() {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const canCreate = hasPermission('workflows', 'create');
  const canDelete = hasPermission('workflows', 'delete');

  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [workflowToDelete, setWorkflowToDelete] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await workflowService.list();
        setWorkflows(data.workflows || []);
      } catch {
        setError('Failed to load workflows');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const confirmDelete = async () => {
    if (!workflowToDelete) return;
    try {
      await workflowService.remove(workflowToDelete);
      setWorkflows((prev) => prev.filter((w) => w.id !== workflowToDelete));
      toast.success("Workflow deleted successfully");
    } catch {
      toast.error('Failed to delete workflow');
    } finally {
      setWorkflowToDelete(null);
    }
  };

  const handleToggleStatus = async (e, wf) => {
    e.stopPropagation();
    try {
      await workflowService.update(wf.id, { is_active: !wf.is_active });
      setWorkflows((prev) =>
        prev.map((w) => (w.id === wf.id ? { ...w, is_active: !w.is_active } : w))
      );
      toast.success(`Workflow marked as ${!wf.is_active ? 'Active' : 'Inactive'}`);
    } catch {
      toast.error('Failed to update workflow status');
    }
  };

  const filteredWorkflows = workflows.filter((wf) => 
    wf.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    (wf.description && wf.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* ── Header ── */}
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/70 backdrop-blur-xl supports-backdrop-filter:bg-background/60">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 sm:gap-4">
            <Button
              variant="ghost"
              onClick={() => navigate('/dashboard')}
              className="gap-2 text-muted-foreground hover:text-foreground h-9 px-3"
            >
              <ArrowLeft className="h-4.5 w-4.5" />
              <span className="hidden sm:inline text-sm font-medium">Dashboard</span>
            </Button>
            
            <div className="hidden h-5 w-px bg-border sm:block" />

            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                 <Scale className="h-4.5 w-4.5 text-primary" />
              </div>
              <span className="text-lg font-bold tracking-tight">Workflows</span>
            </div>
          </div>

          <div className="flex items-center gap-3 sm:gap-4">
            <ThemeToggle />
            {canCreate && (
            <Button
              onClick={() => navigate('/workflows/builder')}
              className="gap-2 rounded-full px-5 shadow-sm"
            >
              <Plus className="h-4.5 w-4.5" />
              New Workflow
            </Button>
            )}
          </div>
        </div>
      </header>

      {/* ── Content ── */}
      <main className="relative z-10 mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : error ? (
          <div className="text-center py-20 text-destructive">{error}</div>
        ) : workflows.length === 0 ? (
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className="flex flex-col items-center justify-center py-24 text-center"
          >
            <div className="mb-6 flex items-center justify-center rounded-full bg-muted/40 p-6 backdrop-blur-sm">
                <Workflow className="h-12 w-12 text-muted-foreground/40" />
            </div>
            <h2 className="text-xl font-bold tracking-tight mb-2">No workflows found</h2>
            <p className="max-w-md text-sm text-muted-foreground mb-8">
              {canCreate
                ? 'Create automated compliance checks, document analysis pipelines, and custom AI evaluations.'
                : 'There are no active workflows available for your current role and permissions.'}
            </p>
            {canCreate && (
              <Button onClick={() => navigate('/workflows/builder')} className="gap-2 rounded-full px-6 shadow-sm">
                <Plus className="h-4 w-4" /> Create Your First Workflow
              </Button>
            )}
          </motion.div>
        ) : filteredWorkflows.length === 0 ? (
           <div className="space-y-6">
             <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                 <div>
                     <h2 className="text-2xl font-bold tracking-tight text-foreground">Active Workflows</h2>
                     <p className="text-sm text-muted-foreground mt-1">Manage and monitor your automated compliance pipelines.</p>
                 </div>
                 
                 <div className="flex items-center gap-3">
                     <div className="relative">
                         <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                         <Input 
                             type="search" 
                             placeholder="Search workflows..." 
                             value={searchQuery}
                             onChange={(e) => setSearchQuery(e.target.value)}
                             className="pl-9 w-full sm:w-[250px] bg-card/40 border-border/50 focus-visible:ring-primary/20 transition-all rounded-full h-9"
                         />
                     </div>
                 </div>
             </div>

              <motion.div
                initial="hidden"
                animate="visible"
                variants={fadeUp}
                className="flex flex-col items-center justify-center py-20 text-center"
              >
               <div className="mb-4 flex items-center justify-center rounded-full bg-muted/40 p-5 backdrop-blur-sm">
                   <Search className="h-10 w-10 text-muted-foreground/40" />
               </div>
               <h2 className="text-xl font-bold tracking-tight mb-2">No results found</h2>
               <p className="text-sm text-muted-foreground">
                 No workflows match your search <span className="font-semibold text-foreground">"{searchQuery}"</span>.
               </p>
               <Button variant="link" onClick={() => setSearchQuery('')} className="mt-2 text-primary">
                 Clear search
               </Button>
              </motion.div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-foreground">Active Workflows</h2>
                    <p className="text-sm text-muted-foreground mt-1">Manage and monitor your automated compliance pipelines.</p>
                </div>
                
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <Input 
                            type="search" 
                            placeholder="Search workflows..." 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 w-full sm:w-[250px] bg-card/40 border-border/50 focus-visible:ring-primary/20 transition-all rounded-full h-9"
                        />
                    </div>
                </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredWorkflows.map((wf, i) => (
                <motion.div
                  key={wf.id}
                  initial="hidden"
                  animate="visible"
                  variants={fadeUp}
                  custom={i}
                >
                  <Card
                    className="group relative cursor-pointer border-border/50 bg-card/30 backdrop-blur-sm transition-all duration-300 hover:bg-card/60 hover:border-primary/30 hover:shadow-md overflow-hidden flex flex-col h-full"
                    onClick={() =>
                      navigate(`/workflows/builder?id=${wf.id}`)
                    }
                  >
                    {/* Top Accent Line */}
                    <div className="absolute top-0 left-0 w-full h-1 bg-linear-to-r from-primary/40 to-primary/10 opacity-0 transition-opacity group-hover:opacity-100" />
                    
                    <CardHeader className="pb-3 flex flex-row items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 border border-primary/10 transition-transform group-hover:scale-105">
                            <Workflow className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                              <CardTitle className="text-base font-bold text-foreground line-clamp-1">{wf.name}</CardTitle>
                              <div className="flex items-center gap-2 mt-1">
                                  {wf.is_active ? (
                                    <div className="flex items-center gap-1.5">
                                      <span className="relative flex h-2 w-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                                      </span>
                                      <span className="text-[11px] font-bold text-emerald-500 uppercase tracking-wider">Active</span>
                                    </div>
                                  ) : (
                                      <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
                                          <div className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50" />
                                          Draft
                                      </span>
                                  )}
                              </div>
                          </div>
                        </div>

                        {(canCreate || canDelete) && (
                          <div onClick={(e) => e.stopPropagation()}>
                              <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                      <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground">
                                          <MoreVertical className="h-4 w-4" />
                                      </Button>
                                  </DropdownMenuTrigger>
                                  <DropdownMenuContent align="end" className="w-[160px]">
                                      <DropdownMenuItem className="gap-2" onClick={() => navigate(`/workflows/builder?id=${wf.id}`)}>
                                          <Play className="h-4 w-4" /> Edit Layout
                                      </DropdownMenuItem>
                                      {canCreate && (
                                          <DropdownMenuItem className="gap-2" onClick={(e) => handleToggleStatus(e, wf)}>
                                              <Activity className="h-4 w-4" /> Mark as {wf.is_active ? 'Inactive' : 'Active'}
                                          </DropdownMenuItem>
                                      )}
                                        {canDelete && (
                                          <DropdownMenuItem className="text-destructive focus:text-destructive gap-2" onClick={(e) => { e.stopPropagation(); setWorkflowToDelete(wf.id); }}>
                                              <Trash2 className="h-4 w-4" /> Delete Workflow
                                          </DropdownMenuItem>
                                        )}
                                  </DropdownMenuContent>
                              </DropdownMenu>
                          </div>
                        )}
                    </CardHeader>
                    <CardContent className="flex-1 flex flex-col justify-end pt-0 mt-auto">
                      {wf.description && (
                        <CardDescription className="mb-4 text-xs line-clamp-2">
                          {wf.description}
                        </CardDescription>
                      )}
                      <div className="flex items-center justify-between mt-auto pt-3 border-t border-border/30">
                        <div className="flex flex-col">
                            <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold mb-0.5">Last Run</span>
                            <span className="text-xs font-medium text-foreground flex items-center gap-1.5">
                                <Activity className="h-3 w-3 text-muted-foreground" />
                                Just now
                            </span>
                        </div>
                        <div className="flex flex-col items-end">
                            <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold mb-0.5">Created</span>
                            <span className="text-xs font-medium text-foreground flex items-center gap-1.5">
                                <Calendar className="h-3 w-3 text-muted-foreground" />
                                {new Date(wf.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                            </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!workflowToDelete} onOpenChange={(open) => !open && setWorkflowToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Workflow</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this workflow? This action cannot be undone and will permanently remove all associated execution history and analytical data.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-destructive text-white hover:bg-destructive/90">Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
