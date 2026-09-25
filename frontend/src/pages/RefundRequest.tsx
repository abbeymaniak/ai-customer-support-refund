import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  Package,
  Loader2,
  Search,
  HelpCircle,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  FileCheck,
  AlertCircle,
  Check,
  UserCheck,
  History,
  Clock,
} from 'lucide-react';
import { refundApi } from '../api/refunds';
import type { RefundRequest as RefundRequestType } from '../types';
import { Alert, Badge } from '../components/ui';

const EMAIL_REGEX = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
const ORDER_REGEX = /^ORD-[0-9A-Za-z-]{3,32}$/;
const EXPLANATION_MIN = 10;
const EXPLANATION_MAX = 1000;

const SAMPLE_PERSONAS = [
  { label: 'Sarah Jenkins (Low Risk, $3.2k Spent)', email: 'sarah.jenkins@example.com' },
  { label: 'David Miller (Occasional, $450 Spent)', email: 'david.miller@example.com' },
  { label: 'Marcus Vance (High Risk 60% Return)', email: 'marcus.vance@example.com' },
  { label: 'Kevin Chen (40d Old Order, Expired)', email: 'kevin.chen@example.com' },
  { label: 'James Wilson (High Value $650 Item)', email: 'james.wilson@example.com' },
  { label: 'Amanda Price (Clearance / Final Sale)', email: 'amanda.price@example.com' },
];

