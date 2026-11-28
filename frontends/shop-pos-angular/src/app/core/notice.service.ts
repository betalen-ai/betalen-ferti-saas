import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class NoticeService {
  readonly message = signal('');
  private timer?: ReturnType<typeof setTimeout>;

  show(text: string, durationMs = 3200): void {
    this.message.set(text);
    if (this.timer) clearTimeout(this.timer);
    this.timer = setTimeout(() => this.message.set(''), durationMs);
  }

  clear(): void {
    if (this.timer) clearTimeout(this.timer);
    this.message.set('');
  }
}
