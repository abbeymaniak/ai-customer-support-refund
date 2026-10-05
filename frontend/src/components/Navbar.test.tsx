import { describe, it, expect, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { Navbar } from './Navbar';
import * as AuthContextModule from '../context/AuthContext';
import * as CustomerAuthContextModule from '../context/CustomerAuthContext';

describe('Navbar Component', () => {
  it('shows only guest sign in actions when neither session is authenticated', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/']}>
        <Navbar />
      </MemoryRouter>
    );

    expect(markup).toContain('AutoRefund');
    expect(markup).toContain('Customer Login');
    expect(markup).toContain('Staff Login');
    expect(markup).not.toContain('Customer Portal');
    expect(markup).not.toContain('Admin Dashboard');
    expect(markup).not.toContain('AI Settings');
  });

  it('shows the customer session links and omits staff navigation for a signed in customer', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: {
        id: 'cust-123',
        email: 'sarah.jenkins@example.com',
        name: 'Sarah Jenkins',
        role: 'customer',
        is_active: true,
        created_at: '2026-09-24T12:00:00Z',
        total_spent: 320,
        orders_count: 3,
        refunds_count: 0,
        return_rate: 0.1,
        risk_score: 0.2,
      },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/portal']}>
        <Navbar />
      </MemoryRouter>
    );

    expect(markup).toContain('Customer Portal');
    expect(markup).toContain('My Claims');
    expect(markup).toContain('Sarah Jenkins');
    expect(markup).not.toContain('Admin Dashboard');
    expect(markup).not.toContain('AI Settings');
  });

  it('shows both role sections when staff and customer sessions are active and keeps AI settings for admins only', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 'admin-uuid',
        email: 'admin@store.com',
        name: 'Store Administrator',
        role: 'admin',
        is_active: true,
        created_at: '2026-09-24T12:00:00Z',
      },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: {
        id: 'cust-123',
        email: 'sarah.jenkins@example.com',
        name: 'Sarah Jenkins',
        role: 'customer',
        is_active: true,
        created_at: '2026-09-24T12:00:00Z',
        total_spent: 320,
        orders_count: 3,
        refunds_count: 0,
        return_rate: 0.1,
        risk_score: 0.2,
      },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/portal']}>
        <Navbar />
      </MemoryRouter>
    );

    expect(markup).toContain('Customer Portal');
    expect(markup).toContain('My Claims');
    expect(markup).toContain('Admin Dashboard');
    expect(markup).toContain('AI Settings');
    expect(markup).toContain('Sarah Jenkins');
    expect(markup).toContain('Store Administrator');
  });

  it('differentiates active state between Customer Portal and My Claims on tab navigation', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: {
        id: 'cust-123',
        email: 'sarah.jenkins@example.com',
        name: 'Sarah Jenkins',
        role: 'customer',
        is_active: true,
        created_at: '2026-09-24T12:00:00Z',
        total_spent: 320,
        orders_count: 3,
        refunds_count: 0,
        return_rate: 0.1,
        risk_score: 0.2,
      },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    // 1. On /portal (File a Refund tab): Customer Portal should be active, My Claims should not be active
    const wizardMarkup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/portal']}>
        <Navbar />
      </MemoryRouter>
    );
    expect(wizardMarkup).toMatch(
      /class="[^"]*bg-emerald-50 text-emerald-700 font-semibold[^"]*"[^>]*href="\/portal"/
    );
    expect(wizardMarkup).not.toMatch(
      /class="[^"]*bg-emerald-50 text-emerald-700 font-semibold[^"]*"[^>]*href="\/portal\?tab=claims"/
    );

    // 2. On /portal?tab=claims: My Claims should be active, Customer Portal should not be active
    const claimsMarkup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/portal?tab=claims']}>
        <Navbar />
      </MemoryRouter>
    );
    expect(claimsMarkup).toMatch(
      /class="[^"]*bg-emerald-50 text-emerald-700 font-semibold[^"]*"[^>]*href="\/portal\?tab=claims"/
    );
    expect(claimsMarkup).not.toMatch(
      /class="[^"]*bg-emerald-50 text-emerald-700 font-semibold[^"]*"[^>]*href="\/portal"/
    );
  });

  it('differentiates active state between Admin Dashboard and AI Settings', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 'admin-uuid',
        email: 'admin@store.com',
        name: 'Store Administrator',
        role: 'admin',
        is_active: true,
        created_at: '2026-09-24T12:00:00Z',
      },
      isLoading: false,
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const settingsMarkup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/admin/settings']}>
        <Navbar />
      </MemoryRouter>
    );
    // AI Settings is active
    expect(settingsMarkup).toMatch(
      /class="[^"]*bg-emerald-50 text-emerald-700 font-semibold[^"]*"[^>]*href="\/admin\/settings"/
    );
    // Admin Dashboard is NOT active
    expect(settingsMarkup).not.toMatch(
      /class="[^"]*bg-emerald-50 text-emerald-700 font-semibold[^"]*"[^>]*href="\/admin"/
    );
  });
});
