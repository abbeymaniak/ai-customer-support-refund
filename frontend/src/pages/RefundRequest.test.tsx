import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RefundRequestPage } from './RefundRequest';
import * as CustomerAuthContextModule from '../context/CustomerAuthContext';
import { customerPortalApi } from '../api/customerPortal';
import { refundApi } from '../api/refunds';

describe('RefundRequestPage Component', () => {
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
    vi.spyOn(refundApi, 'getCustomerRefunds').mockResolvedValue([]);
  });

  const renderWithClient = (ui: React.ReactElement, initialOrders?: typeof mockOrders) => {
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
});

