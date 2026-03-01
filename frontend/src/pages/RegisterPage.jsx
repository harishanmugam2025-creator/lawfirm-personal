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
  User,
  Eye,
  EyeOff,
  KeyRound,
  ArrowLeft,
} from "lucide-react";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState("");
  const [success, setSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // OTP State
  const [showOtp, setShowOtp] = useState(false);
  const [storedUserData, setStoredUserData] = useState(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    defaultValues: { name: "", email: "", password: "", confirmPassword: "", otpCode: "" },
  });

  const onSubmit = async (data) => {
    setServerError("");
    setIsSubmitting(true);

    try {
      if (!showOtp) {
        // Step 1: Send Registration OTP via Resend
        await api.post("/auth/registration-otp", {
          email: data.email,
        });
        setStoredUserData({
          name: data.name,
          email: data.email,
          password: data.password,
        });
        setShowOtp(true);
      } else {
        // Step 2: Verify OTP and Register
        await api.post("/auth/register", {
          name: storedUserData.name,
          email: storedUserData.email,
          password: storedUserData.password,
        }, {
           params: { otp_code: data.otpCode }
        });
        setSuccess(true);
        setTimeout(() => navigate("/login"), 1500);
      }
    } catch (err) {
      setServerError(
        err.response?.data?.detail || 
        (showOtp ? "Invalid OTP or registration failed." : "Failed to send verification email. Please try again.")
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
          <h2 className="text-2xl font-bold">Account Created!</h2>
          <p className="mt-2 text-muted-foreground">
            Redirecting you to sign in…
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
          to="/"
          className="mb-8 flex items-center justify-center gap-2 text-foreground"
        >
          <Scale className="h-7 w-7 text-primary" />
          <span className="text-xl font-bold tracking-tight">Veritas AI</span>
        </Link>

        <Card className="border-border/50 bg-card/80 backdrop-blur">
          <CardHeader className="space-y-1 text-center">
            {showOtp && (
               <div className="mb-4 text-left">
                  <button 
                     onClick={() => setShowOtp(false)}
                     className="text-sm flex items-center gap-1 text-muted-foreground hover:text-foreground"
                  >
                     <ArrowLeft className="h-4 w-4" /> Back
                  </button>
               </div>
            )}
            <CardTitle className="text-2xl font-bold">
              {showOtp ? "Verify your email" : "Create your account"}
            </CardTitle>
            <CardDescription>
              {showOtp 
                ? `We sent a code to ${storedUserData?.email}`
                : "Join Veritas AI and streamline your legal workflow"
              }
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

            <form
              id="register-form"
              onSubmit={handleSubmit(onSubmit)}
              noValidate
              className="space-y-5"
            >
              {!showOtp ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="name"
                        placeholder="John Doe"
                        className="pl-9"
                        {...register("name", { required: "Full name is required" })}
                      />
                    </div>
                    {errors.name && (
                      <p className="flex items-center gap-1 text-xs text-destructive">
                        <AlertCircle className="h-3 w-3" /> {errors.name.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="register-email"
                        type="email"
                        placeholder="you@lawfirm.com"
                        className="pl-9"
                        {...register("email", {
                          required: "Email is required",
                          pattern: {
                            value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                            message: "Enter a valid email address",
                          },
                        })}
                      />
                    </div>
                    {errors.email && (
                      <p className="flex items-center gap-1 text-xs text-destructive">
                        <AlertCircle className="h-3 w-3" /> {errors.email.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="register-password"
                        type={showPassword ? "text" : "password"}
                        placeholder="Min. 8 characters"
                        className="pl-9 pr-10"
                        {...register("password", {
                          required: "Password is required",
                          minLength: {
                            value: 8,
                            message: "Password must be at least 8 characters",
                          },
                        })}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                    {errors.password && (
                      <p className="flex items-center gap-1 text-xs text-destructive">
                        <AlertCircle className="h-3 w-3" />{" "}
                        {errors.password.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirm Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="register-confirmPassword"
                        type={showConfirmPassword ? "text" : "password"}
                        placeholder="Re-enter your password"
                        className="pl-9 pr-10"
                        {...register("confirmPassword", {
                          required: "Please confirm your password",
                          validate: (val) =>
                            val === watch("password") || "Passwords do not match",
                        })}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showConfirmPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                    {errors.confirmPassword && (
                      <p className="flex items-center gap-1 text-xs text-destructive">
                        <AlertCircle className="h-3 w-3" />{" "}
                        {errors.confirmPassword.message}
                      </p>
                    )}
                  </div>
                </>
              ) : (
                <Motion.div 
                   initial={{ opacity: 0, x: 20 }}
                   animate={{ opacity: 1, x: 0 }}
                   className="space-y-2"
                >
                  <Label htmlFor="otpCode">Verification Code</Label>
                  <div className="relative">
                    <KeyRound className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="otp-code"
                      placeholder="Enter 6-digit code"
                      className="pl-9 text-center tracking-widest text-lg font-mono"
                      maxLength={6}
                      {...register("otpCode", { 
                         required: "Verification code is required",
                         minLength: { value: 6, message: "Code must be 6 characters" }
                      })}
                    />
                  </div>
                  {errors.otpCode && (
                    <p className="flex items-center gap-1 text-xs text-destructive">
                      <AlertCircle className="h-3 w-3" /> {errors.otpCode.message}
                    </p>
                  )}
                  <p className="text-xs text-center text-muted-foreground mt-4 border-t border-border pt-3">
                    <strong>Demo Mode Active:</strong> If you don't receive an email (due to free-tier provider limits), you can bypass verification by entering <strong>123456</strong>.
                  </p>
                </Motion.div>
              )}
            </form>
          </CardContent>

          <CardFooter className="flex flex-col gap-4">
            <Button
              type="submit"
              form="register-form"
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> {showOtp ? "Verifying..." : "Sending Code..."}
                </>
              ) : (
                showOtp ? "Create Account" : "Continue"
              )}
            </Button>

            {!showOtp && (
               <>
                 <Separator />
                 <p className="text-center text-sm text-muted-foreground">
                   Already have an account?{" "}
                   <Link
                     to="/login"
                     className="font-medium text-primary underline-offset-4 hover:underline"
                   >
                     Sign in
                   </Link>
                 </p>
               </>
            )}
          </CardFooter>
        </Card>
      </Motion.div>
    </div>
  );
}
