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
});
