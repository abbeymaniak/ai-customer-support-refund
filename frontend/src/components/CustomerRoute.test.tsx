import { describe, it, expect, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { CustomerRoute } from './CustomerRoute';
import * as CustomerAuthContextModule from '../context/CustomerAuthContext';

describe('CustomerRoute Component', () => {
  it('renders loading spinner while customer session is resolving', () => {
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: null,
      isLoading: true,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/portal']}>
        <CustomerRoute>
          <div>Protected Customer Portal</div>
        </CustomerRoute>
      </MemoryRouter>
    );

    expect(markup).toContain('Verifying customer session...');
    expect(markup).not.toContain('Protected Customer Portal');
  });

  it('redirects to /login when customer is unauthenticated', () => {
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/portal']}>
        <Routes>
          <Route
            path="/portal"
            element={
              <CustomerRoute>
                <div>Protected Customer Portal</div>
              </CustomerRoute>
            }
          />
          <Route path="/login" element={<div>Customer Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(markup).toBe('');
    expect(markup).not.toContain('Protected Customer Portal');
  });

  it('renders child content when customer is authenticated', () => {
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: {
        id: 'cust-uuid-1',
        email: 'sarah.jenkins@example.com',
        name: 'Sarah Jenkins',
        role: 'customer',
        risk_score: 5,
        orders_count: 18,
        refunds_count: 0,
        return_rate: 0,
        total_spent: 3240.5,
        is_active: true,
        created_at: '2026-09-24T12:00:00Z',
      },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/portal']}>
        <CustomerRoute>
          <div>Protected Customer Portal</div>
        </CustomerRoute>
      </MemoryRouter>
    );

    expect(markup).toContain('Protected Customer Portal');
  });
});
