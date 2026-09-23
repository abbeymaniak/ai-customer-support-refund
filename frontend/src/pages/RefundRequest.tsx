import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  Package,
  Sparkles,
  Search,
  HelpCircle,
} from 'lucide-react';
import { refundApi } from '../api/refunds';
import type { RefundRequest as RefundRequestType } from '../types';

const SAMPLE_PERSONAS = [
  { label: 'Sarah Jenkins (Low Risk, $3.2k Spent)', email: 'sarah.jenkins@example.com' },
  { label: 'David Miller (Occasional, $450 Spent)', email: 'david.miller@example.com' },
  { label: 'Marcus Vance (High Risk 60% Return)', email: 'marcus.vance@example.com' },
  { label: 'Kevin Chen (40d Old Order, Expired)', email: 'kevin.chen@example.com' },
  { label: 'James Wilson (High Value $650 Item)', email: 'james.wilson@example.com' },
  { label: 'Amanda Price (Clearance / Final Sale)', email: 'amanda.price@example.com' },
];

export const RefundRequestPage: React.FC = () => {
  const [emailInput, setEmailInput] = useState('sarah.jenkins@example.com');
  const [activeEmail, setActiveEmail] = useState('sarah.jenkins@example.com');
  const [selectedOrderId, setSelectedOrderId] = useState<string>('');
  const [selectedItemId, setSelectedItemId] = useState<string>('');
  const [reasonCategory, setReasonCategory] = useState<string>('damaged_on_arrival');
  const [explanation, setExplanation] = useState<string>('');
  const [decisionResult, setDecisionResult] = useState<RefundRequestType | null>(null);

  // Fetch customer by active email
  const customerQuery = useQuery({
    queryKey: ['customer', activeEmail],
    queryFn: () => refundApi.getCustomerByEmail(activeEmail),
    enabled: !!activeEmail,
    retry: 1,
  });

  // Fetch orders for customer
  const ordersQuery = useQuery({
    queryKey: ['orders', customerQuery.data?.id],
    queryFn: () => refundApi.getCustomerOrders(customerQuery.data!.id),
    enabled: !!customerQuery.data?.id,
  });

  const selectedOrder = ordersQuery.data?.find((o) => o.id === selectedOrderId);
  const selectedItem = selectedOrder?.items.find((i) => i.id === selectedItemId);

  // Submit refund mutation
  const refundMutation = useMutation({
    mutationFn: refundApi.submitRefundRequest,
    onSuccess: (data) => {
      setDecisionResult(data);
    },
  });

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    if (emailInput.trim()) {
      setActiveEmail(emailInput.trim());
      setSelectedOrderId('');
      setSelectedItemId('');
      setDecisionResult(null);
    }
  };

  const handleSelectPersona = (email: string) => {
    setEmailInput(email);
    setActiveEmail(email);
    setSelectedOrderId('');
    setSelectedItemId('');
    setDecisionResult(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder || !selectedItem) return;

    refundMutation.mutate({
      customer_email: activeEmail,
      order_number: selectedOrder.order_number,
      item_id: selectedItem.id,
      amount: selectedItem.price,
      reason_category: reasonCategory,
      customer_explanation: explanation || 'Customer requested refund for item.',
    });
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Hero Header */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
          Customer Support Refund Portal
        </h1>
        <p className="text-slate-600 text-sm sm:text-base">
          Submit and evaluate refund claims in seconds with our transparent, policy-guided AI
          assistant.
        </p>
      </div>

      {/* Demo Persona Quick-Picker */}
      <div className="bg-slate-100/80 p-4 rounded-xl border border-slate-200">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Quick Load Test Persona (Evaluation Scenarios)</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_PERSONAS.map((p) => (
            <button
              key={p.email}
              type="button"
              onClick={() => handleSelectPersona(p.email)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                activeEmail === p.email
                  ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                  : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Form and Selection */}
        <div className="lg:col-span-7 space-y-6">
          {/* Customer Lookup Card */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
              <Search className="w-5 h-5 text-indigo-600" />
              <span>Step 1: Customer Account</span>
            </h2>

            <form onSubmit={handleLookup} className="flex gap-2">
              <input
                type="email"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                placeholder="Enter customer email address..."
                required
                className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
              />
              <button
                type="submit"
                disabled={customerQuery.isLoading}
                className="px-5 py-2.5 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 transition disabled:opacity-50"
              >
                Lookup
              </button>
            </form>

            {customerQuery.data && (
              <div className="mt-4 p-4 rounded-xl bg-indigo-50/50 border border-indigo-100 flex flex-wrap gap-4 text-xs">
                <div>
                  <span className="text-slate-500 block">Name</span>
                  <strong className="text-slate-900 text-sm">{customerQuery.data.name}</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Total Spent</span>
                  <strong className="text-slate-900 text-sm">
                    ${customerQuery.data.total_spent.toFixed(2)}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Orders</span>
                  <strong className="text-slate-900 text-sm">
                    {customerQuery.data.orders_count}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Return Rate</span>
                  <strong
                    className={`text-sm ${customerQuery.data.return_rate > 0.3 ? 'text-rose-600' : 'text-emerald-600'}`}
                  >
                    {(customerQuery.data.return_rate * 100).toFixed(0)}%
                  </strong>
                </div>
              </div>
            )}
          </div>

          {/* Refund Claim Form */}
          {customerQuery.data && (
            <form
              onSubmit={handleSubmit}
              className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6"
            >
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <Package className="w-5 h-5 text-indigo-600" />
                <span>Step 2: Select Order & Item</span>
              </h2>

              {/* Select Order */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700 uppercase">
                  Select Order
                </label>
                <select
                  value={selectedOrderId}
                  onChange={(e) => {
                    setSelectedOrderId(e.target.value);
                    setSelectedItemId('');
                  }}
                  required
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- Choose an Order --</option>
                  {ordersQuery.data?.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.order_number} ({new Date(o.order_date).toLocaleDateString()}) - $
                      {o.total_amount.toFixed(2)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Select Item */}
              {selectedOrder && (
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-700 uppercase">
                    Select Item to Refund
                  </label>
                  <div className="grid grid-cols-1 gap-2">
                    {selectedOrder.items.map((item) => (
                      <label
                        key={item.id}
                        className={`flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition-all ${
                          selectedItemId === item.id
                            ? 'border-indigo-600 bg-indigo-50/50 shadow-sm'
                            : 'border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <input
                            type="radio"
                            name="item"
                            value={item.id}
                            checked={selectedItemId === item.id}
                            onChange={() => setSelectedItemId(item.id)}
                            className="text-indigo-600 focus:ring-indigo-500"
                          />
                          <div>
                            <p className="text-sm font-medium text-slate-900">{item.name}</p>
                            <span className="text-xs text-slate-500 capitalize">
                              Category: {item.category}
                            </span>
                          </div>
                        </div>
                        <span className="font-semibold text-sm text-slate-900">
                          ${item.price.toFixed(2)}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Reason & Explanation */}
              {selectedItem && (
                <>
                  <div className="space-y-1.5">
                    <label className="block text-xs font-semibold text-slate-700 uppercase">
                      Reason for Refund
                    </label>
                    <select
                      value={reasonCategory}
                      onChange={(e) => setReasonCategory(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="damaged_on_arrival">Item arrived damaged or broken</option>
                      <option value="defective">
                        Item defective / does not function as advertised
                      </option>
                      <option value="wrong_item_sent">Wrong item sent by merchant</option>
                      <option value="unwanted">Changed mind / No longer needed</option>
                      <option value="late_delivery">Arrived significantly late</option>
                      <option value="not_as_described">Significantly not as described</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="block text-xs font-semibold text-slate-700 uppercase">
                      Explanation / Notes (Evaluated by AI)
                    </label>
                    <textarea
                      rows={3}
                      value={explanation}
                      onChange={(e) => setExplanation(e.target.value)}
                      placeholder="Please explain the issue in detail..."
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={refundMutation.isPending}
                    className="w-full py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-md shadow-indigo-100 transition duration-150 flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {refundMutation.isPending ? (
                      <>
                        <Sparkles className="w-5 h-5 animate-spin" />
                        <span>AI Reasoning Engine Evaluating...</span>
                      </>
                    ) : (
                      <>
                        <span>Submit Refund Claim</span>
                        <ArrowRight className="w-5 h-5" />
                      </>
                    )}
                  </button>
                </>
              )}
            </form>
          )}
        </div>

        {/* Right Column: AI Decision Outcome */}
        <div className="lg:col-span-5">
          <div className="sticky top-24 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-indigo-600" />
                <span>AI Decision Engine Verdict</span>
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Real-time policy validation and multi-factor risk determination.
              </p>
            </div>

            {decisionResult ? (
              <div className="space-y-6">
                {/* Decision Badge */}
                <div
                  className={`p-5 rounded-2xl border text-center flex flex-col items-center justify-center space-y-2 ${
                    decisionResult.decision === 'Approved'
                      ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                      : decisionResult.decision === 'Denied'
                        ? 'bg-rose-50/70 border-rose-200 text-rose-900'
                        : 'bg-amber-50/70 border-amber-200 text-amber-900'
                  }`}
                >
                  {decisionResult.decision === 'Approved' && (
                    <CheckCircle2 className="w-12 h-12 text-emerald-600" />
                  )}
                  {decisionResult.decision === 'Denied' && (
                    <XCircle className="w-12 h-12 text-rose-600" />
                  )}
                  {decisionResult.decision === 'Escalated' && (
                    <AlertTriangle className="w-12 h-12 text-amber-600" />
                  )}

                  <span className="text-2xl font-black uppercase tracking-wide">
                    {decisionResult.decision}
                  </span>
                  <span className="text-xs font-semibold px-3 py-1 rounded-full bg-white/80 border">
                    Confidence: {((decisionResult.confidence_score || 0.95) * 100).toFixed(0)}%
                  </span>
                </div>

                {/* AI Reasoning Narrative */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    AI Reasoning Summary
                  </h4>
                  <p className="text-sm text-slate-700 bg-slate-50 p-3.5 rounded-xl border border-slate-200 leading-relaxed">
                    {decisionResult.decision_reason ||
                      'Request evaluated against official store return policy.'}
                  </p>
                </div>

                {/* Policy Checks Checklist */}
                {decisionResult.policy_checks && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Policy Checks
                    </h4>
                    <div className="space-y-1.5 text-xs">
                      {Object.entries(decisionResult.policy_checks).map(
                        ([key, val]: [string, unknown]) => (
                          <div
                            key={key}
                            className="flex items-center justify-between p-2 rounded-lg bg-slate-50"
                          >
                            <span className="text-slate-600 capitalize">
                              {key.replace(/_/g, ' ')}
                            </span>
                            <span
                              className={
                                val
                                  ? 'text-emerald-600 font-semibold'
                                  : 'text-rose-600 font-semibold'
                              }
                            >
                              {val ? 'Passed' : 'Failed'}
                            </span>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-16 text-center space-y-3 text-slate-400">
                <HelpCircle className="w-12 h-12 mx-auto stroke-1 text-slate-300" />
                <p className="text-sm">
                  Select an order and item on the left to trigger the AI decision engine.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
