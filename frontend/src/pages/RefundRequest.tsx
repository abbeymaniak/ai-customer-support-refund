import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  Package,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  FileCheck,
  AlertCircle,
  Check,
  RotateCcw,
  History,
  Clock,
  User,
  ShoppingBag,
  Info,
} from 'lucide-react';
import { customerPortalApi } from '../api/customerPortal';
import { refundApi } from '../api/refunds';
import { useCustomerAuth } from '../context/CustomerAuthContext';
import type { CustomerRefundClaimPayload, RefundRequest as RefundRequestType } from '../types';
import { Alert, Badge } from '../components/ui';

const ORDER_REGEX = /^ORD-[0-9A-Za-z-]{3,32}$/;
const EXPLANATION_MIN = 10;
const EXPLANATION_MAX = 1000;

export const RefundRequestPage: React.FC = () => {
  const { customer } = useCustomerAuth();
  const queryClient = useQueryClient();

  // Wizard step state: 1 = Order & Item, 2 = Reason & Notes, 3 = Review & Submit
  const [wizardStep, setWizardStep] = useState<number>(1);

  // Form input state
  const [selectedOrderId, setSelectedOrderId] = useState<string>('');
  const [selectedItemId, setSelectedItemId] = useState<string>('');
  const [itemCondition, setItemCondition] = useState<string>('unopened');
  const [quantity, setQuantity] = useState<number>(1);
  const [reasonCategory, setReasonCategory] = useState<string>('defective');
  const [explanation, setExplanation] = useState<string>('');
  const [decisionResult, setDecisionResult] = useState<RefundRequestType | null>(null);

  // Scoped orders query for authenticated customer
  const ordersQuery = useQuery({
    queryKey: ['customer-orders'],
    queryFn: () => customerPortalApi.getMyOrders(),
    enabled: !!customer,
  });

  // Refund history query for authenticated customer
  const refundHistoryQuery = useQuery({
    queryKey: ['customer-refunds', customer?.id],
    queryFn: () => refundApi.getCustomerRefunds(customer!.id),
    enabled: !!customer?.id,
  });

  // Scoped refund submission mutation
  const refundMutation = useMutation({
    mutationFn: (payload: CustomerRefundClaimPayload) => customerPortalApi.submitRefund(payload),
    onSuccess: (data) => {
      setDecisionResult(data);
      queryClient.invalidateQueries({ queryKey: ['customer-orders'] });
      if (customer?.id) {
        queryClient.invalidateQueries({ queryKey: ['customer-refunds', customer.id] });
      }
    },
  });

  const selectedOrder = ordersQuery.data?.find((o) => o.id === selectedOrderId);
  const selectedItem = selectedOrder?.items.find((i) => i.id === selectedItemId);

  const explanationLength = explanation.trim().length;
  const isExplanationValid =
    explanationLength >= EXPLANATION_MIN && explanationLength <= EXPLANATION_MAX;

  const canProceedStep1 = Boolean(
    selectedOrder && selectedItem && !selectedItem.has_active_claim
  );
  const canProceedStep2 = isExplanationValid;

  const handleResetForm = () => {
    setWizardStep(1);
    setSelectedOrderId('');
    setSelectedItemId('');
    setExplanation('');
    setDecisionResult(null);
    refundMutation.reset();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder || !selectedItem || !isExplanationValid) return;

    refundMutation.mutate({
      order_id: selectedOrder.id,
      item_id: selectedItem.id,
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
          Submit and evaluate refund claims in seconds with our transparent policy guided
          artificial intelligence assistant.
        </p>
      </div>

      {/* Authenticated Customer Profile Summary Card */}
      {customer && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-700 font-bold text-lg">
                {customer.name.slice(0, 1).toUpperCase()}
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="text-lg font-bold text-slate-900">{customer.name}</h2>
                  <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <ShieldCheck className="w-3 h-3 text-emerald-600" />
                    <span>Verified Session</span>
                  </span>
                </div>
                <p className="text-xs text-slate-500">{customer.email}</p>
              </div>
            </div>

            <div className="flex items-center space-x-2 text-xs text-slate-500">
              <User className="w-4 h-4 text-emerald-600" />
              <span>Customer ID: {customer.id.slice(0, 8)}</span>
            </div>
          </div>

          {/* Profile Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-1">
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
              <span className="text-xs text-slate-500 block mb-1">Total Purchases</span>
              <strong className="text-slate-900 text-base font-bold">
                ${customer.total_spent.toFixed(2)}
              </strong>
            </div>
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
              <span className="text-xs text-slate-500 block mb-1">Verified Orders</span>
              <strong className="text-slate-900 text-base font-bold">
                {customer.orders_count}
              </strong>
            </div>
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
              <span className="text-xs text-slate-500 block mb-1">Return Rate</span>
              <strong
                className={`text-base font-bold ${
                  customer.return_rate > 0.3 ? 'text-rose-600' : 'text-emerald-600'
                }`}
              >
                {(customer.return_rate * 100).toFixed(0)}%
              </strong>
            </div>
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
              <span className="text-xs text-slate-500 block mb-1">Risk Profile</span>
              <strong
                className={`text-base font-bold ${
                  customer.risk_score > 0.4 ? 'text-rose-600' : 'text-emerald-700'
                }`}
              >
                {(customer.risk_score * 100).toFixed(0)} / 100
              </strong>
            </div>
          </div>
        </div>
      )}

      {/* Main Grid: Wizard Form and Decision Result */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: 3 Step Claim Wizard */}
        <div className="lg:col-span-7 space-y-6">
          {/* Wizard Stepper Bar */}
          <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm">
            <div className="grid grid-cols-3 gap-2 text-center">
              <button
                type="button"
                onClick={() => setWizardStep(1)}
                className={`py-2.5 px-3 rounded-xl text-xs font-semibold transition flex items-center justify-center space-x-1.5 ${
                  wizardStep === 1
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                }`}
              >
                <span className="w-5 h-5 rounded-full border flex items-center justify-center text-[10px] font-bold">
                  1
                </span>
                <span className="truncate">Select Order & Item</span>
              </button>

              <button
                type="button"
                onClick={() => canProceedStep1 && setWizardStep(2)}
                disabled={!canProceedStep1}
                className={`py-2.5 px-3 rounded-xl text-xs font-semibold transition flex items-center justify-center space-x-1.5 ${
                  wizardStep === 2
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : canProceedStep1
                      ? 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                      : 'bg-slate-50 text-slate-300 cursor-not-allowed'
                }`}
              >
                <span className="w-5 h-5 rounded-full border flex items-center justify-center text-[10px] font-bold">
                  2
                </span>
                <span className="truncate">Reason & Notes</span>
              </button>

              <button
                type="button"
                onClick={() => canProceedStep1 && canProceedStep2 && setWizardStep(3)}
                disabled={!canProceedStep1 || !canProceedStep2}
                className={`py-2.5 px-3 rounded-xl text-xs font-semibold transition flex items-center justify-center space-x-1.5 ${
                  wizardStep === 3
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : canProceedStep1 && canProceedStep2
                      ? 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                      : 'bg-slate-50 text-slate-300 cursor-not-allowed'
                }`}
              >
                <span className="w-5 h-5 rounded-full border flex items-center justify-center text-[10px] font-bold">
                  3
                </span>
                <span className="truncate">Review & Submit</span>
              </button>
            </div>
          </div>

          {/* Wizard Body Card */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6">
            {ordersQuery.isLoading && (
              <div className="py-12 text-center space-y-3">
                <Loader2 className="w-8 h-8 text-emerald-600 animate-spin mx-auto" />
                <p className="text-sm text-slate-500">Retrieving your verified customer orders...</p>
              </div>
            )}

            {ordersQuery.isError && (
              <Alert variant="error" title="Order Loading Error">
                Could not load your orders. Please refresh the page or sign in again.
              </Alert>
            )}

            {!ordersQuery.isLoading && ordersQuery.data && ordersQuery.data.length === 0 && (
              <div className="py-12 text-center space-y-3">
                <ShoppingBag className="w-12 h-12 text-slate-300 stroke-1 mx-auto" />
                <h3 className="text-base font-bold text-slate-800">No Orders Found</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  You do not have any past purchase orders associated with this account.
                </p>
              </div>
            )}

            {/* Step 1: Select Order and Item */}
            {!ordersQuery.isLoading && ordersQuery.data && ordersQuery.data.length > 0 && wizardStep === 1 && (
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                    <Package className="w-5 h-5 text-emerald-600" />
                    <span>Step 1: Select Order & Item</span>
                  </h2>
                  <span className="text-xs text-slate-500 font-medium">
                    {ordersQuery.data.length} available order{ordersQuery.data.length !== 1 ? 's' : ''}
                  </span>
                </div>

                {/* Choose Order Dropdown */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <label className="block text-xs font-semibold text-slate-700 uppercase">
                      Select Past Order
                    </label>
                    {selectedOrder && ORDER_REGEX.test(selectedOrder.order_number) && (
                      <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        <ShieldCheck className="w-3 h-3 text-emerald-600" />
                        <span>Verified Order ({selectedOrder.order_number})</span>
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
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="">Choose an Order</option>
                    {ordersQuery.data.map((order) => (
                      <option key={order.id} value={order.id}>
                        {order.order_number} ({new Date(order.order_date).toLocaleDateString()}) : $
                        {order.total_amount.toFixed(2)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Items in Selected Order */}
                {selectedOrder && (
                  <div className="space-y-3">
                    <label className="block text-xs font-semibold text-slate-700 uppercase">
                      Select Item to Refund
                    </label>
                    <div className="grid grid-cols-1 gap-2.5">
                      {selectedOrder.items.map((item) => {
                        const isClaimed = Boolean(item.has_active_claim);
                        const isSelected = selectedItemId === item.id;

                        return (
                          <label
                            key={item.id}
                            className={`flex items-center justify-between p-3.5 rounded-xl border transition-all ${
                              isClaimed
                                ? 'border-slate-200 bg-slate-50/70 opacity-60 cursor-not-allowed'
                                : isSelected
                                  ? 'border-emerald-600 bg-emerald-50/40 shadow-sm cursor-pointer'
                                  : 'border-slate-200 hover:bg-slate-50 cursor-pointer'
                            }`}
                          >
                            <div className="flex items-center space-x-3">
                              <input
                                type="radio"
                                name="orderItem"
                                value={item.id}
                                disabled={isClaimed}
                                checked={isSelected}
                                onChange={() => {
                                  if (!isClaimed) {
                                    setSelectedItemId(item.id);
                                    setDecisionResult(null);
                                  }
                                }}
                                className="text-emerald-600 focus:ring-emerald-500 disabled:opacity-40"
                              />
                              <div>
                                <div className="flex items-center space-x-2">
                                  <p className="text-sm font-semibold text-slate-900">
                                    {item.name || item.product_name}
                                  </p>
                                  {item.is_final_sale && (
                                    <Badge status="denied" size="sm" showIcon={false}>
                                      Final Sale
                                    </Badge>
                                  )}
                                  {isClaimed && (
                                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                                      <Clock className="w-3 h-3 text-amber-600" />
                                      <span>
                                        Claim Filed ({item.claim_status || 'Active'})
                                      </span>
                                    </span>
                                  )}
                                </div>
                                <span className="text-xs text-slate-500 capitalize">
                                  Category: {item.category}
                                </span>
                              </div>
                            </div>
                            <span className="font-bold text-sm text-slate-900">
                              ${item.price.toFixed(2)}
                            </span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Item Condition & Quantity Selection */}
                {selectedItem && !selectedItem.has_active_claim && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-100">
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
                        <option value="opened_used">Opened or Used</option>
                        <option value="damaged">Damaged or Defective on arrival</option>
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className="block text-xs font-semibold text-slate-700 uppercase">
                        Quantity to Return
                      </label>
                      <input
                        type="number"
                        min={1}
                        max={selectedItem.quantity || 1}
                        value={quantity}
                        onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value, 10) || 1))}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>
                  </div>
                )}

                {/* Step 1 Action Button */}
                <div className="pt-2">
                  <button
                    type="button"
                    disabled={!canProceedStep1}
                    onClick={() => setWizardStep(2)}
                    className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold shadow-md shadow-emerald-100 transition flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    <span>Continue to Reason & Notes</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Step 2: Reason & Explanation */}
            {wizardStep === 2 && (
              <div className="space-y-6">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                    <FileCheck className="w-5 h-5 text-emerald-600" />
                    <span>Step 2: Reason & Notes</span>
                  </h2>
                  <span className="text-xs text-slate-500">
                    {selectedItem?.name} ({quantity} item{quantity > 1 ? 's' : ''})
                  </span>
                </div>

                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-700 uppercase">
                    Reason for Refund
                  </label>
                  <select
                    value={reasonCategory}
                    onChange={(e) => setReasonCategory(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="defective">Item defective or does not function as advertised</option>
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
                      Explanation Notes (Evaluated by AI)
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
                      {explanation.length} / {EXPLANATION_MAX} characters (min {EXPLANATION_MIN})
                    </span>
                  </div>
                  <textarea
                    rows={4}
                    value={explanation}
                    onChange={(e) => setExplanation(e.target.value)}
                    placeholder="Please explain the reason for your refund in detail (at least 10 characters)..."
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
                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 space-y-1">
                  <div className="flex items-center space-x-1.5 font-semibold text-slate-700">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>Security & Prompt Injection Protection</span>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-normal">
                    Customer inputs are sanitized and analyzed by security classifiers. Claims are evaluated strictly against verified store return policies.
                  </p>
                </div>

                {/* Step 2 Actions */}
                <div className="flex items-center space-x-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setWizardStep(1)}
                    className="flex-1 py-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm transition flex items-center justify-center space-x-2"
                  >
                    <ArrowLeft className="w-4 h-4" />
                    <span>Back to Item Selection</span>
                  </button>
                  <button
                    type="button"
                    disabled={!canProceedStep2}
                    onClick={() => setWizardStep(3)}
                    className="flex-1 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm shadow-md shadow-emerald-100 transition flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    <span>Continue to Review</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Review & Submit */}
            {wizardStep === 3 && selectedOrder && selectedItem && (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    <span>Step 3: Review & Submit Claim</span>
                  </h2>
                  <span className="text-xs font-mono font-medium text-slate-500">
                    {selectedOrder.order_number}
                  </span>
                </div>

                {/* Summary Card */}
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-3 text-xs">
                  <div className="flex justify-between items-center border-b border-slate-200 pb-2">
                    <span className="text-slate-500 font-medium">Selected Order</span>
                    <span className="font-semibold text-slate-800">
                      {selectedOrder.order_number} ({new Date(selectedOrder.order_date).toLocaleDateString()})
                    </span>
                  </div>

                  <div className="flex justify-between items-center border-b border-slate-200 pb-2">
                    <span className="text-slate-500 font-medium">Returned Item</span>
                    <span className="font-semibold text-slate-800">
                      {selectedItem.name || selectedItem.product_name}
                    </span>
                  </div>

                  <div className="flex justify-between items-center border-b border-slate-200 pb-2">
                    <span className="text-slate-500 font-medium">Condition & Quantity</span>
                    <span className="font-semibold text-slate-800 capitalize">
                      {itemCondition.replace('_', ' ')} : {quantity} unit{quantity > 1 ? 's' : ''}
                    </span>
                  </div>

                  <div className="flex justify-between items-center border-b border-slate-200 pb-2">
                    <span className="text-slate-500 font-medium">Claim Reason</span>
                    <span className="font-semibold text-slate-800 capitalize">
                      {reasonCategory.replace(/_/g, ' ')}
                    </span>
                  </div>

                  <div className="border-b border-slate-200 pb-2">
                    <span className="text-slate-500 font-medium block mb-1">Your Explanation</span>
                    <p className="text-slate-700 italic bg-white p-2.5 rounded-lg border border-slate-200">
                      "{explanation.trim()}"
                    </p>
                  </div>

                  <div className="flex justify-between items-center pt-1 text-sm">
                    <span className="text-slate-700 font-bold">Estimated Refund Amount</span>
                    <span className="font-black text-emerald-700 text-base">
                      ${(selectedItem.price * quantity).toFixed(2)}
                    </span>
                  </div>
                </div>

                {refundMutation.isError && (
                  <Alert variant="error" title="Submission Error">
                    {refundMutation.error instanceof Error
                      ? refundMutation.error.message
                      : 'Could not submit your refund request.'}
                  </Alert>
                )}

                {/* Step 3 Actions */}
                <div className="flex items-center space-x-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setWizardStep(2)}
                    disabled={refundMutation.isPending}
                    className="flex-1 py-3.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm transition flex items-center justify-center space-x-2"
                  >
                    <ArrowLeft className="w-4 h-4" />
                    <span>Edit Reason & Notes</span>
                  </button>

                  <button
                    type="submit"
                    disabled={refundMutation.isPending || !isExplanationValid}
                    className="flex-1 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm shadow-md shadow-emerald-100 transition flex items-center justify-center space-x-2 disabled:opacity-50"
                  >
                    {refundMutation.isPending ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Evaluating Claim...</span>
                      </>
                    ) : (
                      <>
                        <span>Submit Claim (${(selectedItem.price * quantity).toFixed(2)})</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* Right Column: AI Decision Engine Verdict */}
        <div className="lg:col-span-5">
          <div className="sticky top-24 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-6">
            <div className="border-b border-slate-100 pb-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-600" />
                  <span>AI Decision Engine Verdict</span>
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Real time policy validation and multifactor risk determination.
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
                      {policyChecks.citations.map((citation, idx) => (
                        <li key={idx} className="flex items-start space-x-2">
                          <span className="text-emerald-600 font-bold">•</span>
                          <span>{citation}</span>
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
                        <span>Security and Risk Indicators Flagged</span>
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

                <button
                  type="button"
                  onClick={handleResetForm}
                  className="w-full py-2.5 rounded-xl border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition flex items-center justify-center space-x-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Submit Another Claim</span>
                </button>
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
                  <span>AI reasoning in progress</span>
                </div>
              </div>
            ) : (
              <div className="py-16 text-center space-y-3 text-slate-400">
                <Info className="w-12 h-12 mx-auto stroke-1 text-slate-300" />
                <p className="text-sm">
                  Complete the 3 step wizard on the left to trigger the AI decision engine.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Customer Refund History Section */}
      {customer && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <History className="w-5 h-5 text-emerald-600" />
              <h2 className="text-lg font-bold text-slate-900">Your Refund History</h2>
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
              <p className="text-sm">No refund requests found for your account.</p>
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
                          <span className="text-slate-400 text-xs">None</span>
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
