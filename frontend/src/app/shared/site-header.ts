import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

/** Shared top bar. Pages project their own navigation or status into it. */
@Component({
  selector: 'rl-site-header',
  imports: [RouterLink],
  template: `
    <header class="bar">
      <a class="brand" routerLink="/">
        <svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
          <rect class="brand-tile" width="32" height="32" rx="3" />
          <circle class="brand-lens" cx="16" cy="16" r="9.5" />
          <rect class="brand-mark-line" x="4" y="13.5" width="24" height="5" rx="1" />
        </svg>
        ResearchLens
      </a>
      <div class="bar-end"><ng-content /></div>
    </header>
  `,
  styles: `
    :host {
      display: block;
      color: var(--bar-ink, var(--ink));
    }
    .bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px 24px;
      flex-wrap: wrap;
      max-width: var(--measure);
      margin: auto;
      padding: 18px var(--gutter);
    }
    .brand {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      color: inherit;
      font-size: 1.125rem;
      font-weight: 700;
      font-stretch: var(--narrow);
      letter-spacing: 0.005em;
      text-decoration: none;
      border-radius: 2px;
    }
    .brand-mark {
      width: 28px;
      height: 28px;
      flex: none;
    }
    .brand-tile {
      fill: var(--bar-tile, var(--field));
    }
    .brand-lens {
      fill: none;
      stroke: var(--bar-lens, #fff);
      stroke-width: 2.2;
    }
    .brand-mark-line {
      fill: var(--mark);
    }
    .bar-end {
      display: flex;
      align-items: center;
      gap: 8px 24px;
      flex-wrap: wrap;
    }
  `,
})
export class SiteHeader {}
