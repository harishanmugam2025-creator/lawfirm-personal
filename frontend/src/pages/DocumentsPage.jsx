import { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { documentService } from "@/services/documents";
import { analysisService } from "@/services/analysis";
import { workflowService } from "@/services/workflows";
import { ThemeToggle } from "@/components/ThemeToggle";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Scale,
  Upload,
  FileText,
  Trash2,
  Eye,
  X,
  Loader2,
  AlertCircle,
  ArrowLeft,
  CloudUpload,
  File,
  Search,
  Shield,
  ShieldCheck,
  ShieldX,
  CheckCircle2,
  XCircle,
  Lightbulb,
  BarChart3,
  Sparkles,
  Workflow,
} from "lucide-react";
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
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.4 },
  }),
};

/* ── Compliance Result Panel ── */
function CompliancePanel({ result, onClose }) {
  if (!result) return null;

  const scoreColor =
    result.score >= 80
      ? "text-emerald-500"
      : result.score >= 50
        ? "text-amber-500"
        : "text-red-500";

  const scoreBg =
    result.score >= 80
      ? "from-emerald-500/20 to-emerald-500/5"
      : result.score >= 50
        ? "from-amber-500/20 to-amber-500/5"
        : "from-red-500/20 to-red-500/5";

  const scoreTrack =
    result.score >= 80
      ? "stroke-emerald-500"
      : result.score >= 50
        ? "stroke-amber-500"
        : "stroke-red-500";

  return (
    <motion.div
      className="fixed inset-0 z-50 flex"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <motion.div
        className="relative ml-auto flex h-full w-full max-w-2xl flex-col border-l border-border bg-background shadow-2xl"
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 30, stiffness: 300 }}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
              <Shield className="h-5 w-5 text-primary" />
            </div>
            <div className="min-w-0">
              <h3 className="truncate text-lg font-bold">Compliance Report</h3>
              <p className="truncate text-xs text-muted-foreground">
                {result.document_name}
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div className="flex-1 overflow-auto">
          {/* ── Score Section ── */}
          <div className={`mx-6 mt-6 rounded-2xl bg-linear-to-br ${scoreBg} border border-border/50 p-6`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-1">
                  Compliance Score
                </p>
                <div className="flex items-baseline gap-1">
                  <span className={`text-5xl font-black tracking-tight ${scoreColor}`}>
                    {result.score}
                  </span>
                  <span className="text-lg text-muted-foreground font-medium">
                    / 100
                  </span>
                </div>
              </div>

              {/* Circular progress */}
              <div className="relative h-20 w-20">
                <svg className="h-20 w-20 -rotate-90" viewBox="0 0 80 80">
                  <circle
                    cx="40"
                    cy="40"
                    r="35"
                    fill="none"
                    className="stroke-muted/30"
                    strokeWidth="6"
                  />
                  <circle
                    cx="40"
                    cy="40"
                    r="35"
                    fill="none"
                    className={scoreTrack}
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={`${(result.score / 100) * 220} 220`}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <BarChart3 className={`h-5 w-5 ${scoreColor}`} />
                </div>
              </div>
            </div>
          </div>

          {/* ── Status Badges ── */}
          <div className="grid grid-cols-2 gap-3 mx-6 mt-4">
            <StatusCard
              label="GDPR"
              status={result.gdpr_status}
            />
            <StatusCard
              label="CCPA"
              status={result.ccpa_status}
            />
          </div>

          {/* ── Detected Sections ── */}
          {result.detected_sections?.length > 0 && (
            <div className="mx-6 mt-6">
              <h4 className="flex items-center gap-2 text-sm font-bold text-foreground mb-3">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                Detected Sections
              </h4>
              <div className="space-y-1.5">
                {result.detected_sections.map((section, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-center gap-2.5 rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                    <span className="text-sm capitalize">{section}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* ── Missing Sections ── */}
          {result.missing_sections?.length > 0 && (
            <div className="mx-6 mt-6">
              <h4 className="flex items-center gap-2 text-sm font-bold text-foreground mb-3">
                <XCircle className="h-4 w-4 text-red-500" />
                Missing Sections
              </h4>
              <div className="space-y-1.5">
                {result.missing_sections.map((section, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-center gap-2.5 rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2"
                  >
                    <XCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />
                    <span className="text-sm">{section}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* ── AI Suggestions ── */}
          {result.ai_suggestions?.length > 0 && (
            <div className="mx-6 mt-6 mb-6">
              <h4 className="flex items-center gap-2 text-sm font-bold text-foreground mb-3">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                AI Suggestions
              </h4>
              <div className="space-y-2">
                {result.ai_suggestions.map((suggestion, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.06 }}
                    className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3"
                  >
                    <p className="text-sm leading-relaxed">{suggestion}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

function StatusCard({ label, status }) {
  const pass = status === "PASS";
  return (
    <div
      className={`flex items-center gap-3 rounded-xl border p-4 transition-all ${
        pass
          ? "border-emerald-500/30 bg-emerald-500/5"
          : "border-red-500/30 bg-red-500/5"
      }`}
    >
      {pass ? (
        <ShieldCheck className="h-6 w-6 text-emerald-500" />
      ) : (
        <ShieldX className="h-6 w-6 text-red-500" />
      )}
      <div>
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          {label}
        </p>
        <p
          className={`text-lg font-black ${
            pass ? "text-emerald-500" : "text-red-500"
          }`}
        >
          {status}
        </p>
      </div>
    </div>
  );
}

/* ── Main Page ── */
export default function DocumentsPage() {
  const fileInputRef = useRef(null);

  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [viewLoading, setViewLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [docToDelete, setDocToDelete] = useState(null);

  // Compliance analysis state
  const [analyzingDocId, setAnalyzingDocId] = useState(null);
  const [complianceResult, setComplianceResult] = useState(null);
  const [workflows, setWorkflows] = useState([]);
  const [showWorkflowModal, setShowWorkflowModal] = useState(false);
  const [docToAnalyze, setDocToAnalyze] = useState(null);
 
  const fetchWorkflows = useCallback(async () => {
    try {
      const data = await workflowService.list();
      setWorkflows((data.workflows || []).filter(wf => wf.is_active));
    } catch {
      toast.error("Failed to load active workflows.");
    }
  }, []);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await documentService.list();
      setDocuments(data.documents);
    } catch {
      setError("Failed to load documents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
    fetchWorkflows();
  }, [fetchDocuments, fetchWorkflows]);

  const handleUpload = async (file) => {
    if (!file) return;
    if (file.type !== "application/pdf") {
      setError("Only PDF files are accepted.");
      return;
    }
    setError("");
    setUploading(true);
    try {
      await documentService.upload(file);
      await fetchDocuments();
      toast.success("Document uploaded successfully");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Upload failed");
      setError(
        err.response?.data?.detail || "Upload failed. Please try again."
      );
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
    e.target.value = "";
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleUpload(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const confirmDelete = async () => {
    if (!docToDelete) return;
    try {
      await documentService.remove(docToDelete);
      setDocuments((prev) => prev.filter((d) => d.id !== docToDelete));
      if (selectedDoc?.id === docToDelete) setSelectedDoc(null);
      toast.success("Document deleted successfully");
    } catch (err) {
      if (err.response?.status === 403) {
        toast.error("You don't have permission to delete this document.");
      } else {
        toast.error(err.response?.data?.detail || "Failed to delete document.");
      }
    } finally {
      setDocToDelete(null);
    }
  };

  const filteredDocs = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleView = async (id) => {
    setViewLoading(true);
    try {
      const doc = await documentService.get(id);
      setSelectedDoc(doc);
    } catch {
      setError("Failed to load document details.");
    } finally {
      setViewLoading(false);
    }
  };

  // ── Compliance Analysis ──
  const handleAnalyze = (docId) => {
    setDocToAnalyze(docId);
    setShowWorkflowModal(true);
  };
 
  const startAnalysis = async (workflowId) => {
    if (!docToAnalyze) return;
    
    const docId = docToAnalyze;
    setShowWorkflowModal(false);
    setDocToAnalyze(null);
    
    setAnalyzingDocId(docId);
    toast.info("Starting AI compliance analysis…");
    try {
      const result = await analysisService.analyzeDocument(docId, workflowId);
      setComplianceResult(result);
      toast.success(`Analysis complete — Score: ${result.score}/100`);
    } catch (err) {
      const msg =
        err.response?.data?.detail || "Analysis failed. Is Ollama running?";
      toast.error(msg);
    } finally {
      setAnalyzingDocId(null);
    }
  };

  const handleViewAnalysis = async (docId) => {
    try {
      const result = await analysisService.getAnalysis(docId);
      setComplianceResult(result);
    } catch (err) {
      if (err.response?.status === 404) {
        toast.info("No analysis found. Click 'Analyze' to run one.");
      } else {
        toast.error("Failed to load analysis.");
      }
    }
  };

  const formatBytes = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    const date = new Date(dateStr.endsWith("Z") ? dateStr : dateStr + "Z");
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* ── Header ── */}
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-lg">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Link to="/dashboard" className="text-muted-foreground hover:text-foreground transition-colors">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <Separator orientation="vertical" className="h-6" />
            <Scale className="h-6 w-6 text-primary" />
            <span className="text-lg font-bold tracking-tight">Documents</span>
          </div>
          <div className="flex items-center gap-4">
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* ── Main content ── */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
        {/* Error banner */}
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mb-6 flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
            <button
              className="ml-auto shrink-0"
              onClick={() => setError("")}
            >
              <X className="h-4 w-4" />
            </button>
          </motion.div>
        )}

        {/* ── Upload zone ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp}>
          <Card
            className={`mb-8 border-2 border-dashed transition-colors cursor-pointer ${
              dragOver
                ? "border-primary bg-primary/5"
                : "border-border/50 bg-card/60 hover:border-primary/40"
            }`}
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <CardContent className="flex flex-col items-center justify-center py-12">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={handleFileSelect}
              />
              {uploading ? (
                <div className="flex flex-col items-center gap-3">
                  <Loader2 className="h-10 w-10 animate-spin text-primary" />
                  <p className="text-sm text-muted-foreground">
                    Uploading & extracting text…
                  </p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                    <CloudUpload className="h-7 w-7 text-primary" />
                  </div>
                  <div className="text-center">
                    <p className="font-medium">
                      Drop a PDF here or{" "}
                      <span className="text-primary underline underline-offset-4">
                        browse
                      </span>
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      PDF files up to 10 MB • Text is extracted automatically
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Document list ── */}
        {loading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : filteredDocs.length === 0 && documents.length > 0 ? (
          <div className="space-y-6 pt-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-4">
                <div className="flex items-center gap-3">
                    <h2 className="text-xl font-bold tracking-tight">Your Documents</h2>
                    <Badge variant="secondary" className="text-xs">
                      {documents.length} file{documents.length !== 1 ? "s" : ""}
                    </Badge>
                </div>
                
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <Input 
                            type="search" 
                            placeholder="Search documents..." 
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
                No documents match your search <span className="font-semibold text-foreground">"{searchQuery}"</span>.
              </p>
              <Button variant="link" onClick={() => setSearchQuery('')} className="mt-2 text-primary">
                Clear search
              </Button>
            </motion.div>
          </div>
        ) : (
          <div className="space-y-4 pt-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
                <div className="flex items-center gap-3">
                    <h2 className="text-xl font-bold tracking-tight">Your Documents</h2>
                    <Badge variant="secondary" className="text-xs">
                      {documents.length} file{documents.length !== 1 ? "s" : ""}
                    </Badge>
                </div>
                
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <Input 
                            type="search" 
                            placeholder="Search documents..." 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 w-full sm:w-[250px] bg-card/40 border-border/50 focus-visible:ring-primary/20 transition-all rounded-full h-9"
                        />
                    </div>
                </div>
            </div>

            {filteredDocs.map((doc, i) => (
              <motion.div
                key={doc.id}
                initial="hidden"
                animate="visible"
                variants={fadeUp}
                custom={i + 1}
              >
                <Card className="group border-border/50 bg-card/40 backdrop-blur-sm transition-all hover:border-primary/30 hover:shadow-md hover:bg-card/60">
                  <CardContent className="flex items-center gap-4 p-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-orange-500/10 border border-orange-500/10 transition-transform group-hover:scale-105">
                      <FileText className="h-6 w-6 text-orange-500" />
                    </div>

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-bold text-foreground">{doc.filename}</p>
                      <p className="mt-0.5 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                        {formatBytes(doc.size_bytes)} • {formatDate(doc.created_at)}
                      </p>
                    </div>

                    <div className="flex items-center gap-1 opacity-70 group-hover:opacity-100 transition-opacity">
                      {/* Analyze Button */}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 gap-1.5 text-xs font-semibold text-primary hover:text-primary hover:bg-primary/10"
                        onClick={() => handleAnalyze(doc.id)}
                        disabled={analyzingDocId === doc.id}
                      >
                        {analyzingDocId === doc.id ? (
                          <>
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            Analyzing…
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-3.5 w-3.5" />
                            Analyze
                          </>
                        )}
                      </Button>

                      {/* View Analysis Button */}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/10"
                        onClick={() => handleViewAnalysis(doc.id)}
                        title="View latest analysis"
                      >
                        <Shield className="h-4 w-4" />
                      </Button>

                      {/* View Document Button */}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/10"
                        onClick={() => handleView(doc.id)}
                        disabled={viewLoading}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>

                      {/* Delete Button */}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                        onClick={() => setDocToDelete(doc.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}

        {/* ── Extracted text viewer (slide-in panel) ── */}
        <AnimatePresence>
          {selectedDoc && (
            <motion.div
              className="fixed inset-0 z-50 flex"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* Backdrop */}
              <div
                className="absolute inset-0 bg-background/60 backdrop-blur-sm"
                onClick={() => setSelectedDoc(null)}
              />

              {/* Panel */}
              <motion.div
                className="relative ml-auto flex h-full w-full max-w-2xl flex-col border-l border-border bg-background shadow-2xl"
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", damping: 30, stiffness: 300 }}
              >
                <div className="flex items-center justify-between border-b border-border px-6 py-4">
                  <div className="min-w-0">
                    <h3 className="truncate text-lg font-semibold">
                      {selectedDoc.filename}
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      {formatBytes(selectedDoc.size_bytes)} •{" "}
                      {formatDate(selectedDoc.created_at)}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setSelectedDoc(null)}
                  >
                    <X className="h-5 w-5" />
                  </Button>
                </div>

                <div className="flex-1 overflow-auto px-6 py-4">
                  <h4 className="mb-3 flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <FileText className="h-4 w-4" />
                    Extracted Text
                  </h4>
                  {selectedDoc.extracted_text ? (
                    <pre className="whitespace-pre-wrap rounded-lg border border-border bg-muted/30 p-4 text-sm leading-relaxed">
                      {selectedDoc.extracted_text}
                    </pre>
                  ) : (
                    <p className="text-sm italic text-muted-foreground">
                      No text could be extracted from this document.
                    </p>
                  )}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Compliance Result Panel ── */}
        <AnimatePresence>
          {complianceResult && (
            <CompliancePanel
              result={complianceResult}
              onClose={() => setComplianceResult(null)}
            />
          )}
        </AnimatePresence>
      </main>

      {/* Workflow Selection Modal */}
      <AlertDialog open={showWorkflowModal} onOpenChange={setShowWorkflowModal}>
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 mb-2">
              <Workflow className="h-6 w-6 text-primary" />
            </div>
            <AlertDialogTitle>Select Workflow</AlertDialogTitle>
            <AlertDialogDescription>
              Choose an active workflow to analyze this document.
            </AlertDialogDescription>
          </AlertDialogHeader>
          
          <div className="py-4 space-y-2 max-h-[300px] overflow-auto px-1">
            {workflows.length === 0 ? (
              <div className="text-center py-6 border rounded-lg border-dashed">
                <p className="text-sm text-muted-foreground">No active workflows available.</p>
                <Link to="/workflows" className="text-xs text-primary hover:underline mt-1 inline-block">
                  Go to Workflows
                </Link>
              </div>
            ) : (
              workflows.map(wf => (
                <button
                  key={wf.id}
                  onClick={() => startAnalysis(wf.id)}
                  className="w-full flex flex-col items-start p-3 rounded-lg border border-border/50 hover:bg-primary/5 hover:border-primary/30 transition-all text-left group"
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="font-bold text-sm group-hover:text-primary transition-colors">{wf.name}</span>
                    <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-500 border-none text-[10px] h-4">Active</Badge>
                  </div>
                  {wf.description && (
                    <p className="text-[11px] text-muted-foreground mt-1 line-clamp-1">{wf.description}</p>
                  )}
                </button>
              ))
            )}
            
            <button
                onClick={() => startAnalysis(null)}
                className="w-full flex items-center justify-between p-3 rounded-lg border border-dashed border-border/60 hover:bg-muted/30 transition-all text-left mt-2"
            >
                <span className="text-xs font-medium text-muted-foreground italic">Skip workflow (Use default analysis)</span>
            </button>
          </div>
          
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => { setDocToAnalyze(null); setShowWorkflowModal(false); }}>Cancel</AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
 
      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!docToDelete} onOpenChange={(open) => !open && setDocToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Document</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this document? This action cannot be undone and extracted text will be permanently lost.
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
