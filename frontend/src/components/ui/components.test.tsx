import { describe, it, expect } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { cn } from "../../lib/utils";
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Input,
  FormField,
  Badge,
  Dialog,
  Alert,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "./index";

describe("UI Foundation Primitives", () => {
  describe("cn() utility", () => {
    it("merges multiple class strings safely (covers: AC-2)", () => {
      const result = cn("px-4 py-2", "text-sm", "font-medium");
      expect(result).toBe("px-4 py-2 text-sm font-medium");
    });

    it("resolves Tailwind utility conflicts (covers: AC-2)", () => {
      const result = cn("p-2 text-red-500", "p-4 text-blue-500");
      expect(result).toBe("p-4 text-blue-500");
    });

    it("handles conditional and falsy expressions (covers: AC-2)", () => {
      const isActive = false;
      const isPending = true;
      const result = cn("base-class", isActive && "active", isPending && "pending", null, undefined);
      expect(result).toBe("base-class pending");
    });

    it("handles empty inputs, arrays, and object notation (covers: AC-2)", () => {
      const isHidden = false;
      expect(cn()).toBe("");
      expect(cn(["btn", isHidden && "hidden", ["btn-primary"]])).toBe("btn btn-primary");
      expect(cn({ "font-bold": true, "font-normal": false })).toBe("font-bold");
    });
  });

  describe("Button component", () => {
    it("renders primary button variant by default (covers: AC-3)", () => {
      const html = renderToStaticMarkup(<Button>Submit Claim</Button>);
      expect(html).toContain("bg-zinc-900");
      expect(html).toContain("text-white");
      expect(html).toContain("Submit Claim");
      expect(html).toContain('type="button"');
    });

    it("renders outline, danger, and secondary variants (covers: AC-3)", () => {
      const outlineHtml = renderToStaticMarkup(<Button variant="outline">Cancel</Button>);
      expect(outlineHtml).toContain("bg-white");
      expect(outlineHtml).toContain("border-zinc-200");

      const dangerHtml = renderToStaticMarkup(<Button variant="danger">Deny Request</Button>);
      expect(dangerHtml).toContain("bg-rose-600");

      const secondaryHtml = renderToStaticMarkup(<Button variant="secondary">Back</Button>);
      expect(secondaryHtml).toContain("bg-zinc-100");
    });

    it("renders ghost variant and size variations (covers: AC-3)", () => {
      const ghostHtml = renderToStaticMarkup(<Button variant="ghost">Dismiss</Button>);
      expect(ghostHtml).toContain("hover:bg-zinc-100");
      expect(ghostHtml).toContain("text-zinc-700");

      const smHtml = renderToStaticMarkup(<Button size="sm">Small</Button>);
      expect(smHtml).toContain("text-xs");
      expect(smHtml).toContain("px-2.5");

      const lgHtml = renderToStaticMarkup(<Button size="lg">Large</Button>);
      expect(lgHtml).toContain("text-base");
      expect(lgHtml).toContain("px-4");
    });

    it("handles loading state with spinner and disables button (covers: AC-3)", () => {
      const html = renderToStaticMarkup(<Button isLoading>Processing</Button>);
      expect(html).toContain("disabled");
      expect(html).toContain('aria-busy="true"');
      expect(html).toContain("animate-spin");
    });

    it("respects native disabled attribute and applies disabled styles (covers: AC-3)", () => {
      const html = renderToStaticMarkup(<Button disabled>Unavailable</Button>);
      expect(html).toContain("disabled");
      expect(html).toContain("opacity-50");
      expect(html).toContain("pointer-events-none");
    });
  });

  describe("Card component family", () => {
    it("renders structured card layout with header, content, and footer (covers: AC-3)", () => {
      const html = renderToStaticMarkup(
        <Card>
          <CardHeader>
            <CardTitle>Refund Evaluation</CardTitle>
            <CardDescription>Automated policy check results</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Evaluation details here.</p>
          </CardContent>
          <CardFooter>
            <Button size="sm">Acknowledge</Button>
          </CardFooter>
        </Card>,
      );

      expect(html).toContain("border-zinc-200");
      expect(html).toContain("Refund Evaluation");
      expect(html).toContain("Automated policy check results");
      expect(html).toContain("Evaluation details here.");
    });

    it("merges custom className on card elements safely (covers: AC-3)", () => {
      const html = renderToStaticMarkup(
        <Card className="custom-shadow">
          <CardContent className="p-10">Body</CardContent>
        </Card>,
      );
      expect(html).toContain("custom-shadow");
      expect(html).toContain("p-10");
    });
  });

  describe("Input and FormField components", () => {
    it("renders standalone Input with high contrast borders and focus rings (covers: AC-3, AC-6)", () => {
      const html = renderToStaticMarkup(<Input placeholder="Enter order ID" />);
      expect(html).toContain('type="text"');
      expect(html).toContain("placeholder=\"Enter order ID\"");
      expect(html).toContain("border-zinc-300");
    });

    it("renders Input with explicit hasError styling (covers: AC-6)", () => {
      const html = renderToStaticMarkup(<Input hasError placeholder="Invalid input" />);
      expect(html).toContain("border-rose-300");
      expect(html).toContain("focus-visible:ring-rose-500");
      expect(html).toContain('aria-invalid="true"');
    });

    it("wires accessible label and error state in FormField (covers: AC-6)", () => {
      const html = renderToStaticMarkup(
        <FormField id="email-field" label="Customer Email" error="Email is required" required>
          <Input />
        </FormField>,
      );

      expect(html).toContain('for="email-field"');
      expect(html).toContain("Customer Email");
      expect(html).toContain("*");
      expect(html).toContain('id="email-field"');
      expect(html).toContain('aria-describedby="email-field-error"');
      expect(html).toContain('aria-invalid="true"');
      expect(html).toContain('role="alert"');
      expect(html).toContain("Email is required");
    });

    it("displays helper text when no error is present (covers: AC-6)", () => {
      const html = renderToStaticMarkup(
        <FormField id="order-field" label="Order ID" helperText="Located in your confirmation receipt">
          <Input />
        </FormField>,
      );

      expect(html).toContain('aria-describedby="order-field-helper"');
      expect(html).toContain("Located in your confirmation receipt");
      expect(html).not.toContain('role="alert"');
    });

    it("links both error and helper text in aria-describedby when both are present (covers: AC-6)", () => {
      const html = renderToStaticMarkup(
        <FormField
          id="amount-field"
          label="Refund Amount"
          helperText="Maximum allowed is $500"
          error="Amount must be positive"
        >
          <Input />
        </FormField>,
      );

      expect(html).toContain('aria-describedby="amount-field-error amount-field-helper"');
      expect(html).toContain('aria-invalid="true"');
      expect(html).toContain("Amount must be positive");
    });
  });

  describe("Badge component", () => {
    it("renders semantic status badges with distinct colors (covers: AC-3, AC-5)", () => {
      const approved = renderToStaticMarkup(<Badge status="approved">Approved</Badge>);
      expect(approved).toContain("bg-emerald-50");
      expect(approved).toContain("text-emerald-800");

      const denied = renderToStaticMarkup(<Badge status="denied">Denied</Badge>);
      expect(denied).toContain("bg-rose-50");
      expect(denied).toContain("text-rose-800");

      const escalated = renderToStaticMarkup(<Badge status="escalated">Escalated</Badge>);
      expect(escalated).toContain("bg-amber-50");
      expect(escalated).toContain("text-amber-800");

      const manualReview = renderToStaticMarkup(<Badge status="manual_review">Manual Review</Badge>);
      expect(manualReview).toContain("bg-violet-50");
      expect(manualReview).toContain("text-violet-800");
    });

    it("renders neutral badge and format underscored status text (covers: AC-5)", () => {
      const html = renderToStaticMarkup(<Badge status="pending" />);
      expect(html).toContain("bg-zinc-100");
      expect(html).toContain("pending");
    });

    it("merges custom className and preserves semantic border styling (covers: AC-2, AC-5)", () => {
      const html = renderToStaticMarkup(<Badge status="approved" className="shadow-xs" />);
      expect(html).toContain("shadow-xs");
      expect(html).toContain("border");
    });
  });

  describe("Dialog component", () => {
    it("renders native HTML5 dialog element with title and close action (covers: AC-3, AC-4)", () => {
      const html = renderToStaticMarkup(
        <Dialog isOpen={true} onClose={() => {}} title="Manual Override Review" description="Provide reason for policy exception">
          <div>Dialog content</div>
        </Dialog>,
      );

      expect(html).toContain("<dialog");
      expect(html).toContain("Manual Override Review");
      expect(html).toContain("Provide reason for policy exception");
      expect(html).toContain('aria-label="Close dialog"');
      expect(html).toContain("Dialog content");
    });

    it("renders dialog with custom className (covers: AC-3, AC-4)", () => {
      const html = renderToStaticMarkup(
        <Dialog isOpen={true} onClose={() => {}} className="max-w-xl">
          <div>Custom Width Content</div>
        </Dialog>,
      );
      expect(html).toContain("<dialog");
      expect(html).toContain("max-w-xl");
    });
  });

  describe("Alert component", () => {
    it("renders warning, error, and success alert banners (covers: AC-3)", () => {
      const warningHtml = renderToStaticMarkup(
        <Alert variant="warning" title="Policy Escalation">
          This order exceeds the $500 threshold and requires lead review.
        </Alert>,
      );
      expect(warningHtml).toContain('role="alert"');
      expect(warningHtml).toContain("bg-amber-50");
      expect(warningHtml).toContain("Policy Escalation");

      const errorHtml = renderToStaticMarkup(
        <Alert variant="error" title="Ineligible Item">
          Final sale items are excluded from returns.
        </Alert>,
      );
      expect(errorHtml).toContain("bg-rose-50");
      expect(errorHtml).toContain("Final sale items are excluded from returns.");
    });

    it("renders info and success alerts with semantic container tokens (covers: AC-1, AC-3)", () => {
      const infoHtml = renderToStaticMarkup(<Alert variant="info">System operational</Alert>);
      expect(infoHtml).toContain("bg-zinc-50");
      expect(infoHtml).toContain("System operational");

      const successHtml = renderToStaticMarkup(<Alert variant="success" title="Success">Refund paid</Alert>);
      expect(successHtml).toContain("bg-emerald-50");
      expect(successHtml).toContain("Refund paid");
    });

    it("renders dismiss action button when onClose is provided (covers: AC-3)", () => {
      const html = renderToStaticMarkup(
        <Alert variant="info" title="System Notice" onClose={() => {}}>
          Database maintenance scheduled.
        </Alert>,
      );
      expect(html).toContain('aria-label="Dismiss alert"');
    });
  });

  describe("Table component", () => {
    it("renders accessible tabular structure with headers and rows (covers: AC-3)", () => {
      const html = renderToStaticMarkup(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Order #</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell className="font-mono">ORD-2026-9001</TableCell>
              <TableCell>Sarah Jenkins</TableCell>
              <TableCell className="font-mono">$85.00</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      expect(html).toContain("<table");
      expect(html).toContain("<thead");
      expect(html).toContain("<tbody");
      expect(html).toContain("<th");
      expect(html).toContain("<td");
      expect(html).toContain("ORD-2026-9001");
      expect(html).toContain("font-mono");
    });

    it("wraps table in responsive overflow container (covers: AC-3)", () => {
      const html = renderToStaticMarkup(
        <Table className="min-w-full">
          <TableBody>
            <TableRow>
              <TableCell>Data</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );
      expect(html).toContain("overflow-auto");
      expect(html).toContain("w-full");
    });
  });
});
