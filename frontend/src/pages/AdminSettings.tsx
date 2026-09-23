import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Cpu,
  Sparkles,
  Zap,
  CheckCircle2,
  XCircle,
  Eye,
  EyeOff,
  Server,
  RefreshCw,
} from 'lucide-react';
import {
  fetchLLMProviders,
  updateLLMProvider,
  activateLLMProvider,
  testLLMConnection,
} from '../api/settings';
import type { LLMProvider, LLMTestProbeResponse } from '../types';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { Alert } from '../components/ui/Alert';

interface ProviderCardProps {
  provider: LLMProvider;
  onActivate: (providerName: string) => void;
  isActivating: boolean;
}

const PROVIDER_METADATA: Record<
  string,
  {
    title: string;
    description: string;
    icon: React.ElementType;
    badgeColor: 'emerald' | 'indigo' | 'purple';
    defaultModels: string[];
  }
> = {
  ollama: {
    title: 'Local Ollama',
    description: 'On-premises open weight models with local privacy and zero API token costs.',
    icon: Server,
    badgeColor: 'emerald',
    defaultModels: ['llama3', 'qwen2.5', 'phi', 'mistral'],
  },
  openai: {
    title: 'OpenAI',
    description:
      'Commercial cloud models for high accuracy reasoning and strict JSON schema output.',
    icon: Sparkles,
    badgeColor: 'indigo',
    defaultModels: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
  },
  gemini: {
    title: 'Google Gemini',
    description:
      'Fast, multimodal cloud model family with generous context windows and low latency.',
    icon: Zap,
    badgeColor: 'purple',
    defaultModels: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash'],
  },
};

