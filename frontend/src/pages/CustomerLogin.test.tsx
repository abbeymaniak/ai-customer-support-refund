import { describe, it, expect, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { CustomerLoginPage } from './CustomerLogin';
import * as CustomerAuthContextModule from '../context/CustomerAuthContext';

describe('CustomerLoginPage Component', () => {
  it('renders customer portal login header, inputs, and sample customer profiles', () => {
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/login']}>
        <CustomerLoginPage />
      </MemoryRouter>
    );

    expect(markup).toContain('Customer Portal Login');
    expect(markup).toContain('Access your personal orders, view claim status, and file returns');
    expect(markup).toContain('Sarah Jenkins');
    expect(markup).toContain('sarah.jenkins@example.com');
    expect(markup).toContain('David Miller');
    expect(markup).toContain('Elena Rostova');
    expect(markup).toContain('Sample Test Profiles (Password: customer123)');
    expect(markup).toContain('Sign In');
  });

  it('renders accessible form inputs associated with labels and required attributes', () => {
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/login']}>
        <CustomerLoginPage />
      </MemoryRouter>
    );

    // Label associations
    expect(markup).toContain('for="customer-email"');
    expect(markup).toContain('id="customer-email"');
    expect(markup).toContain('type="email"');
    expect(markup).toContain('for="customer-password"');
    expect(markup).toContain('id="customer-password"');
    expect(markup).toContain('type="password"');

    // Submit button
    expect(markup).toContain('type="submit"');
  });

  it('renders link to support staff login', () => {
    vi.spyOn(CustomerAuthContextModule, 'useCustomerAuth').mockReturnValue({
      customer: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/login']}>
        <CustomerLoginPage />
      </MemoryRouter>
    );

    expect(markup).toContain('Support Staff Login');
    expect(markup).toContain('/admin/login');
  });
});
