import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AdminDashboardPage } from './AdminDashboard';

describe('AdminDashboardPage Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const renderWithClient = (ui: React.ReactElement, initialData?: any) => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    if (initialData?.refunds) {
      queryClient.setQueryData(
        [
          'admin-refunds',
          {
            decision: undefined,
            search: undefined,
            start_date: undefined,
            end_date: undefined,
            sort_by: 'created_at',
            sort_order: 'desc',
            limit: 20,
            offset: 0,
          },
        ],
        initialData.refunds
      );
    }

    if (initialData?.stats) {
      queryClient.setQueryData(['admin-stats'], initialData.stats);
    }

    return renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>{ui}</MemoryRouter>
      </QueryClientProvider>
    );
  };

  it('renders console header and refresh button (covers: AC-5)', () => {
    const markup = renderWithClient(<AdminDashboardPage />);

    expect(markup).toContain('Support Agent Refund Console');
    expect(markup).toContain('Review automated AI refund evaluations');
    expect(markup).toContain('Refresh Data');
  });

  it('renders all 6 operational KPI metric cards (covers: AC-2, AC-5)', () => {
    const mockStats = {
      total_requests: 48,
      approved_count: 36,
      denied_count: 8,
      escalated_count: 4,
      approval_rate: 75.0,
      human_overrides_count: 3,
      total_refunded_amount: 3240.5,
    };

    const markup = renderWithClient(<AdminDashboardPage />, { stats: mockStats });

    expect(markup).toContain('Total Claims');
    expect(markup).toContain('Approval Rate');
    expect(markup).toContain('Approved');
    expect(markup).toContain('Denied');
    expect(markup).toContain('Escalations');
    expect(markup).toContain('Refunded');
    expect(markup).toContain('75%');
    expect(markup).toContain('$3,240.50');
  });

  it('renders search input, date range filters, and status tabs (covers: AC-1, AC-5)', () => {
    const markup = renderWithClient(<AdminDashboardPage />);

    expect(markup).toContain('Search by customer name, email, order, or request number...');
    expect(markup).toContain('All Requests');
    expect(markup).toContain('Approved');
    expect(markup).toContain('Denied');
    expect(markup).toContain('Escalated');
    expect(markup).toContain('type="date"');
    expect(markup).toContain('Page Size:');
  });

  it('renders claims table columns and empty state when no items found (covers: AC-5)', () => {
    const markup = renderWithClient(<AdminDashboardPage />, {
      refunds: { items: [], total: 0, limit: 20, offset: 0 },
    });

    expect(markup).toContain('Claim Reference');
    expect(markup).toContain('Customer &amp; Order');
    expect(markup).toContain('Amount');
    expect(markup).toContain('Risk &amp; Anomalies');
    expect(markup).toContain('AI Verdict');
    expect(markup).toContain('Override');
    expect(markup).toContain('Actions');
    expect(markup).toContain('No refund requests found');
  });

  it('renders populated claims rows with formatted verdict badges, risk scores, and anomaly chips (covers: AC-5, AC-8)', () => {
    const mockRefunds = {
      items: [
        {
          id: '21111111-1111-1111-1111-111111111101',
          request_number: 'REF-2026-0001',
          customer_id: 'c1111111-1111-1111-1111-111111111111',
          customer_name: 'Sarah Jenkins',
          customer_email: 'sarah.jenkins@example.com',
          order_id: '01111111-1111-1111-1111-111111111101',
          order_number: 'ORD-2026-9001',
          item_name: 'Wireless Ergonomic Mouse',
          amount: 45.0,
          currency: 'USD',
          reason_category: 'defective',
          status: 'approved',
          decision: 'Approved' as const,
          confidence_score: 0.95,
          human_override: false,
          risk_score: 0.4,
          anomaly_flags: ['velocity_limit_exceeded'],
          created_at: '2026-09-23T00:00:00',
          updated_at: '2026-09-23T00:00:00',
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    };

    const markup = renderWithClient(<AdminDashboardPage />, { refunds: mockRefunds });

    expect(markup).toContain('REF-2026-0001');
    expect(markup).toContain('Sarah Jenkins');
    expect(markup).toContain('sarah.jenkins@example.com');
    expect(markup).toContain('$45.00');
    expect(markup).toContain('40% Risk');
    expect(markup).toContain('Velocity Spike');
    expect(markup).toContain('Approved');
    expect(markup).toContain('href="/admin/refunds/21111111-1111-1111-1111-111111111101"');
    expect(markup).toContain('Override');
    expect(markup).toContain('Audit');
  });
});
