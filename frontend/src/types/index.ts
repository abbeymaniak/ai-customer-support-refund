export type DecisionType = 'Approved' | 'Denied' | 'Escalated' | 'pending';

export interface Customer {
  id: string;
  email: string;
  name: string;
  total_spent: number;
  orders_count: number;
  refunds_count: number;
  return_rate: number;
  risk_score: number;
  account_created_at: string;
}

export interface OrderItem {
  id: string;
  name: string;
  product_name?: string;
  price: number;
  category: string;
  condition?: string;
  quantity?: number;
  is_final_sale?: boolean;
}

export interface Order {
  id: string;
  customer_id: string;
  order_number: string;
  order_date: string;
  delivered_date?: string;
  delivery_date?: string;
  total_amount: number;
  currency: string;
  status: string;
  items: OrderItem[];
}

export interface PolicyCheckResult {
  rule_id: string;
  rule_name: string;
  passed: boolean;
  message?: string;
}

export interface RefundRequest {
  id: string;
  request_number?: string;
  customer_id: string;
  order_id: string;
  item_id?: string;
  item_name?: string;
  amount: number;
  total_refund_amount?: number;
  currency: string;
  reason_category: string;
  customer_explanation: string;
  status?: string;
  decision: DecisionType;
  decision_reason?: string;
  confidence_score?: number;
  policy_checks?: {
    matched_rules?: string[];
    triggered_red_flags?: string[];
    reasons?: string[];
    citations?: string[];
  } | Record<string, unknown>;
  llm_audit_data?: Record<string, unknown>;
  human_override: boolean;
  override_reason?: string;
  override_by?: string;
  created_at: string;
  updated_at: string;
  customer?: Customer;
  order?: Order;
  refund_items?: Array<{
    id: string;
    order_item_id: string;
    quantity: number;
    refund_amount: number;
    item_condition: string;
  }>;
}

export interface AuditLog {
  id: string;
  refund_request_id?: string;
  action: string;
  actor: string;
  details: Record<string, unknown>;
  timestamp: string;
}

export interface RefundSubmissionPayload {
  customer_email: string;
  order_number: string;
  item_id: string;
  amount: number;
  reason_category: string;
  customer_explanation: string;
  quantity?: number;
  item_condition?: string;
}

