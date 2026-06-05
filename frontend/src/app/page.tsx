import Link from "next/link";
import { ArrowRight, FileCheck, ShieldCheck, Clock, BrainCircuit } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  {
    icon: FileCheck,
    title: "Smart Document Processing",
    description:
      "Upload bills, prescriptions, and reports. Our AI extracts and validates all key fields automatically.",
  },
  {
    icon: ShieldCheck,
    title: "Policy-Aware Adjudication",
    description:
      "Claims are evaluated against Plum OPD Advantage policy terms with full transparency.",
  },
  {
    icon: Clock,
    title: "Fast Decisions",
    description:
      "Get claim decisions in seconds. Manual review is automatically triggered for complex cases.",
  },
  {
    icon: BrainCircuit,
    title: "AI-Powered Intelligence",
    description:
      "GPT-4o Vision understands medical documents, diagnoses, and treatments for accurate adjudication.",
  },
];

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-b from-primary/5 to-transparent py-20">
        <div className="container mx-auto px-4 text-center">
          <div className="mx-auto mb-6 inline-flex items-center rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-sm font-medium text-primary">
            AI Automation Pod
          </div>
          <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            OPD Claim Adjudication,{" "}
            <span className="text-primary">Automated</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
            Submit medical documents and get instant claim decisions powered by
            AI. Built for Plum Insurance&apos;s 1M+ members across India.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link href="/submit">
              <Button size="lg" className="gap-2">
                Submit a Claim <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/claims">
              <Button size="lg" variant="outline">
                View Claims
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-center text-3xl font-bold tracking-tight">
            How It Works
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-muted-foreground">
            A streamlined 4-step process from document upload to claim decision
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => (
              <Card
                key={feature.title}
                className="border-2 transition-shadow hover:shadow-lg"
              >
                <CardHeader>
                  <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-t bg-muted/30 py-16">
        <div className="container mx-auto px-4">
          <div className="grid gap-8 sm:grid-cols-3">
            <div className="text-center">
              <div className="text-4xl font-bold text-primary">₹1L+</div>
              <div className="mt-2 text-sm text-muted-foreground">
                Claims Processed Monthly
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary">&lt;5s</div>
              <div className="mt-2 text-sm text-muted-foreground">
                Average Processing Time
              </div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary">95%</div>
              <div className="mt-2 text-sm text-muted-foreground">
                Automation Rate
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
