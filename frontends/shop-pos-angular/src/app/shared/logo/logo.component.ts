import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-logo',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a class="brand" routerLink="/" [attr.aria-label]="'Ferti+ home'">
      <span class="brand-mark" [class.brand-mark-dark]="variant === 'dark'">
        <svg viewBox="0 0 40 40" role="img" aria-label="Ferti+ sprout"><path d="M20 30V17M20 19c-7 0-10-4-10-10 7 0 10 3 10 10Zm0 4c7 0 10-4 10-10-7 0-10 3-10 10Z" fill="white"/></svg>
      </span>
      <span class="brand-copy"><strong>Ferti+</strong><small>Smart shop manager</small></span>
    </a>
  `,
  styles: [`
    .brand{display:inline-flex;align-items:center;gap:10px;text-decoration:none;color:inherit}.brand-mark{width:42px;height:42px;border-radius:10px;background:var(--primary);display:grid;place-items:center}.brand-mark svg{width:30px}.brand-mark-dark{background:var(--surface)}.brand-mark-dark svg path{fill:var(--primary)}.brand-copy{display:flex;flex-direction:column;line-height:1}.brand-copy strong{font:800 21px/1 var(--heading-font)}.brand-copy small{font-size:10px;margin-top:5px}
  `]
})
export class LogoComponent { @Input() variant: 'light' | 'dark' = 'light'; }
