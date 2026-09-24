import { describe, it, expect, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AdminRoute } from './AdminRoute';
import * as AuthContextModule from '../context/AuthContext';

describe('AdminRoute Component', () => {
  it('renders loading spinner while auth is resolving', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      isLoading: true,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminRoute>
          <div>Protected Content</div>
        </AdminRoute>
      </MemoryRouter>
    );

    expect(markup).toContain('Verifying administrative session...');
    expect(markup).not.toContain('Protected Content');
  });

  it('redirects to /admin/login when user is unauthenticated', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshProfile: vi.fn(),
    });

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <div>Protected Content</div>
              </AdminRoute>
            }
          />
          <Route path="/admin/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    // Navigate renders null in server-side static markup, successfully blocking protected content
    expect(markup).toBe('');
    expect(markup).not.toContain('Protected Content');
  });

  it('renders child content when user is authenticated with proper role', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 'admin-id',
        email: 'admin@store.com',
        name: 'Admin User',
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

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/admin']}>
        <AdminRoute>
          <div>Protected Dashboard Area</div>
        </AdminRoute>
      </MemoryRouter>
    );

    expect(markup).toContain('Protected Dashboard Area');
  });

  it('renders access restricted message when user lacks required role', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: {
        id: 'agent-id',
        email: 'lead@store.com',
        name: 'Lead Agent',
        role: 'agent',
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
      <MemoryRouter initialEntries={['/admin/settings']}>
        <AdminRoute requiredRole="admin">
          <div>Settings Content</div>
        </AdminRoute>
      </MemoryRouter>
    );

    expect(markup).toContain('Access Restricted');
    expect(markup).toContain('lead@store.com');
    expect(markup).not.toContain('Settings Content');
  });
});
