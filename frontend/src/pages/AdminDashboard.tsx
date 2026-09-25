import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowUpRight,
  Filter,
  RefreshCw,
  User,
  Search,
  Calendar,
  X,
  ArrowUpDown,
  ShieldCheck,
  ShieldAlert,
  Clock,
  BrainCircuit,
  ChevronLeft,
  ChevronRight,
  DollarSign,
  TrendingUp,
} from 'lucide-react';
import { refundApi } from '../api/refunds';
import type { RefundAdminListItem, RefundAdminDetail, RefundListParams } from '../types';

export const AdminDashboardPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Filter and pagination state
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [minRiskFilter, setMinRiskFilter] = useState<string>('all');
  const [searchInput, setSearchInput] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [pageSize, setPageSize] = useState<number>(20);
  const [currentPage, setCurrentPage] = useState<number>(0);

  // Inspection Drawer & Override Modal state
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [overrideModalOpen, setOverrideModalOpen] = useState<boolean>(false);
  const [overrideDecision, setOverrideDecision] = useState<'Approved' | 'Denied' | 'Escalated'>(
    'Approved'
  );
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [overrideError, setOverrideError] = useState<string | null>(null);

  // Debounce search input (300ms)
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchInput.trim());
      setCurrentPage(0);
    }, 300);
    return () => clearTimeout(handler);
  }, [searchInput]);

  // Reset page when filters change
  const handleStatusChange = (status: string) => {
    setFilterStatus(status);
    setCurrentPage(0);
  };

  const handleDateChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
    setCurrentPage(0);
  };

  const handleClearFilters = () => {
    setFilterStatus('all');
    setMinRiskFilter('all');
    setSearchInput('');
    setStartDate('');
    setEndDate('');
    setSortBy('created_at');
    setSortOrder('desc');
    setCurrentPage(0);
  };

  // Build query params
  const queryParams: RefundListParams = {
    decision: filterStatus !== 'all' ? filterStatus : undefined,
    min_risk_score: minRiskFilter !== 'all' ? parseFloat(minRiskFilter) : undefined,
    search: debouncedSearch || undefined,
    start_date: startDate ? new Date(startDate).toISOString() : undefined,
    end_date: endDate ? new Date(endDate).toISOString() : undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
    limit: pageSize,
    offset: currentPage * pageSize,
  };

  // Queries
  const refundsQuery = useQuery({
    queryKey: ['admin-refunds', queryParams],
    queryFn: () => refundApi.listRefundRequests(queryParams),
  });

  const statsQuery = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => refundApi.getRefundStats(),
  });

  // Query for claim detail when drawer is open
  const claimDetailQuery = useQuery({
    queryKey: ['admin-claim-detail', selectedClaimId],
    queryFn: () => (selectedClaimId ? refundApi.getRefundRequestDetail(selectedClaimId) : null),
    enabled: !!selectedClaimId,
  });

  // Override mutation
  const overrideMutation = useMutation({
    mutationFn: ({
      id,
      decision,
      reason,
    }: {
      id: string;
      decision: 'Approved' | 'Denied' | 'Escalated';
      reason: string;
    }) => refundApi.overrideDecision(id, { decision, reason, actor: 'support_lead@store.com' }),
    onSuccess: (updatedClaim) => {
      queryClient.invalidateQueries({ queryKey: ['admin-refunds'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      queryClient.setQueryData(['admin-claim-detail', updatedClaim.id], updatedClaim);
      setOverrideModalOpen(false);
      setOverrideReason('');
      setOverrideError(null);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to submit override';
      setOverrideError(msg);
    },
  });

  const handleSortToggle = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
    setCurrentPage(0);
  };

  const handleOpenOverride = (claim: RefundAdminListItem | RefundAdminDetail) => {
    setSelectedClaimId(claim.id);
    setOverrideDecision(claim.decision === 'Approved' ? 'Denied' : 'Approved');
    setOverrideReason('');
    setOverrideError(null);
    setOverrideModalOpen(true);
  };

  const handleSaveOverride = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedClaimId) return;
    if (overrideReason.trim().length < 5) {
      setOverrideError('Justification reason must be at least 5 characters.');
      return;
    }
    overrideMutation.mutate({
      id: selectedClaimId,
      decision: overrideDecision,
      reason: overrideReason.trim(),
    });
  };

  const totalRecords = refundsQuery.data?.total ?? 0;
  const totalPages = Math.ceil(totalRecords / pageSize);
  const items = refundsQuery.data?.items ?? [];
  const stats = statsQuery.data;

  // Selected claim detail for drawer
  const selectedDetail = claimDetailQuery.data;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Support Agent Refund Console
          </h1>
          <p className="text-slate-600 text-sm mt-1">
            Review automated AI refund evaluations, inspect audit logs, and provide supervisor
            overrides.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              refundsQuery.refetch();
              statsQuery.refetch();
            }}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 text-sm font-medium hover:bg-slate-50 transition shadow-sm"
            aria-label="Refresh Data"
          >
            <RefreshCw
              className={`w-4 h-4 ${refundsQuery.isFetching || statsQuery.isFetching ? 'animate-spin' : ''}`}
            />
            <span>Refresh Data</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center justify-between">
            <span>Total Claims</span>
            <Clock className="w-3.5 h-3.5 text-slate-400" />
          </span>
          <div className="text-2xl font-black text-slate-900">
            {stats ? stats.total_requests : '—'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider flex items-center justify-between">
            <span>Approval Rate</span>
            <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
          </span>
          <div className="text-2xl font-black text-emerald-700">
            {stats ? `${stats.approval_rate}%` : '—'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider flex items-center justify-between">
            <span>Approved</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          </span>
          <div className="text-2xl font-black text-emerald-700">
            {stats ? stats.approved_count : '—'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-rose-600 uppercase tracking-wider flex items-center justify-between">
            <span>Denied</span>
            <XCircle className="w-3.5 h-3.5 text-rose-500" />
          </span>
          <div className="text-2xl font-black text-rose-700">
            {stats ? stats.denied_count : '—'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-amber-600 uppercase tracking-wider flex items-center justify-between">
            <span>Escalations</span>
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
          </span>
          <div className="text-2xl font-black text-amber-700">
            {stats ? stats.escalated_count : '—'}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider flex items-center justify-between">
            <span>Refunded</span>
            <DollarSign className="w-3.5 h-3.5 text-emerald-500" />
          </span>
          <div className="text-2xl font-black text-emerald-900">
            {stats
              ? `$${stats.total_refunded_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
              : '—'}
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by customer name, email, order, or request number..."
              className="w-full pl-10 pr-9 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition"
              aria-label="Search refund claims"
            />
            {searchInput && (
              <button
                onClick={() => setSearchInput('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                aria-label="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Date range filters */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl text-xs">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <input
                type="date"
                value={startDate}
                onChange={(e) => handleDateChange(e.target.value, endDate)}
                className="bg-transparent text-slate-700 focus:outline-none"
                aria-label="Start Date"
              />
              <span className="text-slate-400">to</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => handleDateChange(startDate, e.target.value)}
                className="bg-transparent text-slate-700 focus:outline-none"
                aria-label="End Date"
              />
            </div>

            {(startDate || endDate || filterStatus !== 'all' || minRiskFilter !== 'all' || debouncedSearch) && (
              <button
                onClick={handleClearFilters}
                className="px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-xl transition"
                aria-label="Reset all filters"
              >
                Reset
              </button>
            )}
          </div>
        </div>

        {/* Status Tabs and Quick Sorter */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center space-x-1.5">
              <span className="text-xs font-bold text-slate-500 uppercase flex items-center space-x-1 mr-1">
                <Filter className="w-3.5 h-3.5" />
                <span>Status:</span>
              </span>
              {['all', 'Approved', 'Denied', 'Escalated'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => handleStatusChange(tab)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                    filterStatus === tab
                      ? 'bg-slate-900 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {tab === 'all' ? 'All Requests' : tab}
                </button>
              ))}
            </div>

            <div className="flex items-center space-x-1.5 pl-2 border-l border-slate-200">
              <span className="text-xs font-bold text-slate-500 uppercase flex items-center space-x-1 mr-1">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                <span>Risk:</span>
              </span>
              {[
                { label: 'All', val: 'all' },
                { label: 'Elevated (≥30%)', val: '0.3' },
                { label: 'High (≥70%)', val: '0.7' },
              ].map(({ label, val }) => (
                <button
                  key={val}
                  onClick={() => {
                    setMinRiskFilter(val);
                    setCurrentPage(0);
                  }}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                    minRiskFilter === val
                      ? 'bg-amber-600 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs text-slate-500">
            <span>Page Size:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(0);
              }}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs font-medium text-slate-700"
              aria-label="Page Size"
            >
              <option value={10}>10 per page</option>
              <option value={20}>20 per page</option>
              <option value={50}>50 per page</option>
            </select>
          </div>
        </div>
      </div>

      {/* Claims Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase text-slate-500 tracking-wider">
              <tr>
                <th
                  onClick={() => handleSortToggle('request_number')}
                  className="px-6 py-3.5 cursor-pointer hover:text-slate-900 select-none"
                >
                  <div className="flex items-center space-x-1">
                    <span>Claim Reference</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="px-6 py-3.5">Customer & Order</th>
                <th
                  onClick={() => handleSortToggle('created_at')}
                  className="px-6 py-3.5 cursor-pointer hover:text-slate-900 select-none"
                >
                  <div className="flex items-center space-x-1">
                    <span>Date</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th
                  onClick={() => handleSortToggle('amount')}
                  className="px-6 py-3.5 cursor-pointer hover:text-slate-900 select-none"
                >
                  <div className="flex items-center space-x-1">
                    <span>Amount</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th
                  onClick={() => handleSortToggle('risk_score')}
                  className="px-6 py-3.5 cursor-pointer hover:text-slate-900 select-none"
                >
                  <div className="flex items-center space-x-1">
                    <span>Risk & Anomalies</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th
                  onClick={() => handleSortToggle('decision')}
                  className="px-6 py-3.5 cursor-pointer hover:text-slate-900 select-none"
                >
                  <div className="flex items-center space-x-1">
                    <span>AI Verdict</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-400" />
                  </div>
                </th>
                <th className="px-6 py-3.5">Override</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {refundsQuery.isLoading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-500">
                    <div className="flex items-center justify-center space-x-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-emerald-600" />
                      <span>Loading claims data...</span>
                    </div>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-400 space-y-2">
                    <p className="font-semibold text-slate-600">No refund requests found</p>
                    <p className="text-xs">
                      Try adjusting your status filter, search terms, or date range.
                    </p>
                  </td>
                </tr>
              ) : (
                items.map((req) => (
                  <tr
                    key={req.id}
                    onClick={() => setSelectedClaimId(req.id)}
                    className={`cursor-pointer transition ${
                      selectedClaimId === req.id ? 'bg-emerald-50/50' : 'hover:bg-slate-50/80'
                    }`}
                  >
                    <td className="px-6 py-4 font-mono font-medium text-slate-900 text-xs">
                      <div>{req.request_number}</div>
                      <div className="text-[11px] text-slate-500 font-sans capitalize mt-0.5">
                        {req.reason_category.replace(/_/g, ' ')}
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900 flex items-center space-x-1">
                        <User className="w-3 h-3 text-slate-400" />
                        <span>{req.customer_name || 'Customer'}</span>
                      </div>
                      <div className="text-xs text-slate-500">
                        {req.customer_email || req.order_number || 'Order details'}
                      </div>
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-600">
                      {new Date(req.created_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </td>

                    <td className="px-6 py-4 font-semibold text-slate-900">
                      ${req.amount.toFixed(2)}
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex flex-col space-y-1">
                        <div className="flex items-center space-x-1.5">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold border ${
                              (req.risk_score ?? 0) >= 0.7
                                ? 'bg-rose-50 text-rose-700 border-rose-200'
                                : (req.risk_score ?? 0) >= 0.3
                                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                                  : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            }`}
                          >
                            {((req.risk_score ?? 0) * 100).toFixed(0)}% Risk
                          </span>
                        </div>
                        {req.anomaly_flags && req.anomaly_flags.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {req.anomaly_flags.map((flag) => (
                              <span
                                key={flag}
                                className="px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 text-[10px] font-semibold font-mono"
                              >
                                {flag === 'velocity_limit_exceeded'
                                  ? 'Velocity Spike'
                                  : flag === 'high_value_cluster'
                                    ? 'High Value'
                                    : flag === 'conflicting_claim_detected'
                                      ? 'Duplicate Claim'
                                      : flag.replace(/_/g, ' ')}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${
                          req.decision.toLowerCase() === 'approved'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : req.decision.toLowerCase() === 'denied'
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {req.decision.toLowerCase() === 'approved' && (
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        )}
                        {req.decision.toLowerCase() === 'denied' && (
                          <XCircle className="w-3.5 h-3.5" />
                        )}
                        {req.decision.toLowerCase() === 'escalated' && (
                          <AlertTriangle className="w-3.5 h-3.5" />
                        )}
                        <span className="capitalize">{req.decision}</span>
                      </span>
                    </td>

                    <td className="px-6 py-4 text-xs">
                      {req.human_override ? (
                        <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-semibold text-[11px]">
                          Supervisor
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs">—</span>
                      )}
                    </td>

                    <td
                      className="px-6 py-4 text-right space-x-2"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={() => handleOpenOverride(req)}
                        className="px-2.5 py-1 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition"
                        aria-label={`Override decision for ${req.request_number}`}
                      >
                        Override
                      </button>
                      <Link
                        to={`/admin/refunds/${req.id}`}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-semibold hover:bg-emerald-100 transition"
                        aria-label={`Audit detail for ${req.request_number}`}
                      >
                        <span>Audit</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Server Pagination Footer */}
        <div className="flex flex-col sm:flex-row items-center justify-between px-6 py-4 border-t border-slate-200 bg-slate-50 gap-3 text-xs text-slate-600">
          <div>
            Showing{' '}
            <span className="font-semibold text-slate-900">
              {totalRecords === 0 ? 0 : currentPage * pageSize + 1}
            </span>{' '}
            to{' '}
            <span className="font-semibold text-slate-900">
              {Math.min((currentPage + 1) * pageSize, totalRecords)}
            </span>{' '}
            of <span className="font-semibold text-slate-900">{totalRecords}</span> claims
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
              disabled={currentPage === 0 || refundsQuery.isLoading}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg border border-slate-200 bg-white font-medium hover:bg-slate-100 disabled:opacity-40 transition"
              aria-label="Previous Page"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>
            <span className="px-2 font-medium">
              Page {totalPages === 0 ? 1 : currentPage + 1} of {Math.max(1, totalPages)}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={currentPage >= totalPages - 1 || refundsQuery.isLoading}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg border border-slate-200 bg-white font-medium hover:bg-slate-100 disabled:opacity-40 transition"
              aria-label="Next Page"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Slide Over Inspection Drawer */}
      {selectedClaimId && (
        <div
          className="fixed inset-0 z-40 flex justify-end bg-slate-900/40 backdrop-blur-xs transition-opacity"
          onClick={() => setSelectedClaimId(null)}
          role="dialog"
          aria-modal="true"
          aria-label="Claim Inspection Drawer"
        >
          <div
            className="w-full max-w-xl bg-white h-full shadow-2xl border-l border-slate-200 flex flex-col overflow-hidden animate-in slide-in-from-right duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Drawer Header */}
            <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-sm font-bold text-slate-900">
                    {selectedDetail?.request_number || 'Claim Inspection'}
                  </span>
                  {selectedDetail && (
                    <span
                      className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                        selectedDetail.decision.toLowerCase() === 'approved'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : selectedDetail.decision.toLowerCase() === 'denied'
                            ? 'bg-rose-50 text-rose-700 border-rose-200'
                            : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}
                    >
                      <span className="capitalize">{selectedDetail.decision}</span>
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500">
                  Quick triage panel. Review reasoning without losing table context.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <Link
                  to={`/admin/refunds/${selectedClaimId}`}
                  className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 text-xs font-semibold hover:bg-emerald-100 transition"
                >
                  <span>Full View</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
                <button
                  onClick={() => setSelectedClaimId(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
                  aria-label="Close Drawer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Drawer Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {claimDetailQuery.isLoading ? (
                <div className="py-20 text-center text-slate-400 space-y-2">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-600" />
                  <p className="text-xs">Loading comprehensive claim data...</p>
                </div>
              ) : selectedDetail ? (
                <>
                  {/* Amount and Reason Overview */}
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex justify-between items-center">
                    <div>
                      <span className="text-xs text-slate-500 uppercase font-semibold">
                        Claim Amount
                      </span>
                      <div className="text-2xl font-black text-slate-900">
                        ${selectedDetail.amount.toFixed(2)}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-slate-500 uppercase font-semibold">
                        Category
                      </span>
                      <div className="text-sm font-bold text-slate-800 capitalize">
                        {selectedDetail.reason_category.replace(/_/g, ' ')}
                      </div>
                    </div>
                  </div>

                  {/* Customer Risk & Profile */}
                  <div className="space-y-3">
                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1.5">
                      <User className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Customer Context & Risk</span>
                    </h3>
                    <div className="bg-white border border-slate-200 rounded-xl p-4 text-xs space-y-2">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Customer Name:</span>
                        <span className="font-semibold text-slate-900">
                          {selectedDetail.customer?.name || '—'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Email:</span>
                        <span className="text-slate-700 font-mono">
                          {selectedDetail.customer?.email || '—'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center pt-1 border-t border-slate-100">
                        <span className="text-slate-500">Risk Score:</span>
                        <span
                          className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                            (selectedDetail.customer?.risk_score ?? 0) > 0.4
                              ? 'bg-rose-50 text-rose-700 border border-rose-200'
                              : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          }`}
                        >
                          {((selectedDetail.customer?.risk_score ?? 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Return Rate:</span>
                        <span className="font-medium text-slate-800">
                          {((selectedDetail.customer?.return_rate ?? 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Lifetime Spent:</span>
                        <span className="font-medium text-slate-800">
                          ${(selectedDetail.customer?.total_spent ?? 0).toFixed(2)} (
                          {selectedDetail.customer?.orders_count ?? 0} orders)
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* AI Outage Fallback Banner if present */}
                  {selectedDetail.error_context && (
                    <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-1">
                      <div className="font-bold flex items-center space-x-1.5">
                        <AlertTriangle className="w-4 h-4 text-amber-600" />
                        <span>AI Provider Outage Fallback</span>
                      </div>
                      <p className="text-amber-800 text-xs">
                        Automated AI decision service was unavailable during evaluation. The claim was safely persisted and escalated for supervisor review.
                      </p>
                    </div>
                  )}

                  {/* Security & Anomaly Telemetry */}
                  <div className="space-y-3">
                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1.5">
                      <ShieldAlert className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Security & Anomaly Telemetry</span>
                    </h3>
                    <div className="bg-white border border-slate-200 rounded-xl p-4 text-xs space-y-2.5">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Claim Risk Score:</span>
                        <span
                          className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                            (selectedDetail.risk_score ?? 0) >= 0.7
                              ? 'bg-rose-50 text-rose-700 border border-rose-200'
                              : (selectedDetail.risk_score ?? 0) >= 0.3
                                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          }`}
                        >
                          {((selectedDetail.risk_score ?? 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block mb-1">Anomaly Flags:</span>
                        {selectedDetail.anomaly_flags && selectedDetail.anomaly_flags.length > 0 ? (
                          <div className="space-y-1.5 pt-1">
                            {selectedDetail.anomaly_flags.map((flag) => (
                              <div
                                key={flag}
                                className="flex items-center space-x-2 bg-rose-50 border border-rose-200 text-rose-800 p-2 rounded-lg"
                              >
                                <AlertTriangle className="w-3.5 h-3.5 text-rose-600 flex-shrink-0" />
                                <div className="font-semibold text-[11px]">
                                  {flag === 'velocity_limit_exceeded' && 'Velocity Spike: 3+ claims within rolling 24 hours'}
                                  {flag === 'high_value_cluster' && 'High Value Cluster: Item > $200 or 7-day sum > $500'}
                                  {flag === 'conflicting_claim_detected' && 'Conflicting Claim: Active or approved claim on item within 30 days'}
                                  {!['velocity_limit_exceeded', 'high_value_cluster', 'conflicting_claim_detected'].includes(flag) && flag}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-emerald-700 font-medium">Clean • No anomalies detected</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Customer Explanation */}
                  <div className="space-y-2">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      Customer Explanation
                    </span>
                    <p className="text-xs text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200 leading-relaxed italic">
                      "{selectedDetail.customer_explanation}"
                    </p>
                  </div>

                  {/* AI Reasoning & Policy Evaluations */}
                  <div className="space-y-3">
                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1.5">
                      <BrainCircuit className="w-3.5 h-3.5 text-emerald-600" />
                      <span>AI Reasoning & Guardrails</span>
                    </h3>
                    <div className="bg-emerald-50/40 border border-emerald-100 rounded-xl p-4 text-xs space-y-3">
                      <div>
                        <span className="text-emerald-900 font-bold block mb-1">
                          Generated Justification:
                        </span>
                        <p className="text-slate-700 leading-relaxed">
                          {selectedDetail.decision_reason ||
                            selectedDetail.ai_reasoning ||
                            'No specific reasoning provided.'}
                        </p>
                      </div>

                      {selectedDetail.confidence_score && (
                        <div className="flex justify-between items-center pt-2 border-t border-emerald-100 text-xs">
                          <span className="text-emerald-950 font-medium">Model Confidence:</span>
                          <span className="font-bold text-emerald-900">
                            {(selectedDetail.confidence_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Policy checks matches */}
                  {selectedDetail.policy_checks && (
                    <div className="space-y-2">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Policy Check Signals</span>
                      </span>
                      <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs space-y-1.5">
                        {Array.isArray((selectedDetail.policy_checks as any).matched_rules) && (
                          <div className="flex items-start space-x-2">
                            <span className="text-slate-500 min-w-24">Rules:</span>
                            <div className="flex flex-wrap gap-1">
                              {(selectedDetail.policy_checks as any).matched_rules.map(
                                (rule: string) => (
                                  <span
                                    key={rule}
                                    className="px-2 py-0.5 bg-white border border-slate-200 rounded text-[11px] font-mono text-slate-700"
                                  >
                                    {rule}
                                  </span>
                                )
                              )}
                            </div>
                          </div>
                        )}
                        {Array.isArray((selectedDetail.policy_checks as any).triggered_red_flags) &&
                          (selectedDetail.policy_checks as any).triggered_red_flags.length > 0 && (
                            <div className="flex items-start space-x-2 pt-1">
                              <span className="text-rose-600 font-semibold min-w-24 flex items-center space-x-1">
                                <ShieldAlert className="w-3 h-3" />
                                <span>Red Flags:</span>
                              </span>
                              <div className="flex flex-wrap gap-1">
                                {(selectedDetail.policy_checks as any).triggered_red_flags.map(
                                  (flag: string) => (
                                    <span
                                      key={flag}
                                      className="px-2 py-0.5 bg-rose-50 border border-rose-200 rounded text-[11px] font-mono text-rose-700"
                                    >
                                      {flag}
                                    </span>
                                  )
                                )}
                              </div>
                            </div>
                          )}
                      </div>
                    </div>
                  )}

                  {/* Supervisor Override Banner if active */}
                  {selectedDetail.human_override && (
                    <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-1">
                      <div className="font-bold flex items-center space-x-1.5">
                        <span>Supervisor Override Applied</span>
                      </div>
                      <p className="text-amber-800">{selectedDetail.override_reason}</p>
                      <span className="text-amber-600 text-[11px] block mt-1">
                        By {selectedDetail.override_by || 'Supervisor'}
                      </span>
                    </div>
                  )}
                </>
              ) : null}
            </div>

            {/* Drawer Footer Actions */}
            {selectedDetail && (
              <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
                <button
                  onClick={() => handleOpenOverride(selectedDetail)}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-semibold hover:bg-emerald-700 transition shadow-sm"
                >
                  Manual Decision Override
                </button>
                <Link
                  to={`/admin/refunds/${selectedDetail.id}`}
                  className="text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center space-x-1"
                >
                  <span>Open Deep Audit</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Human Supervisor Override Modal */}
      {overrideModalOpen && selectedClaimId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Supervisor Override Dialog"
        >
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Supervisor Decision Override</h3>
              <button
                onClick={() => setOverrideModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
                aria-label="Close Override Modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Overrides update the automated verdict and record an immutable entry in the compliance
              audit trail.
            </p>

            {overrideError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 font-medium">
                {overrideError}
              </div>
            )}

            <form onSubmit={handleSaveOverride} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  New Decision
                </label>
                <select
                  value={overrideDecision}
                  onChange={(e) => setOverrideDecision(e.target.value as any)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="Approved">Approved</option>
                  <option value="Denied">Denied</option>
                  <option value="Escalated">Escalated</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Justification Reason (min 5 characters)
                </label>
                <textarea
                  required
                  rows={3}
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="Explain why this decision is being manually overridden..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 placeholder:text-slate-400"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setOverrideModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-300 text-xs font-medium text-slate-700 hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={overrideMutation.isPending}
                  className="px-4 py-2 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 disabled:opacity-50 transition shadow-sm"
                >
                  {overrideMutation.isPending ? 'Applying...' : 'Confirm Override'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
