// import { PaymentAllocation } from '../models/shop.models';

import { PaymentAllocation } from "../models";

export interface CreditTotal {
  principal: number;
  interest: number;
  total: number;
  balance: number;
}

export interface UnpaidBill {
  billId: string;
  date: string;
  interestDue: number;
  principalDue: number;
}

export function calcSpotTotal(subtotal: number, discount: number, discountType: 'amount' | 'percent' = 'amount'): number {
  const validSubtotal = Math.max(0, subtotal);
  const requestedDiscount = discountType === 'percent' ? validSubtotal * Math.max(0, discount) / 100 : Math.max(0, discount);
  return Math.round(Math.max(0, validSubtotal - Math.min(validSubtotal, requestedDiscount)));
}

export function calcCreditTotal(subtotal: number, monthlyRatePct: number, months: number, paidNow = 0): CreditTotal {
  const validSubtotal = Math.max(0, subtotal);
  const principal = Math.max(0, validSubtotal - Math.min(validSubtotal, Math.max(0, paidNow)));
  const interest = Math.round(principal * Math.max(0, monthlyRatePct) / 100 * Math.max(0, months));
  const total = Math.round(validSubtotal + interest);
  return { principal, interest, total, balance: Math.max(0, total - Math.max(0, paidNow)) };
}

export function monthsBetween(start: Date | string, end: Date | string): number {
  const startTime = new Date(start).getTime();
  const endTime = new Date(end).getTime();
  if (!Number.isFinite(startTime) || !Number.isFinite(endTime) || endTime <= startTime) return 0;
  const months = (endTime - startTime) / (1000 * 60 * 60 * 24 * 30);
  return Math.round(months * 10) / 10;
}

export function allocatePayment(amount: number, bills: UnpaidBill[]): PaymentAllocation[] {
  let remaining = Math.max(0, amount);
  const allocations: PaymentAllocation[] = [];
  const oldestFirst = [...bills].sort((a, b) => a.date.localeCompare(b.date));
  for (const bill of oldestFirst) {
    if (remaining <= 0) break;
    const interestPaid = Math.min(remaining, Math.max(0, bill.interestDue));
    remaining -= interestPaid;
    const principalPaid = Math.min(remaining, Math.max(0, bill.principalDue));
    remaining -= principalPaid;
    const allocated = interestPaid + principalPaid;
    if (allocated > 0) allocations.push({ billId: bill.billId, interestPaid, principalPaid, amount: allocated });
  }
  return allocations;
}
