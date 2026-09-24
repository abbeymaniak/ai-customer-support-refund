import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RequestDetailPage } from './RequestDetail';

describe('RequestDetailPage Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const renderWithDetail = (claimId: string, claimData: any) => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    queryClient.setQueryData(['refund-detail', claimId], claimData);

    return renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[`/admin/refunds/${claimId}`]}>
          <Routes>
            <Route path="/admin/refunds/:id" element={<RequestDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  const sampleClaim = {
    id: '21111111-1111-1111-1111-111111111101',
    request_number: 'REF-2026-0001',
    customer_id: 'c1111111-1111-1111-1111-111111111111',
    order_id: '01111111-1111-1111-1111-111111111101',
    amount: 45.0,
    currency: 'USD',
    reason_category: 'defective',
    customer_explanation: 'Scroll wheel failed completely.',
    decision: 'Approved' as const,
    status: 'approved',
    confidence_score: 0.95,
    decision_reason: 'Approved: Customer is low risk and order is well within the 30-day window.',
    policy_checks: {
      matched_rules: ['RULE_RETURN_WINDOW', 'RULE_DEFECTIVE_REPLACEMENT'],
      triggered_red_flags: [],
      citations: ['Refund Policy § 1.1'],
    },
    human_override: true,
    override_reason: 'Supervisor courtesy grant.',
    override_by: 'lead@store.com',
    created_at: '2026-09-23T00:00:00',
    updated_at: '2026-09-23T00:00:00',
    customer: {
      id: 'c1111111-1111-1111-1111-111111111111',
      name: 'Sarah Jenkins',
      email: 'sarah.jenkins@example.com',
      risk_score: 0.05,
      return_rate: 0.0,
      total_spent: 3240.5,
      orders_count: 18,
      refunds_count: 0,
      account_created_at: '2025-01-01',
      created_at: '2025-01-01',
      updated_at: '2025-01-01',
    },
    order: {
      id: '01111111-1111-1111-1111-111111111101',
      customer_id: 'c1111111-1111-1111-1111-111111111111',
      order_number: 'ORD-2026-9001',
      order_date: '2026-09-10T00:00:00',
      delivery_date: '2026-09-12T00:00:00',
      total_amount: 85.0,
      currency: 'USD',
      status: 'delivered',
      items: [
        {
          id: 'item-101',
          name: 'Wireless Ergonomic Mouse',
          category: 'electronics',
          price: 45.0,
          quantity: 1,
          is_final_sale: false,
        },
      ],
    },
    audit_logs: [
      {
        id: 'log-1',
        refund_request_id: '21111111-1111-1111-1111-111111111101',
        action: 'ai_evaluated',
        actor: 'ai_engine',
        details: { confidence: 0.95 },
        timestamp: '2026-09-23T00:00:05',
      },
      {
        id: 'log-2',
        refund_request_id: '21111111-1111-1111-1111-111111111101',
        action: 'human_override',
        actor: 'lead@store.com',
        details: { reason: 'Supervisor courtesy grant.' },
        timestamp: '2026-09-23T00:05:00',
      },
    ],
  };

  it('renders header, claim reference, decision badge, and back link (covers: AC-3, AC-6)', () => {
    const markup = renderWithDetail('21111111-1111-1111-1111-111111111101', sampleClaim);

    expect(markup).toContain('Back to Console');
    expect(markup).toContain('REF-2026-0001');
    expect(markup).toContain('Approved');
    expect(markup).toContain('Human Overridden');
    expect(markup).toContain('$45.00');
    expect(markup).toContain('Manual Override');
  });

  it('renders customer profile metrics and lifetime values (covers: AC-3)', () => {
    const markup = renderWithDetail('21111111-1111-1111-1111-111111111101', sampleClaim);

    expect(markup).toContain('Customer Profile');
    expect(markup).toContain('Sarah Jenkins');
    expect(markup).toContain('sarah.jenkins@example.com');
    expect(markup).toContain('5%'); // 0.05 * 100
    expect(markup).toContain('$3240.50');
    expect(markup).toContain('18 orders');
  });

  it('renders order context and order items table (covers: AC-3)', () => {
    const markup = renderWithDetail('21111111-1111-1111-1111-111111111101', sampleClaim);

    expect(markup).toContain('ORD-2026-9001');
    expect(markup).toContain('Order Line Items');
    expect(markup).toContain('Wireless Ergonomic Mouse');
    expect(markup).toContain('electronics');
    expect(markup).toContain('Standard');
  });

  it('renders AI reasoning, matched policy rules, and telemetry (covers: AC-3)', () => {
    const markup = renderWithDetail('21111111-1111-1111-1111-111111111101', sampleClaim);

    expect(markup).toContain('AI Reasoning Chain &amp; Guardrails');
    expect(markup).toContain('Approved: Customer is low risk and order is well within the 30-day window.');
    expect(markup).toContain('RULE_RETURN_WINDOW');
    expect(markup).toContain('RULE_DEFECTIVE_REPLACEMENT');
    expect(markup).toContain('Refund Policy § 1.1');
    expect(markup).toContain('AI Telemetry');
    expect(markup).toContain('95.0%');
  });

  it('renders supervisor override explanation banner and audit timeline (covers: AC-4)', () => {
    const markup = renderWithDetail('21111111-1111-1111-1111-111111111101', sampleClaim);

    expect(markup).toContain('Supervisor Override Justification');
    expect(markup).toContain('Supervisor courtesy grant.');
    expect(markup).toContain('Authorized by lead@store.com');
    expect(markup).toContain('Chronological Compliance Audit Trail');
    expect(markup).toContain('ai evaluated');
    expect(markup).toContain('human override');
    expect(markup).toContain('Actor: lead@store.com');
  });
});
