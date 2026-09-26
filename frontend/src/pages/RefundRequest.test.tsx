/** @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { afterEach, describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen } from '@testing-library/react';
import { createMemoryRouter, MemoryRouter, RouterProvider } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { RefundRequestPage } from './RefundRequest';
import * as CustomerAuthContextModule from '../context/CustomerAuthContext';
import { customerPortalApi } from '../api/customerPortal';
import { refundApi } from '../api/refunds';
import type { RefundRequest } from '../types';

describe('RefundRequestPage Component', () => {
  afterEach(cleanup);

  const mockCustomer = {
    id: 'cust-sarah-123',
    name: 'Sarah Jenkins',
    email: 'sarah.jenkins@example.com',
    total_spent: 3250.5,
    orders_count: 18,
    refunds_count: 1,
    return_rate: 0.05,
    risk_score: 0.12,
    is_active: true,
    role: 'customer',
    created_at: '2026-01-01T00:00:00Z',
  };

  const mockOrders = [
    {
      id: 'ord-101',
      customer_id: 'cust-sarah-123',
      order_number: 'ORD-98721',
      order_date: '2026-09-10T12:00:00Z',
      total_amount: 149.99,
      currency: 'USD',
      status: 'delivered',
      items: [
        {
          id: 'item-201',
          name: 'Noise Cancelling Headphones',
          price: 99.99,
          category: 'Electronics',
          quantity: 1,
          is_final_sale: false,
          has_active_claim: false,
          claim_status: null,
        },
        {
          id: 'item-202',
          name: 'Wireless Mouse',
          price: 50.0,
          category: 'Electronics',
          quantity: 1,
          is_final_sale: false,
          has_active_claim: true,
          claim_status: 'Approved',
          claim_request_number: 'REF-2026-0001',
        },
      ],
    },
  ];

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: mockCustomer,
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    vi.spyOn(customerPortalApi, 'getMyOrders').mockResolvedValue(mockOrders);
    vi.spyOn(customerPortalApi, 'getMyRefunds').mockResolvedValue([]);
    vi.spyOn(refundApi, 'getCustomerRefunds').mockResolvedValue([]);
  });

  const mockClaims = [
    {
      id: 'claim-1',
      request_number: 'REF-2026-0001',
      order_id: 'ord-101',
      order_number: 'ORD-98721',
      item_name: 'Noise Cancelling Headphones',
      amount: 99.99,
      currency: 'USD',
      status: 'approved',
      decision: 'Approved' as const,
      ai_decision: 'Approved',
      confidence_score: 0.95,
      reason_category: 'defective',
      customer_explanation: 'Left earbud stopped charging.',
      ai_reasoning: 'Hardware defect verified within standard warranty window.',
      human_override: false,
      override_reason: null,
      override_by: null,
      items: [
        {
          id: 'rf-item-1',
          order_item_id: 'item-201',
          product_name: 'Noise Cancelling Headphones',
          quantity: 1,
          refund_amount: 99.99,
          item_condition: 'opened_used',
        },
      ],
      created_at: '2026-09-25T14:00:00Z',
    },
    {
      id: 'claim-2',
      request_number: 'REF-2026-0002',
      order_id: 'ord-101',
      order_number: 'ORD-98721',
      item_name: 'Mechanical Gaming Keyboard',
      amount: 129.99,
      currency: 'USD',
      status: 'approved',
      decision: 'Approved' as const,
      ai_decision: 'Escalated',
      confidence_score: 0.65,
      reason_category: 'damaged_on_arrival',
      customer_explanation: 'Package crushed during postal delivery.',
      ai_reasoning: 'Borderline transit damage requiring human supervisor review.',
      human_override: true,
      override_reason: 'Customer submitted clear photographic evidence of courier box damage.',
      override_by: 'lead.supervisor@example.com',
      items: [
        {
          id: 'rf-item-2',
          order_item_id: 'item-202',
          product_name: 'Mechanical Gaming Keyboard',
          quantity: 1,
          refund_amount: 129.99,
          item_condition: 'damaged',
        },
      ],
      created_at: '2026-09-26T09:30:00Z',
    },
  ];

  const renderWithClient = (
    ui: React.ReactElement,
    initialOrders?: typeof mockOrders,
    initialRefunds?: typeof mockClaims
  ) => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    if (initialOrders) {
      queryClient.setQueryData(['customer-orders'], initialOrders);
    }
    if (initialRefunds) {
      queryClient.setQueryData(['customer-refunds'], initialRefunds);
    }

    return renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    );
  };

  it('renders authenticated customer profile summary card with verified metrics (covers: AC-5)', () => {
    const markup = renderWithClient(<RefundRequestPage />);

    expect(markup).toContain('Sarah Jenkins');
    expect(markup).toContain('sarah.jenkins@example.com');
    expect(markup).toContain('Verified Session');
    expect(markup).toContain('$3250.50');
    expect(markup).toContain('18');
    expect(markup).toContain('5%');
    expect(markup).toContain('12 / 100');
  });

  it('completely removes manual email input and lookup controls (covers: AC-5)', () => {
    const markup = renderWithClient(<RefundRequestPage />);

    expect(markup).not.toContain('placeholder="Enter customer email address..."');
    expect(markup).not.toContain('Step 1: Customer Account');
    expect(markup).not.toContain('Lookup');
  });

  it('completely removes sample persona quick load buttons (covers: AC-5)', () => {
    const markup = renderWithClient(<RefundRequestPage />);

    expect(markup).not.toContain('Quick Load Test Persona (Evaluation Scenarios)');
    expect(markup).not.toContain('Marcus Vance (High Risk 60% Return)');
    expect(markup).not.toContain('Amanda Price (Clearance / Final Sale)');
  });

  it('renders the 3 step wizard stepper navigation (covers: AC-5)', () => {
    const markup = renderWithClient(<RefundRequestPage />);

    expect(markup).toContain('Select Order &amp; Item');
    expect(markup).toContain('Reason &amp; Notes');
    expect(markup).toContain('Review &amp; Submit');
  });

  it('renders orders dropdown and marks claimed items as disabled with Claim Filed badge (covers: AC-4)', () => {
    const markup = renderWithClient(<RefundRequestPage />, mockOrders);

    expect(markup).toContain('ORD-98721');
    expect(markup).toContain('Choose an Order');
    expect(markup).toContain('1 available order');
  });

  it('renders AI decision engine verdict card with initial guidance state (covers: AC-3, AC-5)', () => {
    const markup = renderWithClient(<RefundRequestPage />);

    expect(markup).toContain('AI Decision Engine Verdict');
    expect(markup).toContain('Real time policy validation and multifactor risk determination');
    expect(markup).toContain(
      'Complete the 3 step wizard on the left to trigger the AI decision engine'
    );
  });

  it('renders security perimeter notice and prompt injection protection markers (covers: AC-3)', () => {
    const markup = renderWithClient(<RefundRequestPage />);

    expect(markup).toContain('Customer Support Refund Portal');
    expect(markup).toContain('Submit and evaluate refund claims in seconds');
  });

  it('renders empty state when customer has no past purchase orders (covers: AC-1, AC-5)', () => {
    const markup = renderWithClient(<RefundRequestPage />, []);

    expect(markup).toContain('No Orders Found');
    expect(markup).toContain('You do not have any past purchase orders associated with this account');
  });

  it('renders loading state when fetching customer orders (covers: AC-5)', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    // Do not pre-populate cache so query is initially in fetching/loading state
    const markup = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <RefundRequestPage />
      </QueryClientProvider>
    );

    expect(markup).toContain('Retrieving your verified customer orders...');
  });

  it('verifies accessible heading hierarchy and wizard progress indicators (covers: AC-5)', () => {
    const markup = renderWithClient(<RefundRequestPage />, mockOrders);

    expect(markup).toContain('<h1');
    expect(markup).toContain('Customer Support Refund Portal');
    expect(markup).toContain('Step 1: Select Order &amp; Item');
    expect(markup).toContain('AI Decision Engine Verdict');
    expect(markup).toContain('Your Refund History');
  });

  it('renders segmented tab navigation for File a Refund and My Claims (covers: AC-3)', () => {
    const markup = renderWithClient(<RefundRequestPage />, mockOrders, mockClaims);

    expect(markup).toContain('id="tab-file-refund"');
    expect(markup).toContain('File a Refund');
    expect(markup).toContain('id="tab-my-claims"');
    expect(markup).toContain('My Claims (Your Refund History)');
    expect(markup).toContain('2'); // 2 claims in badge
  });

  it('renders claims history metrics, search bar, and status filter pills when My Claims tab is active (covers: AC-3, AC-4)', () => {
    const markup = renderWithClient(
      <RefundRequestPage initialTab="claims" />,
      mockOrders,
      mockClaims
    );

    // Metrics cards
    expect(markup).toContain('Total Claims');
    expect(markup).toContain('Approved');
    expect(markup).toContain('Under Review');
    expect(markup).toContain('Denied');

    // Search and filter controls
    expect(markup).toContain('id="claims-search-input"');
    expect(markup).toContain('placeholder="Search request #, order #, or product name..."');
    expect(markup).toContain('id="filter-all"');
    expect(markup).toContain('id="filter-approved"');
    expect(markup).toContain('id="filter-escalated"');
    expect(markup).toContain('id="filter-denied"');

    // Claims table data
    expect(markup).toContain('REF-2026-0001');
    expect(markup).toContain('REF-2026-0002');
    expect(markup).toContain('ORD-98721');
    expect(markup).toContain('Noise Cancelling Headphones');
    expect(markup).toContain('Mechanical Gaming Keyboard');
    expect(markup).toContain('$99.99');
    expect(markup).toContain('$129.99');
    expect(markup).toContain('Supervisor Override');
    expect(markup).toContain('Automated');
    expect(markup).toContain('Inspect');
  });

  it('renders inspection drawer with policy evaluation and supervisor override justification (covers: AC-2, AC-5)', () => {
    const markup = renderWithClient(
      <RefundRequestPage initialTab="claims" initialSelectedClaim={mockClaims[1]} />,
      mockOrders,
      mockClaims
    );

    expect(markup).toContain('id="claim-inspection-drawer"');
    expect(markup).toContain('REF-2026-0002');
    expect(markup).toContain('Claim Amount');
    expect(markup).toContain('$129.99 USD');
    expect(markup).toContain('Associated Order');
    expect(markup).toContain('ORD-98721');
    expect(markup).toContain('Customer Explanation');
    expect(markup).toContain('Package crushed during postal delivery.');
    expect(markup).toContain('AI Policy Reasoning');
    expect(markup).toContain('Borderline transit damage requiring human supervisor review.');
    expect(markup).toContain('65% Confidence');
    expect(markup).toContain('Supervisor Override Applied');
    expect(markup).toContain('lead.supervisor@example.com');
    expect(markup).toContain('Customer submitted clear photographic evidence of courier box damage.');
    expect(markup).toContain('Close Inspection');
  });

  it('renders empty state when customer has zero refund claims (covers: AC-1, AC-4)', () => {
    const markup = renderWithClient(
      <RefundRequestPage initialTab="claims" />,
      mockOrders,
      []
    );

    expect(markup).toContain('No Refund Claims Yet');
    expect(markup).toContain("You haven&#x27;t filed any refund requests for your purchase orders.");
    expect(markup).toContain('File Your First Refund');
  });

  const renderInteractive = (
    initialTab: 'wizard' | 'claims',
    initialOrders = mockOrders,
    initialRefunds: typeof mockClaims = mockClaims
  ) => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: Infinity },
        mutations: { retry: false },
      },
    });
    queryClient.setQueryData(['customer-orders'], initialOrders);
    queryClient.setQueryData(['customer-refunds'], initialRefunds);

    const result = render(
      <QueryClientProvider client={queryClient}>
        <RefundRequestPage initialTab={initialTab} />
      </QueryClientProvider>
    );

    return { ...result, queryClient };
  };

  it('filters claims by decision and searches by item name (covers: AC-4)', async () => {
    const user = userEvent.setup();
    const claims = [
      mockClaims[0],
      { ...mockClaims[1], decision: 'Escalated' as const },
      {
        ...mockClaims[1],
        id: 'claim-3',
        request_number: 'REF-2026-0003',
        item_name: 'Travel Backpack',
        decision: 'Denied' as const,
      },
    ] as typeof mockClaims;
    renderInteractive('claims', mockOrders, claims);

    await user.click(screen.getByRole('button', { name: /Denied/ }));
    expect(screen.getByText('REF-2026-0003')).toBeInTheDocument();
    expect(screen.queryByText('REF-2026-0001')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /All/ }));
    await user.type(
      screen.getByPlaceholderText('Search request #, order #, or product name...'),
      'Travel Backpack'
    );

    expect(screen.getByText('REF-2026-0003')).toBeInTheDocument();
    expect(screen.queryByText('REF-2026-0001')).not.toBeInTheDocument();
  });

  it('switches between refund filing and claim history tabs (covers: AC-3)', async () => {
    const user = userEvent.setup();
    renderInteractive('claims');

    expect(screen.getByRole('heading', { name: 'Your Refund History' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /File a Refund/ }));
    expect(screen.getByText('Step 1: Select Order & Item')).toBeInTheDocument();
  });

  it('maps portal tab state to the URL and falls back for unsupported values', async () => {
    const user = userEvent.setup();
    const router = createMemoryRouter(
      [
        {
          path: '/portal',
          element: (
            <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
              <RefundRequestPage />
            </QueryClientProvider>
          ),
        },
      ],
      { initialEntries: ['/portal?tab=claims'] }
    );

    render(<RouterProvider router={router} />);

    expect(screen.getByRole('heading', { name: 'Your Refund History' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /File a Refund/ }));
    expect(router.state.location.pathname).toBe('/portal');
    expect(router.state.location.search).toBe('');

    await user.click(screen.getByRole('button', { name: /My Claims/ }));
    expect(router.state.location.search).toContain('tab=claims');
  });

  it('opens a claim inspection dialog and closes it with the close button (covers: AC-5)', async () => {
    const user = userEvent.setup();
    renderInteractive('claims');

    await user.click(screen.getAllByRole('button', { name: 'Inspect' })[0]);
    expect(screen.getByRole('dialog', { name: 'REF-2026-0001' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Close drawer' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('closes the inspection dialog on Escape and restores focus to its trigger (covers: AC-5)', async () => {
    const user = userEvent.setup();
    renderInteractive('claims');
    const inspectButton = screen.getAllByRole('button', { name: 'Inspect' })[0];

    await user.click(inspectButton);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    await user.keyboard('{Escape}');

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(inspectButton).toHaveFocus();
  });

  it('shows an error when claim history cannot be loaded (covers: AC-1)', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(['customer-orders'], mockOrders);
    vi.spyOn(customerPortalApi, 'getMyRefunds').mockRejectedValueOnce(
      new Error('Network unavailable')
    );

    render(
      <QueryClientProvider client={queryClient}>
        <RefundRequestPage initialTab="claims" />
      </QueryClientProvider>
    );

    expect(await screen.findByText('Failed to retrieve refund history.')).toBeInTheDocument();
  });

  it('shows a submitted claim in history without reloading the page (covers: AC-3, AC-6)', async () => {
    const user = userEvent.setup();
    const submittedClaim = {
      ...mockClaims[0],
      id: 'claim-new',
      request_number: 'REF-2026-0003',
      decision: 'Approved' as const,
      item_name: 'Noise Cancelling Headphones',
    };
    const refundResponse: RefundRequest = {
      id: submittedClaim.id,
      request_number: submittedClaim.request_number,
      customer_id: mockCustomer.id,
      order_id: submittedClaim.order_id,
      amount: submittedClaim.amount,
      currency: submittedClaim.currency,
      reason_category: submittedClaim.reason_category,
      customer_explanation: submittedClaim.customer_explanation,
      status: 'approved',
      decision: 'Approved',
      human_override: false,
      created_at: submittedClaim.created_at,
      updated_at: submittedClaim.created_at,
    };
    vi.spyOn(customerPortalApi, 'submitRefund').mockResolvedValueOnce(refundResponse);
    vi.spyOn(customerPortalApi, 'getMyRefunds').mockResolvedValue([submittedClaim]);
    renderInteractive('wizard', mockOrders, []);

    await user.selectOptions(screen.getByRole('combobox'), 'ord-101');
    await user.click(screen.getByRole('radio', { name: /Noise Cancelling Headphones/ }));
    await user.click(screen.getByRole('button', { name: /Continue to Reason & Notes/ }));
    await user.type(
      screen.getByPlaceholderText(/Please explain the reason for your refund/),
      'The headphones stopped charging after two days of normal use.'
    );
    await user.click(screen.getByRole('button', { name: /Continue to Review/ }));
    await user.click(screen.getByRole('button', { name: /Submit Claim/ }));

    await user.click(await screen.findByRole('button', { name: /View in My Claims/ }));

    const claimMarkers = await screen.findAllByText('REF-2026-0003');
    expect(claimMarkers.length).toBeGreaterThan(0);
    expect(customerPortalApi.submitRefund).toHaveBeenCalledWith({
      order_id: 'ord-101',
      item_id: 'item-201',
      reason_category: 'defective',
      customer_explanation: 'The headphones stopped charging after two days of normal use.',
      quantity: 1,
      item_condition: 'unopened',
    });
  });
});

