import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { usersService } from "@/services/users";
import { useAuth } from "@/context/useAuth";
import { ThemeToggle } from "@/components/ThemeToggle";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Scale,
  ArrowLeft,
  Users,
  UserPlus,
  Loader2,
  AlertCircle,
  X,
  Search,
  Shield,
  ShieldCheck,
  Crown,
  Briefcase,
  Settings,
  Mail,
  Lock,
  User,
  MoreVertical,
  Pencil,
  UserX,
  Trash2,
  KeyRound,
  CheckCircle2,
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.4 },
  }),
};

const roleConfig = {
  paralegal: { label: "Paralegal", icon: Users, color: "text-blue-500", bg: "bg-blue-500/10", border: "border-blue-500/20" },
  associate: { label: "Associate", icon: Briefcase, color: "text-emerald-500", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  partner: { label: "Partner", icon: Crown, color: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  it_admin: { label: "IT Admin", icon: Settings, color: "text-violet-500", bg: "bg-violet-500/10", border: "border-violet-500/20" },
};

/* ── Create User Modal ── */
function CreateUserModal({ open, onClose, onCreated }) {
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "paralegal" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.password || !form.role) {
      setError("All fields are required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await usersService.create(form);
      toast.success(`User ${form.email} created successfully`);
      setForm({ name: "", email: "", password: "", role: "paralegal" });
      onCreated();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create user.");
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-background/60 backdrop-blur-sm" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl"
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
              <UserPlus className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-bold">Create User</h3>
              <p className="text-xs text-muted-foreground">Assign role and credentials</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Full Name</Label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="John Doe"
                className="pl-9"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="email"
                placeholder="user@lawfirm.com"
                className="pl-9"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Temporary Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="password"
                placeholder="Min. 8 characters"
                className="pl-9"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Role</Label>
            <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="paralegal">Paralegal</SelectItem>
                <SelectItem value="associate">Associate</SelectItem>
                <SelectItem value="partner">Partner</SelectItem>
                <SelectItem value="it_admin">IT Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Creating…
              </>
            ) : (
              "Create User"
            )}
          </Button>
        </form>
      </motion.div>
    </div>
  );
}

/* ── Edit User Modal ── */
function EditUserModal({ open, user, onClose, onUpdated }) {
  const [form, setForm] = useState({ name: "", role: "paralegal", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user) {
      setForm({ name: user.name || "", role: user.role, password: "" });
      setError("");
    }
  }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const updates = {};
    if (form.name && form.name !== user.name) updates.name = form.name;
    if (form.role && form.role !== user.role) updates.role = form.role;
    if (form.password) updates.password = form.password;

    if (Object.keys(updates).length === 0) {
      setError("No changes to save.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      await usersService.update(user.id, updates);
      toast.success("User updated successfully");
      onUpdated();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update user.");
    } finally {
      setLoading(false);
    }
  };

  if (!open || !user) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-background/60 backdrop-blur-sm" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl"
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
              <Pencil className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-bold">Edit User</h3>
              <p className="text-xs text-muted-foreground">{user.email}</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Name</Label>
            <Input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label>Role</Label>
            <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
              <SelectTrigger>
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="paralegal">Paralegal</SelectItem>
                <SelectItem value="associate">Associate</SelectItem>
                <SelectItem value="partner">Partner</SelectItem>
                <SelectItem value="it_admin">IT Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Reset Password <span className="text-muted-foreground text-xs">(leave blank to keep)</span></Label>
            <div className="relative">
              <KeyRound className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="password"
                placeholder="New password (min 8 chars)"
                className="pl-9"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving…
              </>
            ) : (
              "Save Changes"
            )}
          </Button>
        </form>
      </motion.div>
    </div>
  );
}