export const RefundRequestPage: React.FC = () => {
  const [emailInput, setEmailInput] = useState('');
  const [emailTouched, setEmailTouched] = useState(false);
  const [activeEmail, setActiveEmail] = useState('');
  const [selectedOrderId, setSelectedOrderId] = useState<string>('');
  const [selectedItemId, setSelectedItemId] = useState<string>('');
  const [itemCondition, setItemCondition] = useState<string>('unopened');
  const [quantity, setQuantity] = useState<number>(1);
  const [reasonCategory, setReasonCategory] = useState<string>('defective');
  const [explanation, setExplanation] = useState<string>('');
  const [decisionResult, setDecisionResult] = useState<RefundRequestType | null>(null);

  const isEmailValid = EMAIL_REGEX.test(emailInput.trim());
  const explanationLength = explanation.trim().length;
  const isExplanationValid =
    explanationLength >= EXPLANATION_MIN && explanationLength <= EXPLANATION_MAX;

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

  // Fetch refund history for customer
  const refundHistoryQuery = useQuery({
    queryKey: ['customer-refunds', customerQuery.data?.id],
    queryFn: () => refundApi.getCustomerRefunds(customerQuery.data!.id),
    enabled: !!customerQuery.data?.id,
  });


  const selectedOrder = ordersQuery.data?.find((o) => o.id === selectedOrderId);
  const selectedItem = selectedOrder?.items.find((i) => i.id === selectedItemId);

  // Submit refund mutation
  const queryClient = useQueryClient();
  const refundMutation = useMutation({
    mutationFn: refundApi.submitRefundRequest,
    onSuccess: (data) => {
      setDecisionResult(data);
      queryClient.invalidateQueries({ queryKey: ['customer-refunds'] });
    },
  });

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    if (isEmailValid) {
      setActiveEmail(emailInput.trim());
      setSelectedOrderId('');
      setSelectedItemId('');
      setDecisionResult(null);
      refundMutation.reset();
    }
  };

  const handleSelectPersona = (email: string) => {
    setEmailInput(email);
    setEmailTouched(false);
    setActiveEmail(email);
    setSelectedOrderId('');
    setSelectedItemId('');
    setDecisionResult(null);
    refundMutation.reset();
  };

  const handleResetForm = () => {
    setDecisionResult(null);
    setSelectedItemId('');
    setExplanation('');
    refundMutation.reset();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder || !selectedItem || !isExplanationValid) return;

    refundMutation.mutate({
      customer_email: activeEmail,
      order_number: selectedOrder.order_number,
      item_id: selectedItem.id,
      amount: selectedItem.price * quantity,
      reason_category: reasonCategory,
      customer_explanation: explanation.trim(),
      quantity,
      item_condition: itemCondition,
    });
  };

  const policyChecks = decisionResult?.policy_checks as
    | {
        matched_rules?: string[];
        triggered_red_flags?: string[];
        reasons?: string[];
        citations?: string[];
      }
    | undefined;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Hero Header */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
          Customer Support Refund Portal
        </h1>
        <p className="text-slate-600 text-sm sm:text-base">
          Submit and evaluate refund claims in seconds with our transparent, policy guided
          artificial intelligence assistant.
        </p>
      </div>

      {/* Demo Persona Quick-Picker */}
      <div className="bg-slate-100/80 p-4 rounded-xl border border-slate-200">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
          <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
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
                  ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
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
              <Search className="w-5 h-5 text-emerald-600" />
              <span>Step 1: Customer Account</span>
            </h2>

            <form onSubmit={handleLookup} className="space-y-2">
              <div className="flex gap-2">
                <input
                  type="email"
                  value={emailInput}
                  onChange={(e) => {
                    setEmailInput(e.target.value);
                    setEmailTouched(true);
                  }}
                  onBlur={() => setEmailTouched(true)}
                  placeholder="Enter customer email address..."
                  required
                  className={`flex-1 px-4 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 transition ${
                    emailTouched && !isEmailValid
                      ? 'border-rose-300 focus:ring-rose-500 bg-rose-50/20'
                      : emailTouched && isEmailValid
                        ? 'border-emerald-300 focus:ring-emerald-500 bg-emerald-50/20'
                        : 'border-slate-300 focus:ring-emerald-500'
                  }`}
                />
                <button
                  type="submit"
                  disabled={customerQuery.isLoading || !isEmailValid}
                  className="px-5 py-2.5 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 transition disabled:opacity-50 flex items-center space-x-1.5"
                >
                  <Search className="w-4 h-4" />
                  <span>Lookup</span>
                </button>
              </div>

              {emailTouched && !isEmailValid && (
                <p className="text-xs text-rose-600 flex items-center space-x-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>Please enter a valid email address (e.g. name@example.com).</span>
                </p>
              )}
              {emailTouched && isEmailValid && (
                <p className="text-xs text-emerald-600 flex items-center space-x-1">
                  <Check className="w-3.5 h-3.5" />
                  <span>Valid email address format.</span>
                </p>
              )}
            </form>

            {customerQuery.isError && (
              <Alert variant="error" title="Customer Lookup Error">
                {customerQuery.error instanceof Error
                  ? customerQuery.error.message
                  : 'Customer account not found.'}
              </Alert>
            )}

            {customerQuery.data && (
              <div className="mt-4 p-4 rounded-xl bg-emerald-50/50 border border-emerald-100 flex flex-wrap gap-4 text-xs">
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
                <div>
                  <span className="text-slate-500 block">Risk Score</span>
                  <strong
                    className={`text-sm ${customerQuery.data.risk_score > 0.4 ? 'text-rose-600' : 'text-slate-700'}`}
                  >
                    {(customerQuery.data.risk_score * 100).toFixed(0)}/100
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
                <Package className="w-5 h-5 text-emerald-600" />
                <span>Step 2: Select Order & Item</span>
              </h2>

              {/* Select Order */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <label className="block text-xs font-semibold text-slate-700 uppercase">
                    Select Order
                  </label>
                  {selectedOrder && ORDER_REGEX.test(selectedOrder.order_number) && (
                    <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      <ShieldCheck className="w-3 h-3 text-emerald-600" />
                      <span>Validated Format ({selectedOrder.order_number})</span>
                    </span>
                  )}
                </div>
                <select
                  value={selectedOrderId}
                  onChange={(e) => {
                    setSelectedOrderId(e.target.value);
                    setSelectedItemId('');
                    setDecisionResult(null);
                  }}
                  required
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="">Choose an Order</option>
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
                            ? 'border-emerald-600 bg-emerald-50/50 shadow-sm'
                            : 'border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <input
                            type="radio"
                            name="item"
                            value={item.id}
                            checked={selectedItemId === item.id}
                            onChange={() => {
                              setSelectedItemId(item.id);
                              setDecisionResult(null);
                            }}
                            className="text-emerald-600 focus:ring-emerald-500"
                          />
                          <div>
                            <div className="flex items-center space-x-2">
                              <p className="text-sm font-medium text-slate-900">{item.name}</p>
                              {item.is_final_sale && (
                                <Badge status="denied" size="sm" showIcon={false}>
                                  Final Sale
                                </Badge>
                              )}
                            </div>
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

              {/* Item Condition & Quantity */}
              {selectedItem && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="block text-xs font-semibold text-slate-700 uppercase">
                      Item Condition
                    </label>
                    <select
                      value={itemCondition}
                      onChange={(e) => setItemCondition(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    >
                      <option value="unopened">Unopened (Original packaging)</option>
                      <option value="opened_used">Opened / Used</option>
                      <option value="damaged">Damaged / Defective on arrival</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="block text-xs font-semibold text-slate-700 uppercase">
                      Quantity to Refund
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={selectedItem.quantity || 1}
                      value={quantity}
                      onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
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
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    >
                      <option value="defective">
                        Item defective or does not function as advertised
                      </option>
                      <option value="damaged_on_arrival">Item arrived damaged or broken</option>
                      <option value="wrong_item_sent">Wrong item sent by merchant</option>
                      <option value="unwanted">Changed mind or no longer needed</option>
                      <option value="bought_by_mistake">Ordered by mistake</option>
                      <option value="item_not_received">Item not received</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex justify-between items-center">
                      <label className="block text-xs font-semibold text-slate-700 uppercase">
                        Explanation / Notes (Evaluated by AI)
                      </label>
                      <span
                        className={`text-xs font-mono font-medium ${
                          explanation.length > EXPLANATION_MAX
                            ? 'text-rose-600 font-bold'
                            : explanationLength >= EXPLANATION_MIN
                              ? 'text-emerald-600'
                              : explanation.length > 0
                                ? 'text-amber-600'
                                : 'text-slate-400'
                        }`}
                      >
                        {explanation.length} / {EXPLANATION_MAX} chars (min {EXPLANATION_MIN})
                      </span>
                    </div>
                    <textarea
                      rows={3}
                      value={explanation}
                      onChange={(e) => setExplanation(e.target.value)}
                      placeholder="Please explain the issue in detail (at least 10 characters)..."
                      className={`w-full px-3.5 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 transition ${
                        explanation.length > EXPLANATION_MAX
                          ? 'border-rose-300 focus:ring-rose-500 bg-rose-50/20'
                          : explanationLength >= EXPLANATION_MIN
                            ? 'border-emerald-300 focus:ring-emerald-500'
                            : explanation.length > 0
                              ? 'border-amber-300 focus:ring-amber-500'
                              : 'border-slate-300 focus:ring-emerald-500'
                      }`}
                    />
                    {explanation.length > 0 && explanationLength < EXPLANATION_MIN && (
                      <p className="text-xs text-amber-600 flex items-center space-x-1">
                        <AlertCircle className="w-3.5 h-3.5" />
                        <span>
                          Explanation must be at least {EXPLANATION_MIN} characters ({EXPLANATION_MIN - explanationLength} more needed).
                        </span>
                      </p>
                    )}
                    {explanation.length > EXPLANATION_MAX && (
                      <p className="text-xs text-rose-600 flex items-center space-x-1">
                        <AlertCircle className="w-3.5 h-3.5" />
                        <span>
                          Explanation cannot exceed {EXPLANATION_MAX} characters ({explanation.length - EXPLANATION_MAX} characters over limit).
                        </span>
                      </p>
                    )}
                    {isExplanationValid && (
                      <p className="text-xs text-emerald-600 flex items-center space-x-1">
                        <Check className="w-3.5 h-3.5" />
                        <span>Valid explanation length for policy evaluation.</span>
                      </p>
                    )}
                  </div>

                  {/* Security Perimeter Notice */}
                  <div className="p-3 bg-slate-50/80 rounded-xl border border-slate-200 text-xs text-slate-600 space-y-1">
                    <div className="flex items-center space-x-1.5 font-semibold text-slate-700">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      <span>Security & Prompt Injection Protection</span>
                    </div>
                    <p className="text-[11px] text-slate-500 leading-normal">
                      Inputs are sanitized against script tags and checked by security classifiers. Claims are evaluated strictly against store return policies.
                    </p>
                  </div>

                  {refundMutation.isError && (
                    <Alert variant="error" title="Submission Error">
                      {refundMutation.error instanceof Error
                        ? refundMutation.error.message
                        : 'Could not process refund request.'}
                    </Alert>
                  )}

                  <button
                    type="submit"
                    disabled={refundMutation.isPending || !isExplanationValid}
                    className="w-full py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold shadow-md shadow-emerald-100 transition duration-150 flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {refundMutation.isPending ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>Policy & AI Engine Evaluating...</span>
                      </>
                    ) : (
                      <>
                        <span>
                          Submit Refund Claim (${(selectedItem.price * quantity).toFixed(2)})
                        </span>
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
            <div className="border-b border-slate-100 pb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-600" />
                  <span>AI Decision Engine Verdict</span>
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Real time policy validation and multi factor risk determination.
                </p>
              </div>
              {decisionResult && (
                <button
                  type="button"
                  onClick={handleResetForm}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
                  title="Submit Another Claim"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              )}
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
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold px-3 py-1 rounded-full bg-white/80 border">
                      Confidence: {((decisionResult.confidence_score || 0.95) * 100).toFixed(0)}%
                    </span>
                    {decisionResult.request_number && (
                      <span className="text-xs font-mono px-2 py-1 rounded-md bg-white/60 border text-slate-700">
                        {decisionResult.request_number}
                      </span>
                    )}
                  </div>
                </div>

                {/* AI Reasoning Narrative */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
                    <FileCheck className="w-4 h-4 text-emerald-600" />
                    <span>Decision Reasoning</span>
                  </h4>
                  <p className="text-sm text-slate-700 bg-slate-50 p-3.5 rounded-xl border border-slate-200 leading-relaxed">
                    {decisionResult.decision_reason ||
                      'Request evaluated against official store return policy.'}
                  </p>
                </div>

                {/* Matched Rules and Policy Citations */}
                {policyChecks?.matched_rules && policyChecks.matched_rules.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Policy Rules Applied
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {policyChecks.matched_rules.map((rule) => (
                        <Badge key={rule} status="neutral" size="sm" showIcon={false}>
                          {rule}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {policyChecks?.citations && policyChecks.citations.length > 0 && (
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Official Policy References
                    </h4>
                    <ul className="text-xs text-slate-600 space-y-1 bg-slate-50 p-3 rounded-lg border border-slate-200">
                      {policyChecks.citations.map((c, idx) => (
                        <li key={idx} className="flex items-start space-x-2">
                          <span className="text-emerald-600 font-bold">•</span>
                          <span>{c}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {policyChecks?.triggered_red_flags &&
                  policyChecks.triggered_red_flags.length > 0 && (
                    <div className="space-y-1.5">
                      <h4 className="text-xs font-bold text-rose-700 uppercase tracking-wider flex items-center space-x-1">
                        <ShieldAlert className="w-4 h-4 text-rose-600" />
                        <span>Security / Red Flags Flagged</span>
                      </h4>
                      <div className="flex flex-wrap gap-1.5">
                        {policyChecks.triggered_red_flags.map((flag) => (
                          <Badge key={flag} status="denied" size="sm">
                            {flag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            ) : refundMutation.isPending ? (
              <div className="py-14 text-center space-y-5">
                <div className="relative mx-auto w-16 h-16 flex items-center justify-center">
                  <div className="absolute inset-0 rounded-full bg-emerald-100 animate-ping opacity-75"></div>
                  <div className="relative rounded-full bg-emerald-600 p-3.5 text-white shadow-lg shadow-emerald-100">
                    <Loader2 className="w-8 h-8 animate-spin" />
                  </div>
                </div>
                <div className="space-y-2">
                  <h3 className="text-base font-bold text-slate-800 flex items-center justify-center space-x-1">
                    <span>Evaluating your request</span>
                    <span className="inline-flex items-center space-x-1 ml-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </span>
                  </h3>
                  <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed">
                    Analyzing order history, product condition, and store policies with the decision engine.
                  </p>
                </div>
                <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-emerald-50 border border-emerald-100 text-xs text-emerald-700 font-medium">
                  <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse"></span>
                  <span>AI reasoning in progress (few seconds for local models)</span>
                </div>
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

      {/* Refund History Section */}
      {customerQuery.data && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <History className="w-5 h-5 text-emerald-600" />
              <h2 className="text-lg font-bold text-slate-900">Refund History</h2>
            </div>
            <span className="text-xs font-medium text-slate-500">
              {refundHistoryQuery.data?.length ?? 0} request{(refundHistoryQuery.data?.length ?? 0) !== 1 ? 's' : ''}
            </span>
          </div>

          {refundHistoryQuery.isLoading ? (
            <div className="p-8 text-center text-slate-400 text-sm">Loading refund history...</div>
          ) : refundHistoryQuery.isError ? (
            <div className="p-8 text-center text-rose-500 text-sm">Failed to load refund history.</div>
          ) : !refundHistoryQuery.data || refundHistoryQuery.data.length === 0 ? (
            <div className="p-10 text-center space-y-2 text-slate-400">
              <CheckCircle2 className="w-10 h-10 mx-auto stroke-1 text-slate-300" />
              <p className="text-sm">No refund requests found for this customer.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100 text-left">
                    <th className="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Request #</th>
                    <th className="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Item</th>
                    <th className="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Amount</th>
                    <th className="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Decision</th>
                    <th className="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Override</th>
                    <th className="px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {refundHistoryQuery.data.map((refund) => (
                    <tr key={refund.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-5 py-3.5">
                        <span className="font-mono text-xs text-slate-700 font-medium">
                          {refund.request_number || refund.id.slice(0, 8)}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-xs text-slate-700">
                          {refund.item_name || refund.reason_category}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-xs font-semibold text-slate-900">
                          ${refund.amount.toFixed(2)}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-bold border ${
                            refund.decision === 'Approved'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : refund.decision === 'Denied'
                                ? 'bg-rose-50 text-rose-700 border-rose-200'
                                : refund.decision === 'Escalated'
                                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                                  : 'bg-slate-50 text-slate-600 border-slate-200'
                          }`}
                        >
                          {refund.decision === 'Approved' && <CheckCircle2 className="w-3 h-3" />}
                          {refund.decision === 'Denied' && <XCircle className="w-3 h-3" />}
                          {refund.decision === 'Escalated' && <AlertTriangle className="w-3 h-3" />}
                          {refund.decision === 'pending' && <Clock className="w-3 h-3" />}
                          <span className="capitalize">{refund.decision}</span>
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        {refund.human_override ? (
                          <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 text-[11px] font-semibold">
                            Overridden
                          </span>
                        ) : (
                          <span className="text-slate-400 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3.5 text-xs text-slate-500">
                        {new Date(refund.created_at).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
