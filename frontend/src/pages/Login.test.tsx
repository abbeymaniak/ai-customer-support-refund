import { describe, it, expect, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from './Login';
import * as AuthContextModule from '../context/AuthContext';

describe('LoginPage Component', () => {
  it('renders login header, inputs, and demo quick-fill buttons', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/admin/login']}>
        <LoginPage />
      </MemoryRouter>
    );

    expect(markup).toContain('Admin Authentication');
    expect(markup).toContain('Evaluator Demo Credentials');
    expect(markup).toContain('Login as Admin');
    expect(markup).toContain('Login as Lead');
    expect(markup).toContain('Sign In');
  });

  it('renders frictionless claim filing callout for evaluators', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/admin/login']}>
        <LoginPage />
      </MemoryRouter>
    );

    expect(markup).toContain('Customer claim filing remains frictionless and unauthenticated');
  });

  it('renders accessible form inputs associated with labels and required attributes', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/admin/login']}>
        <LoginPage />
      </MemoryRouter>
    );

    // Label associations
    expect(markup).toContain('for="email"');
    expect(markup).toContain('id="email"');
    expect(markup).toContain('type="email"');
    expect(markup).toContain('for="password"');
    expect(markup).toContain('id="password"');
    expect(markup).toContain('type="password"');

    // Submit button
    expect(markup).toContain('type="submit"');
  });
});
