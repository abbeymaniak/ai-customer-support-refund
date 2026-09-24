import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AdminSettingsPage } from './AdminSettings';

describe('AdminSettingsPage Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockProviders = [
    {
      id: 'prov-1',
      llm: 'ollama',
      llm_model: 'llama3',
      is_active: true,
      api_base: 'http://host.docker.internal:11434',
      has_api_key: false,
      api_key_masked: null,
      temperature: 0.1,
      timeout_seconds: 30,
      created_at: '2026-09-23T00:00:00',
      updated_at: '2026-09-23T00:00:00',
    },
    {
      id: 'prov-2',
      llm: 'openai',
      llm_model: 'gpt-4o-mini',
      is_active: false,
      api_base: null,
      has_api_key: true,
      api_key_masked: 'sk-...4321',
      temperature: 0.1,
      timeout_seconds: 30,
      created_at: '2026-09-23T00:00:00',
      updated_at: '2026-09-23T00:00:00',
    },
    {
      id: 'prov-3',
      llm: 'gemini',
      llm_model: 'gemini-1.5-flash',
      is_active: false,
      api_base: null,
      has_api_key: false,
      api_key_masked: null,
      temperature: 0.1,
      timeout_seconds: 30,
      created_at: '2026-09-23T00:00:00',
      updated_at: '2026-09-23T00:00:00',
    },
  ];

  const renderWithProviders = (providers = mockProviders) => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    queryClient.setQueryData(['admin-llm-providers'], providers);

    return renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <AdminSettingsPage />
      </QueryClientProvider>
    );
  };

  it('renders header, title, and admin badge', () => {
    const markup = renderWithProviders();

    expect(markup).toContain('AI Provider Settings');
    expect(markup).toContain('Admin Control');
    expect(markup).toContain('Configure active models, credentials, and endpoint bases');
  });

  it('renders active provider banner with active model details', () => {
    const markup = renderWithProviders();

    expect(markup).toContain('Active Evaluation Provider');
    expect(markup).toContain('ollama');
    expect(markup).toContain('llama3');
    expect(markup).toContain('http://host.docker.internal:11434');
  });

  it('renders provider cards for local ollama, openai, and gemini', () => {
    const markup = renderWithProviders();

    expect(markup).toContain('Local Ollama');
    expect(markup).toContain('OpenAI');
    expect(markup).toContain('Google Gemini');
  });

  it('renders model preset choices and connection probe buttons', () => {
    const markup = renderWithProviders();

    expect(markup).toContain('llama3');
    expect(markup).toContain('qwen2.5');
    expect(markup).toContain('gpt-4o-mini');
    expect(markup).toContain('gemini-1.5-flash');
    expect(markup).toContain('Test Connection');
    expect(markup).toContain('Save Settings');
    expect(markup).toContain('Set as Active Provider');
  });

  it('displays masked api key notice for configured cloud provider', () => {
    const markup = renderWithProviders();

    expect(markup).toContain('Current: sk-...4321');
  });

  it('renders parameter inputs for temperature and timeout thresholds', () => {
    const markup = renderWithProviders();

    expect(markup).toContain('Temperature');
    expect(markup).toContain('Timeout (s)');
    expect(markup).toContain('step="0.05"');
    expect(markup).toContain('step="5"');
  });

  it('renders loading state when provider data is pending', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    // empty client without preloaded data
    const markup = renderToStaticMarkup(
      <QueryClientProvider client={queryClient}>
        <AdminSettingsPage />
      </QueryClientProvider>
    );

    expect(markup).toContain('Loading provider settings...');
  });

  it('accessibility check: inputs and action buttons carry descriptive titles and types', () => {
    const markup = renderWithProviders();

    expect(markup).toContain('type="text"');
    expect(markup).toContain('type="password"');
    expect(markup).toContain('type="number"');
    expect(markup).toContain('Refresh');
    expect(markup).toContain('Test Connection');
    expect(markup).toContain('Save Settings');
  });
});

