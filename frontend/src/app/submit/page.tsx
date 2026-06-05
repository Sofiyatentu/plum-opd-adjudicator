"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Loader2,
  CheckCircle,
  Upload,
  FileText,
  Image,
  X,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { submitClaimWithFiles, submitClaim } from "@/lib/api";

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
});

type ClaimFormData = z.infer<typeof claimSchema>;

interface UploadedFile {
  file: File;
  type: "prescription" | "bill";
  preview: string | null;
}

export default function SubmitClaimPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedClaimId, setSubmittedClaimId] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [dragActive, setDragActive] = useState<"prescription" | "bill" | null>(
    null
  );
  const prescriptionInputRef = useRef<HTMLInputElement>(null);
  const billInputRef = useRef<HTMLInputElement>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ClaimFormData>({
    resolver: zodResolver(claimSchema),
    defaultValues: {
      cashless_request: false,
    },
  });

  const handleFileSelect = useCallback(
    (files: FileList | null, type: "prescription" | "bill") => {
      if (!files || files.length === 0) return;
      const file = files[0];

      // Validate file type
      const validTypes = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
      ];
      if (!validTypes.includes(file.type)) {
        toast.error("Please upload an image (JPG, PNG, WebP) or PDF file");
        return;
      }

      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        toast.error("File size must be less than 10MB");
        return;
      }

      // Generate preview for images
      let preview: string | null = null;
      if (file.type.startsWith("image/")) {
        preview = URL.createObjectURL(file);
      }

      // Replace existing file of the same type
      setUploadedFiles((prev) => {
        const filtered = prev.filter((f) => f.type !== type);
        return [...filtered, { file, type, preview }];
      });

      toast.success(
        `${type === "prescription" ? "Prescription" : "Bill"} document uploaded`
      );
    },
    []
  );

  const removeFile = (type: "prescription" | "bill") => {
    setUploadedFiles((prev) => {
      const removed = prev.find((f) => f.type === type);
      if (removed?.preview) URL.revokeObjectURL(removed.preview);
      return prev.filter((f) => f.type !== type);
    });
  };

  const handleDrag = (
    e: React.DragEvent,
    type: "prescription" | "bill",
    active: boolean
  ) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(active ? type : null);
  };

  const handleDrop = (e: React.DragEvent, type: "prescription" | "bill") => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(null);
    handleFileSelect(e.dataTransfer.files, type);
  };

  const onSubmit = async (data: ClaimFormData) => {
    if (uploadedFiles.length === 0) {
      toast.error(
        "Please upload at least one document (prescription or bill)"
      );
      return;
    }

    setIsSubmitting(true);
    try {
      // Build FormData for file upload
      const formData = new FormData();
      formData.append("member_id", data.member_id);
      formData.append("member_name", data.member_name);
      formData.append("treatment_date", data.treatment_date);
      formData.append("claim_amount", data.claim_amount);
      formData.append("hospital", data.hospital_name || "");
      formData.append(
        "cashless_request",
        String(data.cashless_request || false)
      );

      // Attach files
      const prescriptionFile = uploadedFiles.find(
        (f) => f.type === "prescription"
      );
      const billFile = uploadedFiles.find((f) => f.type === "bill");

      if (prescriptionFile) {
        formData.append("prescription_file", prescriptionFile.file);
      }
      if (billFile) {
        formData.append("bill_file", billFile.file);
      }

      const result = await submitClaimWithFiles(formData);
      setSubmittedClaimId(result.claim_id);
      toast.success("Claim submitted and processed successfully!");
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
              Your documents have been processed with AI and the claim is being
              adjudicated. Claim ID:{" "}
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

  const prescriptionFile = uploadedFiles.find(
    (f) => f.type === "prescription"
  );
  const billFile = uploadedFiles.find((f) => f.type === "bill");

  return (
    <div className="container mx-auto px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tight">Submit a Claim</h1>
        <p className="mt-2 text-muted-foreground">
          Upload your medical documents and fill in the claim details. Our AI
          will extract and process the information automatically.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-8">
          {/* Document Upload Section */}
          <Card className="border-2 border-dashed border-primary/30 bg-primary/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Upload Medical Documents
              </CardTitle>
              <CardDescription>
                Upload prescription and bill images or PDFs. AI (GPT-4o Vision)
                will automatically extract the relevant information.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Prescription Upload */}
              <div>
                <Label className="text-sm font-semibold">
                  Prescription Document
                </Label>
                <p className="text-xs text-muted-foreground mb-2">
                  Upload a photo or scan of the doctor&apos;s prescription
                </p>
                {!prescriptionFile ? (
                  <div
                    className={`relative cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-all hover:border-primary hover:bg-primary/5 ${
                      dragActive === "prescription"
                        ? "border-primary bg-primary/10"
                        : "border-muted-foreground/30"
                    }`}
                    onClick={() => prescriptionInputRef.current?.click()}
                    onDragEnter={(e) => handleDrag(e, "prescription", true)}
                    onDragLeave={(e) => handleDrag(e, "prescription", false)}
                    onDragOver={(e) => handleDrag(e, "prescription", true)}
                    onDrop={(e) => handleDrop(e, "prescription")}
                  >
                    <Upload className="mx-auto h-10 w-10 text-muted-foreground" />
                    <p className="mt-2 text-sm font-medium">
                      Click to upload or drag and drop
                    </p>
                    <p className="text-xs text-muted-foreground">
                      JPG, PNG, WebP or PDF (max 10MB)
                    </p>
                    <input
                      ref={prescriptionInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp,application/pdf"
                      className="hidden"
                      onChange={(e) =>
                        handleFileSelect(e.target.files, "prescription")
                      }
                    />
                  </div>
                ) : (
                  <div className="relative rounded-lg border bg-card p-4">
                    <button
                      type="button"
                      onClick={() => removeFile("prescription")}
                      className="absolute top-2 right-2 rounded-full bg-destructive/10 p-1 text-destructive hover:bg-destructive/20"
                    >
                      <X className="h-4 w-4" />
                    </button>
                    <div className="flex items-center gap-4">
                      {prescriptionFile.preview ? (
                        <img
                          src={prescriptionFile.preview}
                          alt="Prescription preview"
                          className="h-20 w-20 rounded-md object-cover border"
                        />
                      ) : (
                        <div className="flex h-20 w-20 items-center justify-center rounded-md bg-muted">
                          <FileText className="h-8 w-8 text-muted-foreground" />
                        </div>
                      )}
                      <div>
                        <p className="font-medium text-sm">
                          {prescriptionFile.file.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {(prescriptionFile.file.size / 1024).toFixed(1)} KB •{" "}
                          {prescriptionFile.file.type.split("/")[1].toUpperCase()}
                        </p>
                        <p className="text-xs text-success mt-1 flex items-center gap-1">
                          <CheckCircle className="h-3 w-3" /> Ready for AI
                          processing
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Bill Upload */}
              <div>
                <Label className="text-sm font-semibold">Bill / Invoice</Label>
                <p className="text-xs text-muted-foreground mb-2">
                  Upload a photo or scan of the medical bill
                </p>
                {!billFile ? (
                  <div
                    className={`relative cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-all hover:border-primary hover:bg-primary/5 ${
                      dragActive === "bill"
                        ? "border-primary bg-primary/10"
                        : "border-muted-foreground/30"
                    }`}
                    onClick={() => billInputRef.current?.click()}
                    onDragEnter={(e) => handleDrag(e, "bill", true)}
                    onDragLeave={(e) => handleDrag(e, "bill", false)}
                    onDragOver={(e) => handleDrag(e, "bill", true)}
                    onDrop={(e) => handleDrop(e, "bill")}
                  >
                    <Upload className="mx-auto h-10 w-10 text-muted-foreground" />
                    <p className="mt-2 text-sm font-medium">
                      Click to upload or drag and drop
                    </p>
                    <p className="text-xs text-muted-foreground">
                      JPG, PNG, WebP or PDF (max 10MB)
                    </p>
                    <input
                      ref={billInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp,application/pdf"
                      className="hidden"
                      onChange={(e) =>
                        handleFileSelect(e.target.files, "bill")
                      }
                    />
                  </div>
                ) : (
                  <div className="relative rounded-lg border bg-card p-4">
                    <button
                      type="button"
                      onClick={() => removeFile("bill")}
                      className="absolute top-2 right-2 rounded-full bg-destructive/10 p-1 text-destructive hover:bg-destructive/20"
                    >
                      <X className="h-4 w-4" />
                    </button>
                    <div className="flex items-center gap-4">
                      {billFile.preview ? (
                        <img
                          src={billFile.preview}
                          alt="Bill preview"
                          className="h-20 w-20 rounded-md object-cover border"
                        />
                      ) : (
                        <div className="flex h-20 w-20 items-center justify-center rounded-md bg-muted">
                          <FileText className="h-8 w-8 text-muted-foreground" />
                        </div>
                      )}
                      <div>
                        <p className="font-medium text-sm">
                          {billFile.file.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {(billFile.file.size / 1024).toFixed(1)} KB •{" "}
                          {billFile.file.type.split("/")[1].toUpperCase()}
                        </p>
                        <p className="text-xs text-success mt-1 flex items-center gap-1">
                          <CheckCircle className="h-3 w-3" /> Ready for AI
                          processing
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

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
                  <Label
                    htmlFor="cashless_request"
                    className="text-sm cursor-pointer"
                  >
                    Request cashless treatment
                  </Label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Processing Note */}
          <div className="rounded-lg bg-muted/50 p-4 text-sm text-muted-foreground">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-primary mt-0.5 shrink-0" />
              <div>
                <p className="font-medium text-foreground">
                  AI-Powered Processing
                </p>
                <p className="mt-1">
                  Your uploaded documents will be analyzed by GPT-4o Vision to
                  extract doctor details, diagnosis, medicines, and bill amounts.
                  The extracted data is then run through our 6-step adjudication
                  engine for an instant decision.
                </p>
              </div>
            </div>
          </div>

          <Button
            type="submit"
            size="lg"
            className="w-full"
            disabled={isSubmitting || uploadedFiles.length === 0}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing Documents with AI...
              </>
            ) : uploadedFiles.length === 0 ? (
              "Upload Documents to Submit"
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Submit Claim & Process with AI
              </>
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
