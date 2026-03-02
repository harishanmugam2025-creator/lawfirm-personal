import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { motion as Motion } from "framer-motion";
import api from "@/services/api";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Scale,
  Mail,
  Lock,
  AlertCircle,
  Loader2,
  CheckCircle2,
  ArrowLeft,
  KeyRound,
  Eye,
  EyeOff,
} from "lucide-react";

export default function ForgotPasswordPage() {
  const [step, setStep] = useState(1); // 1: Email, 2: OTP & New Password
  const [email, setEmail] = useState("");
  const [serverError, setServerError] = useState("");
  const [success, setSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    defaultValues: { otp_code: "", new_password: "", confirm_password: "" },
  });

  const requestOtp = async (e) => {
    e.preventDefault();
    setServerError("");
    setIsSubmitting(true);
    try {
      await api.post("/auth/forgot-password", { email });
      setStep(2);
    } catch (err) {
      setServerError(
        err.response?.data?.detail || "Failed to send OTP. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetPassword = async (data) => {
    setServerError("");
    setIsSubmitting(true);
    try {
      await api.post("/auth/reset-password", {
        email,
        otp_code: data.otp_code,
        new_password: data.new_password,
      });
      setSuccess(true);
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      setServerError(
        err.response?.data?.detail || "Failed to reset password. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <Motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-center"
        >
          <CheckCircle2 className="mx-auto mb-4 h-16 w-16 text-green-400" />
          <h2 className="text-2xl font-bold">Password Reset!</h2>
          <p className="mt-2 text-muted-foreground">
            Your password has been updated. Redirecting to sign in…
          </p>
        </Motion.div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-primary/5 blur-3xl" />
      </div>

      <Motion.div
        className="relative z-10 w-full max-w-md"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Link
          to="/login"
          className="mb-8 flex items-center justify-center gap-2 text-foreground"
        >
          <Scale className="h-7 w-7 text-primary" />
          <span className="text-xl font-bold tracking-tight">Veritas AI</span>
        </Link>

        <Card className="border-border/50 bg-card/80 backdrop-blur">
          <CardHeader className="space-y-1 text-center">
            <CardTitle className="text-2xl font-bold">
              {step === 1 ? "Forgot password?" : "Reset password"}
            </CardTitle>
            <CardDescription>
              {step === 1
                ? "Enter your email for a verification code"
                : "Enter the code sent to your email (Demo: 123456) and your new password"}
            </CardDescription>
          </CardHeader>

          <CardContent>
            {serverError && (
              <Motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="mb-4 flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2.5 text-sm text-destructive"
              >
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{serverError}</span>
              </Motion.div>
            )}

            {step === 1 ? (
              <form onSubmit={requestOtp} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@lawfirm.com"
                      className="pl-9"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <Button type="submit" className="w-full" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Sending...
                    </>
                  ) : (
                    "Send Verification Code"
                  )}
                </Button>
              </form>
            ) : (
              <form onSubmit={handleSubmit(resetPassword)} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="otp">Verification Code</Label>
                  <div className="relative">
                    <KeyRound className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="otp"
                      placeholder="6-digit code"
                      className="pl-9"
                      {...register("otp_code", {
                        required: "OTP code is required",
                        pattern: { value: /^\d{6}$/, message: "Enter 6-digit code" },
                      })}
                    />
                  </div>
                  {errors.otp_code && (
                    <p className="text-xs text-destructive">{errors.otp_code.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="new_password">New Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="new_password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Min. 8 characters"
                      className="pl-9 pr-10"
                      {...register("new_password", {
                        required: "Password is required",
                        minLength: { value: 8, message: "Min 8 characters" },
                      })}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {errors.new_password && (
                    <p className="text-xs text-destructive">{errors.new_password.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm_password">Confirm New Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="confirm_password"
                      type="password"
                      placeholder="Repeate new password"
                      className="pl-9"
                      {...register("confirm_password", {
                        required: "Please confirm your password",
                        validate: (val) =>
                          val === watch("new_password") || "Passwords do not match",
                      })}
                    />
                  </div>
                  {errors.confirm_password && (
                    <p className="text-xs text-destructive">
                      {errors.confirm_password.message}
                    </p>
                  )}
                </div>

                <Button type="submit" className="w-full" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Resetting...
                    </>
                  ) : (
                    "Reset Password"
                  )}
                </Button>
                <Button
                  variant="outline"
                  type="button"
                  className="w-full"
                  onClick={() => setStep(1)}
                  disabled={isSubmitting}
                >
                  Back to Email
                </Button>
              </form>
            )}
          </CardContent>

          <CardFooter>
            <Link
              to="/login"
              className="flex w-full items-center justify-center gap-2 text-sm text-muted-foreground hover:text-primary"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to sign in
            </Link>
          </CardFooter>
        </Card>
      </Motion.div>
    </div>
  );
}
