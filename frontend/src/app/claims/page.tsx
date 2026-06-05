"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { format } from "date-fns";
import { Search, ChevronRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getClaims } from "@/lib/api";
import type { ClaimSummary } from "@/lib/types";

const STATUS_BADGE: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
  submitted: { variant: "secondary", label: "Submitted" },
  processing: { variant: "secondary", label: "Processing" },
  completed: { variant: "default", label: "Completed" },
  manual_review: { variant: "outline", label: "Manual Review" },
};

const DECISION_BADGE: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
  APPROVED: { variant: "default", label: "Approved" },
  REJECTED: { variant: "destructive", label: "Rejected" },
  PARTIAL: { variant: "outline", label: "Partial" },
  MANUAL_REVIEW: { variant: "secondary", label: "Manual Review" },
};

function ClaimsListInner() {
  const searchParams = useSearchParams();
  const memberIdParam = searchParams.get("member_id") || "";

  const [memberId, setMemberId] = useState(memberIdParam);
  const [claims, setClaims] = useState<ClaimSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchClaims = async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getClaims(id);
      setClaims(data.claims);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch claims");
      setClaims([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (memberIdParam) {
      fetchClaims(memberIdParam);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [memberIdParam]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchClaims(memberId);
  };

  return (
    <div className="container mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold tracking-tight">Claim History</h1>
      <p className="mt-2 text-muted-foreground">
        Search and view past claims by member ID
      </p>

      <form onSubmit={handleSearch} className="mt-8 flex gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Enter Member ID (e.g. EMP001)"
            value={memberId}
            onChange={(e) => setMemberId(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </Button>
      </form>

      <div className="mt-8">
        {error && (
          <Card className="border-destructive/50 bg-destructive/5">
            <CardContent className="py-6 text-center text-destructive">
              {error}
            </CardContent>
          </Card>
        )}

        {!loading && claims.length === 0 && !error && memberIdParam && (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              No claims found for member {memberIdParam}
            </CardContent>
          </Card>
        )}

        {!memberIdParam && !error && (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              Enter a member ID to view their claim history
            </CardContent>
          </Card>
        )}

        {claims.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Showing {claims.length} claim{claims.length !== 1 ? "s" : ""}
            </p>
            {claims.map((claim) => {
              const statusBadge = STATUS_BADGE[claim.status] || STATUS_BADGE.submitted;
              const decisionBadge = claim.decision
                ? DECISION_BADGE[claim.decision]
                : null;

              return (
                <Link key={claim.id} href={`/claims/${claim.id}`}>
                  <Card className="cursor-pointer transition-shadow hover:shadow-md">
                    <CardContent className="flex items-center justify-between py-4">
                      <div className="flex items-center gap-6">
                        <div>
                          <p className="font-mono text-sm font-bold text-primary">
                            {claim.claim_code}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {format(new Date(claim.treatment_date), "dd MMM yyyy")}
                          </p>
                        </div>
                        <Badge variant={statusBadge.variant}>
                          {statusBadge.label}
                        </Badge>
                        {decisionBadge && (
                          <Badge variant={decisionBadge.variant}>
                            {decisionBadge.label}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="font-bold">₹{claim.claim_amount.toLocaleString("en-IN")}</p>
                          {claim.approved_amount != null && (
                            <p className="text-xs text-muted-foreground">
                              Approved: ₹{claim.approved_amount.toLocaleString("en-IN")}
                            </p>
                          )}
                        </div>
                        <ChevronRight className="h-5 w-5 text-muted-foreground" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ClaimsListPage() {
  return (
    <Suspense
      fallback={
        <div className="container mx-auto px-4 py-10">
          <h1 className="text-3xl font-bold tracking-tight">Claim History</h1>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      }
    >
      <ClaimsListInner />
    </Suspense>
  );
}