/* ── Main Page ── */
export default function UserManagementPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [deactivateTarget, setDeactivateTarget] = useState(null);
  const [activateTarget, setActivateTarget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const fetchUsers = useCallback(async () => {
    try {
      const data = await usersService.list();
      setUsers(data.users);
    } catch {
      setError("Failed to load users.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const filteredUsers = users.filter(
    (u) =>
      (u.name || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.role.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const confirmDeactivate = async () => {
    if (!deactivateTarget) return;
    try {
      await usersService.deactivate(deactivateTarget);
      toast.success("User deactivated");
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to deactivate user.");
    } finally {
      setDeactivateTarget(null);
    }
  };

  const confirmActivate = async () => {
    if (!activateTarget) return;
    try {
      await usersService.activate(activateTarget);
      toast.success("User activated");
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to activate user.");
    } finally {
      setActivateTarget(null);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await usersService.delete(deleteTarget);
      toast.success("User permanently deleted");
      fetchUsers();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to delete user.");
    } finally {
      setDeleteTarget(null);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    const date = new Date(dateStr.endsWith("Z") ? dateStr : dateStr + "Z");
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const stats = {
    total: users.length,
    active: users.filter((u) => u.is_active).length,
    admins: users.filter((u) => u.role === "it_admin").length,
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* ── Header ── */}
      <header className="sticky top-0 z-40 border-b border-border/40 bg-background/80 backdrop-blur-lg">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Link to="/dashboard" className="text-muted-foreground hover:text-foreground transition-colors">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <Separator orientation="vertical" className="h-6" />
            <Scale className="h-6 w-6 text-primary" />
            <div>
              <span className="text-lg font-bold tracking-tight">User Management</span>
              <p className="text-[11px] text-muted-foreground -mt-0.5">System Config</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              size="sm"
              className="gap-1.5"
              onClick={() => setShowCreate(true)}
            >
              <UserPlus className="h-4 w-4" />
              Create User
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mb-6 flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
            <button className="ml-auto" onClick={() => setError("")}>
              <X className="h-4 w-4" />
            </button>
          </motion.div>
        )}

        {/* ── System Config Tabs ── */}
        <div className="mb-8 border-b border-border/40">
          <div className="flex gap-8">
            <Link
              to="/system/users"
              className="relative pb-4 text-sm font-bold text-primary"
            >
              User Management
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
              />
            </Link>
            <Link
              to="/system/rbac"
              className="relative pb-4 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Roles & Permissions
            </Link>
          </div>
        </div>

        {/* ── Stats ── */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeUp}
          className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3"
        >
          <Card className="border-border/50 bg-card/40 backdrop-blur-sm">
            <CardContent className="flex items-center gap-4 p-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
                <Users className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-black">{stats.total}</p>
                <p className="text-xs text-muted-foreground font-medium">Total Users</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card/40 backdrop-blur-sm">
            <CardContent className="flex items-center gap-4 p-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <CheckCircle2 className="h-6 w-6 text-emerald-500" />
              </div>
              <div>
                <p className="text-2xl font-black">{stats.active}</p>
                <p className="text-xs text-muted-foreground font-medium">Active</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card/40 backdrop-blur-sm">
            <CardContent className="flex items-center gap-4 p-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-violet-500/10 border border-violet-500/20">
                <ShieldCheck className="h-6 w-6 text-violet-500" />
              </div>
              <div>
                <p className="text-2xl font-black">{stats.admins}</p>
                <p className="text-xs text-muted-foreground font-medium">Admins</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* ── Search + heading ── */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold tracking-tight">All Users</h2>
            <Badge variant="secondary" className="text-xs">{users.length}</Badge>
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 w-full sm:w-[250px] bg-card/40 border-border/50 focus-visible:ring-primary/20 transition-all rounded-full h-9"
            />
          </div>
        </div>

        {/* ── Users Table ── */}
        {loading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <Card className="border-border/50 bg-card/40 backdrop-blur-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border/50 bg-muted/30">
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">User</th>
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Role</th>
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Created</th>
                    <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30">
                  {filteredUsers.length > 0 ? (
                    filteredUsers.map((u, i) => {
                      const rc = roleConfig[u.role] || roleConfig.paralegal;
                      const RoleIcon = rc.icon;
                      const isSelf = u.id === currentUser?.id;
                      return (
                        <motion.tr
                          key={u.id}
                          initial="hidden"
                          animate="visible"
                          variants={fadeUp}
                          custom={i}
                          className="group hover:bg-muted/20 transition-colors"
                        >
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-3">
                              <div className={`flex h-9 w-9 items-center justify-center rounded-full ${rc.bg} ${rc.border} border`}>
                                <span className={`text-sm font-bold ${rc.color}`}>
                                  {(u.name || u.email)[0].toUpperCase()}
                                </span>
                              </div>
                              <div className="min-w-0">
                                <p className="text-sm font-semibold truncate">
                                  {u.name || "—"}
                                  {isSelf && <span className="ml-1.5 text-[10px] text-muted-foreground">(You)</span>}
                                </p>
                                <p className="text-xs text-muted-foreground truncate">{u.email}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <Badge variant="outline" className={`gap-1 ${rc.border} ${rc.bg} ${rc.color} border`}>
                              <RoleIcon className="h-3 w-3" />
                              {rc.label}
                            </Badge>
                          </td>
                          <td className="px-4 py-3">
                            {u.is_active ? (
                              <Badge className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/20">
                                Active
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="bg-red-500/10 text-red-500 border border-red-500/20">
                                Inactive
                              </Badge>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-xs text-muted-foreground">{formatDate(u.created_at)}</span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 opacity-70 group-hover:opacity-100">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => setEditUser(u)}>
                                  <Pencil className="mr-2 h-4 w-4" />
                                  Edit User
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => setEditUser({ ...u, _resetPassword: true })}>
                                  <KeyRound className="mr-2 h-4 w-4" />
                                  Reset Password
                                </DropdownMenuItem>
                                  {!isSelf && u.is_active && (
                                    <>
                                      <DropdownMenuSeparator />
                                      <DropdownMenuItem
                                        className="text-destructive focus:text-destructive"
                                        onClick={() => setDeactivateTarget(u.id)}
                                      >
                                        <UserX className="mr-2 h-4 w-4" />
                                        Deactivate
                                      </DropdownMenuItem>
                                    </>
                                  )}
                                  {!isSelf && !u.is_active && (
                                    <>
                                      <DropdownMenuSeparator />
                                      <DropdownMenuItem
                                        className="text-emerald-500 focus:text-emerald-500"
                                        onClick={() => setActivateTarget(u.id)}
                                      >
                                        <CheckCircle2 className="mr-2 h-4 w-4" />
                                        Activate
                                      </DropdownMenuItem>
                                    </>
                                  )}
                                  {!isSelf && (
                                    <>
                                      <DropdownMenuSeparator />
                                      <DropdownMenuItem
                                        className="text-destructive focus:text-destructive"
                                        onClick={() => setDeleteTarget(u.id)}
                                      >
                                        <Trash2 className="mr-2 h-4 w-4" />
                                        Delete User
                                      </DropdownMenuItem>
                                    </>
                                  )}
                                </DropdownMenuContent>
                            </DropdownMenu>
                          </td>
                        </motion.tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={5} className="px-4 py-12 text-center">
                        <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground">
                          <Search className="h-8 w-8 opacity-20" />
                          <p className="text-sm font-medium">No users match your search criteria</p>
                          <Button 
                            variant="link" 
                            size="sm" 
                            onClick={() => setSearchQuery("")}
                            className="text-primary font-bold h-auto p-0"
                          >
                            Clear search
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </main>

      {/* ── Modals ── */}
      <CreateUserModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreated={fetchUsers}
      />
      <EditUserModal
        open={!!editUser}
        user={editUser}
        onClose={() => setEditUser(null)}
        onUpdated={fetchUsers}
      />
      <AlertDialog open={!!deactivateTarget} onOpenChange={(open) => !open && setDeactivateTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Deactivate User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to deactivate this user? They will no longer be able to log in. This action can be reversed by an IT Admin.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDeactivate} className="bg-destructive text-white hover:bg-destructive/90">
              Deactivate
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={!!activateTarget} onOpenChange={(open) => !open && setActivateTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Activate User</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to reactivate this user? They will regain access to their account and the system.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmActivate} className="bg-emerald-500 text-white hover:bg-emerald-600">
              Activate
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="text-destructive flex items-center gap-2">
              <Trash2 className="h-5 w-5" />
              Permanently Delete User?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This action is irreversible. All records associated with this user will be permanently removed from the system.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-destructive text-white hover:bg-destructive/90">
              Permanently Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
