"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, CheckCircle, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { submitClaim } from "@/lib/api";

const claimSchema = z.object({
  member_id: z.string().min(1, "Member ID is required"),
  member_name: z.string().min(1, "Member name is required"),
  treatment_date: z.string().min(1, "Treatment date is required"),
  claim_amount: z
    .string()
    .min(1, "Claim amount is required")
    .refine((val) => !isNaN(Number(val)) && Number(val) > 0, {
      message: "Must be a positive number",
    }),
  hospital_name: z.string().optional(),
  cashless_request: z.boolean().optional(),
  // Prescription fields
  doctor_name: z.string().optional(),
  doctor_reg: z.string().optional(),
  diagnosis: z.string().optional(),
  medicines: z.string().optional(),
  treatment: z.string().optional(),
  // Bill fields
  consultation_fee: z.string().optional(),
  diagnostic_tests: z.string().optional(),
  medicines_cost: z.string().optional(),
  therapy_charges: z.string().optional(),
});

type ClaimFormData = z.infer<typeof claimSchema>;

export default function SubmitClaimPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedClaimId, setSubmittedClaimId] = useState<string | null>(null);
  const [procedures, setProcedures] = useState<string[]>([]);
  const [newProcedure, setNewProcedure] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ClaimFormData>({
    resolver: zodResolver(claimSchema),
    defaultValues: {
      cashless_request: false,
    },
  });

  const addProcedure = () => {
    if (newProcedure.trim()) {
      setProcedures((prev) => [...prev, newProcedure.trim()]);
      setNewProcedure("");
    }
  };

  const removeProcedure = (index: number) => {
    setProcedures((prev) => prev.filter((_, i) => i !== index));
  };

  const onSubmit = async (data: ClaimFormData) => {
    setIsSubmitting(true);
    try {
      // Build the structured JSON that the backend expects
      const documents: Record<string, unknown> = {};

      // Build prescription if any prescription fields are filled
      if (data.doctor_name || data.doctor_reg || data.diagnosis) {
        const prescription: Record<string, unknown> = {};
        if (data.doctor_name) prescription.doctor_name = data.doctor_name;
        if (data.doctor_reg) prescription.doctor_reg = data.doctor_reg;
        if (data.diagnosis) prescription.diagnosis = data.diagnosis;
        if (data.medicines) {
          prescription.medicines_prescribed = data.medicines
            .split(",")
            .map((m) => m.trim())
            .filter(Boolean);
        }
        if (data.treatment) prescription.treatment = data.treatment;
        if (procedures.length > 0) prescription.procedures = procedures;
        documents.prescription = prescription;
      }

      // Build bill if any bill fields are filled
      const bill: Record<string, number> = {};
      if (data.consultation_fee && Number(data.consultation_fee) > 0) {
        bill.consultation_fee = Number(data.consultation_fee);
      }
      if (data.diagnostic_tests && Number(data.diagnostic_tests) > 0) {
        bill.diagnostic_tests = Number(data.diagnostic_tests);
      }
      if (data.medicines_cost && Number(data.medicines_cost) > 0) {
        bill.medicines = Number(data.medicines_cost);
      }
      if (data.therapy_charges && Number(data.therapy_charges) > 0) {
        bill.therapy_charges = Number(data.therapy_charges);
      }
      if (Object.keys(bill).length > 0) {
        documents.bill = bill;
      }

      const payload = {
        member_id: data.member_id,
        member_name: data.member_name,
        treatment_date: data.treatment_date,
        claim_amount: Number(data.claim_amount),
        hospital: data.hospital_name || undefined,
        cashless_request: data.cashless_request || false,
        documents,
      };

      const result = await submitClaim(payload);
      setSubmittedClaimId(result.claim_id);
      toast.success("Claim submitted successfully!");
      setTimeout(() => {
        router.push(`/claims/${result.claim_id}`);
      }, 2000);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to submit claim"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submittedClaimId) {
    return (
      <div className="container mx-auto flex min-h-[60vh] items-center justify-center px-4 py-16">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-12 pb-10">
            <CheckCircle className="mx-auto h-16 w-16 text-success" />
            <h2 className="mt-4 text-2xl font-bold">Claim Submitted!</h2>
            <p className="mt-2 text-muted-foreground">
              Your claim is being processed. Claim ID:{" "}
              <span className="font-mono font-bold text-primary">
                {submittedClaimId}
              </span>
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Redirecting to claim details...
            </p>
            <div className="mt-6">
              <Loader2 className="mx-auto h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tight">Submit a Claim</h1>
        <p className="mt-2 text-muted-foreground">
          Fill in the claim details and medical document information
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-8">
          {/* Member & Claim Details */}
          <Card>
            <CardHeader>
              <CardTitle>Claim Details</CardTitle>
              <CardDescription>
                Enter the basic information about your claim
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="member_id">Member ID *</Label>
                  <Input
                    id="member_id"
                    placeholder="EMP001"
                    {...register("member_id")}
                  />
                  {errors.member_id && (
                    <p className="text-sm text-destructive">
                      {errors.member_id.message}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="member_name">Member Name *</Label>
                  <Input
                    id="member_name"
                    placeholder="Rajesh Kumar"
                    {...register("member_name")}
                  />
                  {errors.member_name && (
                    <p className="text-sm text-destructive">
                      {errors.member_name.message}
                    </p>
                  )}
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="treatment_date">Treatment Date *</Label>
                  <Input
                    id="treatment_date"
                    type="date"
                    {...register("treatment_date")}
                  />
                  {errors.treatment_date && (
                    <p className="text-sm text-destructive">
                      {errors.treatment_date.message}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="claim_amount">Claim Amount (₹) *</Label>
                  <Input
                    id="claim_amount"
                    type="number"
                    placeholder="1500"
                    min="0"
                    step="0.01"
                    {...register("claim_amount")}
                  />
                  {errors.claim_amount && (
                    <p className="text-sm text-destructive">
                      {errors.claim_amount.message}
                    </p>
                  )}
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="hospital_name">Hospital / Clinic</Label>
                  <Input
                    id="hospital_name"
                    placeholder="Apollo Hospitals"
                    {...register("hospital_name")}
                  />
                </div>
                <div className="flex items-end space-x-2 pb-1">
                  <input
                    type="checkbox"
                    id="cashless_request"
                    className="h-4 w-4 rounded border-gray-300"
                    {...register("cashless_request")}
                  />
                  <Label htmlFor="cashless_request" className="text-sm cursor-pointer">
                    Request cashless treatment
                  </Label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Prescription Details */}
          <Card>
            <CardHeader>
              <CardTitle>Prescription Details</CardTitle>
              <CardDescription>
                Enter details from the doctor&apos;s prescription
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="doctor_name">Doctor Name</Label>
                  <Input
                    id="doctor_name"
                    placeholder="Dr. Sharma"
                    {...register("doctor_name")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="doctor_reg">Doctor Reg. Number</Label>
                  <Input
                    id="doctor_reg"
                    placeholder="KA/45678/2015"
                    {...register("doctor_reg")}
                  />
                  <p className="text-xs text-muted-foreground">
                    Format: STATE/NUMBER/YEAR (e.g., KA/45678/2015)
                  </p>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="diagnosis">Diagnosis</Label>
                <Input
                  id="diagnosis"
                  placeholder="Viral fever"
                  {...register("diagnosis")}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="medicines">Medicines Prescribed</Label>
                <Input
                  id="medicines"
                  placeholder="Paracetamol 650mg, Vitamin C (comma-separated)"
                  {...register("medicines")}
                />
                <p className="text-xs text-muted-foreground">
                  Separate multiple medicines with commas
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="treatment">Treatment / Therapy</Label>
                <Input
                  id="treatment"
                  placeholder="Panchakarma therapy"
                  {...register("treatment")}
                />
              </div>
              {/* Procedures */}
              <div className="space-y-2">
                <Label>Procedures</Label>
                <div className="flex gap-2">
                  <Input
                    value={newProcedure}
                    onChange={(e) => setNewProcedure(e.target.value)}
                    placeholder="Root canal treatment"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addProcedure();
                      }
                    }}
                  />
                  <Button type="button" variant="outline" size="icon" onClick={addProcedure}>
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                {procedures.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {procedures.map((proc, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between rounded-md bg-muted px-3 py-1.5 text-sm"
                      >
                        <span>{proc}</span>
                        <button
                          type="button"
                          onClick={() => removeProcedure(i)}
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Bill Details */}
          <Card>
            <CardHeader>
              <CardTitle>Bill Details</CardTitle>
              <CardDescription>
                Enter the itemized amounts from the bill
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="consultation_fee">Consultation Fee (₹)</Label>
                  <Input
                    id="consultation_fee"
                    type="number"
                    placeholder="1000"
                    min="0"
                    {...register("consultation_fee")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="diagnostic_tests">Diagnostic Tests (₹)</Label>
                  <Input
                    id="diagnostic_tests"
                    type="number"
                    placeholder="500"
                    min="0"
                    {...register("diagnostic_tests")}
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="medicines_cost">Medicines (₹)</Label>
                  <Input
                    id="medicines_cost"
                    type="number"
                    placeholder="2000"
                    min="0"
                    {...register("medicines_cost")}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="therapy_charges">Therapy Charges (₹)</Label>
                  <Input
                    id="therapy_charges"
                    type="number"
                    placeholder="3000"
                    min="0"
                    {...register("therapy_charges")}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing Claim...
              </>
            ) : (
              "Submit Claim"
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