export const AdminSettingsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load providers from backend
  const {
    data: providers = [],
    isLoading,
    isError,
    refetch,
  } = useQuery<LLMProvider[]>({
    queryKey: ['admin-llm-providers'],
    queryFn: fetchLLMProviders,
  });

  const activateMutation = useMutation({
    mutationFn: (providerName: string) => activateLLMProvider(providerName),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['admin-llm-providers'] });
      setSuccessMessage(`Activated ${updated.llm.toUpperCase()} as primary evaluation provider.`);
      setErrorMessage(null);
    },
    onError: (err: Error) => {
      setErrorMessage(err.message || 'Failed to activate provider.');
      setSuccessMessage(null);
    },
  });

  const activeProvider = providers.find((p) => p.is_active);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              AI Provider Settings
            </h1>
            <Badge status="manual_review" size="sm" showIcon={false}>
              Admin Control
            </Badge>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Configure active models, credentials, and endpoint bases for automated refund
            evaluation.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          className="flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </Button>
      </div>

      {/* Global Alerts */}
      {successMessage && (
        <Alert variant="success" title="Settings Updated" onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}
      {errorMessage && (
        <Alert variant="error" title="Error" onClose={() => setErrorMessage(null)}>
          {errorMessage}
        </Alert>
      )}

      {/* Active Provider Status Banner */}
      {activeProvider && (
        <div className="bg-gradient-to-r from-indigo-900 to-slate-900 rounded-2xl p-6 text-white shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase tracking-wider font-semibold text-indigo-300">
                Active Evaluation Provider
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Live
              </span>
            </div>
            <h2 className="text-xl font-bold capitalize">
              {activeProvider.llm} &bull; {activeProvider.llm_model}
            </h2>
            <p className="text-xs text-slate-300">
              {activeProvider.api_base
                ? `Endpoint: ${activeProvider.api_base}`
                : activeProvider.has_api_key
                  ? `API Key: ${activeProvider.api_key_masked}`
                  : 'Using default system credentials'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-xs text-slate-400">Deterministic Threshold</p>
              <p className="text-sm font-semibold text-white">
                Temp: {activeProvider.temperature} &bull; Timeout: {activeProvider.timeout_seconds}s
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Providers Grid */}
      {isLoading ? (
        <div className="text-center py-12 text-slate-500">Loading provider settings...</div>
      ) : isError ? (
        <Alert variant="error" title="Database Error">
          Failed to load provider configurations. Ensure database is running.
        </Alert>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {providers.map((provider) => (
            <ProviderCard
              key={provider.id}
              provider={provider}
              onActivate={(name) => activateMutation.mutate(name)}
              isActivating={activateMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const ProviderCard: React.FC<ProviderCardProps> = ({ provider, onActivate, isActivating }) => {
  const queryClient = useQueryClient();
  const meta = PROVIDER_METADATA[provider.llm] || {
    title: provider.llm.toUpperCase(),
    description: 'Custom language model provider.',
    icon: Cpu,
    badgeColor: 'indigo',
    defaultModels: [provider.llm_model],
  };

  const IconComponent = meta.icon;

  const [model, setModel] = useState(provider.llm_model);
  const [apiKey, setApiKey] = useState('');
  const [apiBase, setApiBase] = useState(provider.api_base || '');
  const [temperature, setTemperature] = useState(provider.temperature);
  const [timeoutSeconds, setTimeoutSeconds] = useState(provider.timeout_seconds);
  const [showKey, setShowKey] = useState(false);
  const [probeResult, setProbeResult] = useState<LLMTestProbeResponse | null>(null);
  const [isProbing, setIsProbing] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const saveMutation = useMutation({
    mutationFn: () =>
      updateLLMProvider(provider.llm, {
        llm_model: model,
        api_key: apiKey ? apiKey : undefined,
        api_base: apiBase ? apiBase : undefined,
        temperature,
        timeout_seconds: timeoutSeconds,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-llm-providers'] });
      setSaveSuccess(true);
      setApiKey('');
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  const handleTestProbe = async () => {
    setIsProbing(true);
    setProbeResult(null);
    try {
      const res = await testLLMConnection({
        llm: provider.llm,
        llm_model: model,
        api_key: apiKey || undefined,
        api_base: apiBase || undefined,
      });
      setProbeResult(res);
    } catch (err: unknown) {
      setProbeResult({
        llm: provider.llm,
        llm_model: model,
        status: 'offline',
        latency_ms: 0,
        message: 'Probe request failed.',
        error: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setIsProbing(false);
    }
  };

  return (
    <Card
      className={`relative flex flex-col justify-between transition-all duration-200 ${
        provider.is_active
          ? 'ring-2 ring-indigo-600 shadow-md bg-white'
          : 'bg-white hover:border-slate-300'
      }`}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                provider.is_active ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'
              }`}
            >
              <IconComponent className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 text-base">{meta.title}</h3>
              <span className="text-xs text-slate-500">{provider.llm}</span>
            </div>
          </div>

          {provider.is_active ? (
            <Badge status="approved" size="sm">
              Active
            </Badge>
          ) : (
            <Badge status="neutral" size="sm" showIcon={false}>
              Inactive
            </Badge>
          )}
        </div>

        <p className="text-xs text-slate-500 leading-relaxed">{meta.description}</p>

        {/* Model Selection */}
        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-slate-700">Selected Model</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="flex-1 text-xs border border-slate-300 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:ring-1 focus:ring-indigo-500 outline-none"
              placeholder="e.g. gpt-4o-mini"
            />
          </div>
          {/* Quick preset chips */}
          <div className="flex flex-wrap gap-1 mt-1">
            {meta.defaultModels.map((preset) => (
              <button
                key={preset}
                type="button"
                onClick={() => setModel(preset)}
                className={`text-[10px] px-2 py-0.5 rounded border transition-colors ${
                  model === preset
                    ? 'bg-indigo-50 border-indigo-200 text-indigo-700 font-semibold'
                    : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                }`}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* API Endpoint Base (for local Ollama) */}
        {provider.llm === 'ollama' && (
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700">
              Ollama Base Endpoint
            </label>
            <input
              type="text"
              value={apiBase}
              onChange={(e) => setApiBase(e.target.value)}
              className="w-full text-xs font-mono border border-slate-300 rounded-lg px-3 py-2 bg-slate-50 focus:bg-white focus:ring-1 focus:ring-indigo-500 outline-none"
              placeholder="http://host.docker.internal:11434"
            />
          </div>
        )}

        {/* API Key Input (for Cloud Providers) */}
        {provider.llm !== 'ollama' && (
          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <label className="block text-xs font-semibold text-slate-700">API Key</label>
              {provider.has_api_key && (
                <span className="text-[11px] font-mono text-slate-500">
                  Current: {provider.api_key_masked}
                </span>
              )}
            </div>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={provider.has_api_key ? 'Enter new key to update...' : 'sk-...'}
                className="w-full text-xs font-mono border border-slate-300 rounded-lg pl-3 pr-9 py-2 bg-slate-50 focus:bg-white focus:ring-1 focus:ring-indigo-500 outline-none"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
              >
                {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        )}

        {/* Temperature & Timeout Settings */}
        <div className="grid grid-cols-2 gap-3 pt-1">
          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <label className="text-xs font-semibold text-slate-700">Temperature</label>
              <span className="text-[11px] font-mono text-slate-500">{temperature}</span>
            </div>
            <input
              type="number"
              step="0.05"
              min="0.0"
              max="1.0"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value) || 0.0)}
              className="w-full text-xs font-mono border border-slate-300 rounded-lg px-2.5 py-1.5 bg-slate-50 focus:bg-white focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <label className="text-xs font-semibold text-slate-700">Timeout (s)</label>
              <span className="text-[11px] font-mono text-slate-500">{timeoutSeconds}s</span>
            </div>
            <input
              type="number"
              step="5"
              min="5"
              max="120"
              value={timeoutSeconds}
              onChange={(e) => setTimeoutSeconds(parseInt(e.target.value, 10) || 30)}
              className="w-full text-xs font-mono border border-slate-300 rounded-lg px-2.5 py-1.5 bg-slate-50 focus:bg-white focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          </div>
        </div>

        {/* Probe Test Result Card */}
        {probeResult && (
          <div
            className={`p-3 rounded-xl border text-xs space-y-1 ${
              probeResult.status === 'online'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                : 'bg-rose-50 border-rose-200 text-rose-900'
            }`}
          >
            <div className="flex items-center justify-between font-semibold">
              <span className="flex items-center gap-1.5">
                {probeResult.status === 'online' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600" />
                )}
                {probeResult.status === 'online' ? 'Connection Successful' : 'Connection Failed'}
              </span>
              <span>{probeResult.latency_ms}ms</span>
            </div>
            <p className="text-[11px] opacity-90">{probeResult.message}</p>
            {probeResult.error && (
              <p className="text-[10px] font-mono text-rose-700 bg-rose-100/50 p-1.5 rounded mt-1 overflow-x-auto">
                {probeResult.error}
              </p>
            )}
          </div>
        )}

        {saveSuccess && (
          <p className="text-xs font-medium text-emerald-600 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Settings saved successfully.
          </p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="pt-5 border-t border-slate-100 flex flex-col gap-2 mt-4">
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTestProbe}
            disabled={isProbing}
            className="w-full text-xs"
          >
            {isProbing ? 'Probing...' : 'Test Connection'}
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending}
            className="w-full text-xs"
          >
            {saveMutation.isPending ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>

        {!provider.is_active && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => onActivate(provider.llm)}
            disabled={isActivating}
            className="w-full text-xs mt-1"
          >
            {isActivating ? 'Activating...' : `Set as Active Provider`}
          </Button>
        )}
      </div>
    </Card>
  );
};
