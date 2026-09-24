import { describe, it, expect, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { Navbar } from './Navbar';
import * as AuthContextModule from '../context/AuthContext';

describe('Navbar Component', () => {
  it('renders brand logo, title, and staff login button when unauthenticated', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: null,
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
    expect(markup).toContain('Customer Portal');
    expect(markup).toContain('Admin Dashboard');
    expect(markup).toContain('Staff Login');
  });

  it('renders AI Settings navigation link pointing to admin settings for admin user', () => {
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

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/']}>
        <Navbar />
      </MemoryRouter>
    );

    expect(markup).toContain('AI Settings');
    expect(markup).toContain('href="/admin/settings"');
    expect(markup).toContain('Store Administrator');
    expect(markup).toContain('admin');
  });

  it('highlights AI Settings link when active route is admin settings', () => {
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

    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/admin/settings']}>
        <Navbar />
      </MemoryRouter>
    );

    expect(markup).toContain('bg-indigo-50 text-indigo-700 font-semibold');
  });
});
