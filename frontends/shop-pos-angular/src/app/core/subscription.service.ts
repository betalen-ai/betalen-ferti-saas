import { Injectable, signal, computed } from '@angular/core';

export type SubStatus = 'TRIAL' | 'ACTIVE' | 'GRACE' | 'EXPIRED' | 'CANCELLED';

@Injectable({ providedIn: 'root' })
export class SubscriptionService {
  status = signal<SubStatus | null>(null);
  daysLeft = signal<number | null>(null);
  warning = signal<string | null>(null);
  blockedMessage = signal<string | null>(null); // set on 402, drives the modal

  banner = computed(() => {
    const s = this.status(), d = this.daysLeft();
    if (s === 'TRIAL' && d !== null && d <= 30) return { level: 'warning', text: `Free trial ends in ${d} days.` };
    if (s === 'TRIAL' && d !== null) return { level: 'info', text: `Free trial: ${d} days left.` };
    if (s === 'ACTIVE' && d !== null && d <= 15) return { level: 'warning', text: `Renewal due in ${d} days.` };
    if (s === 'GRACE') return { level: 'danger', text: 'Subscription ended. Renew soon to avoid being blocked.' };
    if (s === 'EXPIRED') return { level: 'danger', text: 'Subscription expired. Renew to continue.' };
    return null;
  });

  update(status?: string | null, days?: number | string | null, warning?: string | null) {
    if (status) this.status.set(status as SubStatus);
    if (days !== undefined && days !== null && days !== '') this.daysLeft.set(Number(days));
    this.warning.set(warning ?? null);
  }
  block(message: string) { this.blockedMessage.set(message); this.status.set('EXPIRED'); }
  clearBlock() { this.blockedMessage.set(null); }
  reset() { this.status.set(null); this.daysLeft.set(null); this.warning.set(null); this.blockedMessage.set(null); }
}