import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { Navbar } from './Navbar';

describe('Navbar Component', () => {
  it('renders brand logo and title', () => {
    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/']}>
        <Navbar />
      </MemoryRouter>
    );

    expect(markup).toContain('AutoRefund');
    expect(markup).toContain('Customer Portal');
    expect(markup).toContain('Admin Dashboard');
  });

  it('renders AI Settings navigation link pointing to admin settings', () => {
    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/']}>
        <Navbar />
      </MemoryRouter>
    );

    expect(markup).toContain('AI Settings');
    expect(markup).toContain('href="/admin/settings"');
  });

  it('highlights AI Settings link when active route is admin settings', () => {
    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/admin/settings']}>
        <Navbar />
      </MemoryRouter>
    );

    expect(markup).toContain('bg-indigo-50 text-indigo-700 font-semibold');
  });
});
