"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import { format } from "date-fns";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Separator } from "@/components/ui/separator";
import { getClaim } from "@/lib/api";
import type { ClaimDetail } from "@/lib/types";
import { cn } from "@/lib/utils";

const DECISION_CONFIG: Record<string, {
  icon: typeof CheckCircle;
  color: string;
  bg: string;
  border: string;
}> = {
  APPROVED: {
    icon: CheckCircle,
    color: "text-success",
    bg: "bg-success/10",
    border: "border-success/30",
  },
  REJECTED: {
    icon: XCircle,
    color: "text-destructive",
    bg: "bg-destructive/10",
    border: "border-destructive/30",
  },
  PARTIAL: {
    icon: AlertTriangle,
    color: "text-warning",
    bg: "bg-warning/10",
    border: "border-warning/30",
  },
  MANUAL_REVIEW: {
    icon: Clock,
    color: "text-blue-500",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
};

export default function ClaimDetailPage() {
  const params = useParams();
  const claimId = params.claim_id as string;

  const [claim, setClaim] = useState<ClaimDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchClaim = useCallback(async () => {
    try {
      const data = await getClaim(claimId);
      setClaim(data);
      setError(null);

      // Stop polling if claim is no longer processing
      if (data.status !== "processing" && data.status !== "submitted") {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load claim");
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } finally {
      setLoading(false);
    }
  }, [claimId]);

  useEffect(() => {
    fetchClaim().then(() => {
      // Start polling if initial fetch shows processing
      // We need to check the claim state after first fetch
    });

    // Start polling — will be stopped when claim is completed
    intervalRef.current = setInterval(fetchClaim, 2000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchClaim]);

  if (loading) {
    return (
      <div className="container mx-auto flex min-h-[60vh] items-center justify-center px-4">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary" />
          <p className="mt-4 text-muted-foreground">Loading claim details...</p>
        </div>
      </div>
    );
  }

  if (error || !claim) {
    return (
      <div className="container mx-auto px-4 py-16">
        <Card className="mx-auto max-w-md border-destructive/50 bg-destructive/5">
          <CardContent className="py-10 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
            <p className="mt-4 text-destructive">{error || "Claim not found"}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const decisionConf = claim.decision ? DECISION_CONFIG[claim.decision] : null;
  const DecisionIcon = decisionConf?.icon;

  const isProcessing = claim.status === "submitted" || claim.status === "processing";

  // Format the status label for display
  const statusLabel = (() => {
    switch (claim.status) {
      case "submitted": return "Submitted";
      case "processing": return "Processing...";
      case "completed": return "Completed";
      case "manual_review": return "Manual Review";
      default: return claim.status;
    }
  })();

  return (
    <div className="container mx-auto px-4 py-10">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Claim {claim.claim_code}
          </h1>
          <p className="mt-1 text-muted-foreground">
            Submitted on {format(new Date(claim.submission_date), "dd MMM yyyy")}
          </p>
        </div>
        <Badge
          variant={claim.status === "completed" ? "default" : "secondary"}
          className="w-fit px-4 py-2 text-sm"
        >
          {statusLabel}
        </Badge>
      </div>

      {/* Processing indicator */}
      {isProcessing && (
        <Card className="mb-8 border-blue-200 bg-blue-50">
          <CardContent className="flex items-center gap-4 py-6">
            <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            <div>
              <p className="font-medium text-blue-700">
                Processing your claim...
              </p>
              <p className="text-sm text-blue-600">
                Documents are being analyzed and validated against policy terms
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Decision Card */}
      {claim.decision && decisionConf && DecisionIcon && (
        <Card
          className={cn(
            "mb-8 border-2",
            decisionConf.border,
            decisionConf.bg
          )}
        >
          <CardContent className="py-8">
            <div className="flex flex-col items-center text-center sm:flex-row sm:text-left">
              <DecisionIcon className={cn("mb-4 h-14 w-14 sm:mb-0 sm:mr-6", decisionConf.color)} />
              <div>
                <h2 className="text-2xl font-bold">{claim.decision}</h2>
                {claim.decision === "APPROVED" && claim.approved_amount != null && (
                  <p className="mt-2 text-lg">
                    Approved Amount:{" "}
                    <span className="font-bold text-success">
                      ₹{claim.approved_amount.toLocaleString("en-IN")}
                    </span>
                  </p>
                )}
                {claim.decision === "PARTIAL" && claim.approved_amount != null && (
                  <p className="mt-2 text-lg">
                    Partial Approval:{" "}
                    <span className="font-bold text-warning">
                      ₹{claim.approved_amount.toLocaleString("en-IN")}
                    </span>{" "}
                    of ₹{claim.claim_amount.toLocaleString("en-IN")}
                  </p>
                )}
                {claim.decision === "REJECTED" && (
                  <p className="mt-2 text-muted-foreground">
                    Claim amount: ₹{claim.claim_amount.toLocaleString("en-IN")}
                  </p>
                )}
                {claim.notes && (
                  <p className="mt-2 text-sm text-muted-foreground">
                    {claim.notes}
                  </p>
                )}
              </div>
              {claim.confidence_score != null && (
                <div className="mt-4 sm:ml-auto sm:mt-0">
                  <div className="rounded-full border-2 border-primary/20 p-4 text-center">
                    <div className="text-2xl font-bold text-primary">
                      {Math.round(claim.confidence_score * 100)}%
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Confidence
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Claim Details */}
        <Card>
          <CardHeader>
            <CardTitle>Claim Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Member ID</span>
              <span className="font-mono font-medium">{claim.member_code}</span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-muted-foreground">Member Name</span>
              <span className="font-medium">{claim.member_name}</span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-muted-foreground">Treatment Date</span>
              <span>{format(new Date(claim.treatment_date), "dd MMM yyyy")}</span>
            </div>
            <Separator />
            <div className="flex justify-between">
              <span className="text-muted-foreground">Claim Amount</span>
              <span className="font-bold">₹{claim.claim_amount.toLocaleString("en-IN")}</span>
            </div>
            {claim.hospital_name && (
              <>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Hospital</span>
                  <span>{claim.hospital_name}</span>
                </div>
              </>
            )}
            {claim.is_network && (
              <>
                <Separator />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Network Hospital</span>
                  <Badge variant="default">Yes</Badge>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Rejection Reasons */}
        {claim.rejection_reasons && claim.rejection_reasons.length > 0 && (
          <Card className="border-destructive/30">
            <CardHeader>
              <CardTitle className="text-destructive">Rejection Reasons</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {claim.rejection_reasons.map((r, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 rounded-md bg-destructive/5 px-3 py-2"
                  >
                    <XCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-destructive" />
                    <div>
                      <span className="font-mono text-xs text-destructive">
                        {r.reason_code}
                      </span>
                      <p className="text-sm">{r.reason_description}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Fraud Flags */}
        {claim.fraud_flags && claim.fraud_flags.length > 0 && (
          <Card className="border-warning/30">
            <CardHeader>
              <CardTitle className="text-warning">Fraud Flags</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {claim.fraud_flags.map((f, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 rounded-md bg-warning/5 px-3 py-2"
                  >
                    <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-warning" />
                    <div>
                      <span className="font-mono text-xs text-warning">
                        {f.flag_type}
                      </span>
                      <p className="text-sm">{f.flag_details}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Adjudication Steps */}
        {claim.adjudication_steps && claim.adjudication_steps.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Adjudication Steps</CardTitle>
              <CardDescription>Pipeline execution details</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {claim.adjudication_steps.map((step) => (
                  <div key={step.step_number} className="flex items-start gap-3">
                    <div
                      className={cn(
                        "mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold",
                        step.passed
                          ? "bg-success/20 text-success"
                          : "bg-destructive/20 text-destructive"
                      )}
                    >
                      {step.passed ? "✓" : "✗"}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium capitalize">
                        Step {step.step_number}: {step.step_name}
                      </p>
                      {step.details && (
                        <p className="text-xs text-muted-foreground">
                          {JSON.stringify(step.details)}
                        </p>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {step.execution_time_ms}ms
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Extracted Data */}
        {claim.extracted_data && claim.extracted_data.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Extracted Data</CardTitle>
              <CardDescription>AI-extracted fields from documents</CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="multiple">
                {claim.extracted_data.map((doc, i) => (
                  <AccordionItem key={i} value={`doc-${i}`}>
                    <AccordionTrigger className="text-sm">
                      {doc.document_type} — Confidence:{" "}
                      {doc.extraction_confidence != null
                        ? `${Math.round(doc.extraction_confidence * 100)}%`
                        : "N/A"}
                    </AccordionTrigger>
                    <AccordionContent>
                      <pre className="max-h-60 overflow-auto rounded-md bg-muted p-3 text-xs">
                        {JSON.stringify(doc.structure_json, null, 2)}
                      </pre>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
