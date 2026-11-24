import { Component, DOCUMENT, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  template: '<router-outlet />',
})
export class App {
  constructor() {
    const document = inject(DOCUMENT);
    // index.html carries the public origin (set from SITE_ADDRESS in production); keep the
    // canonical link and og:url on that origin but follow the current route, without the query.
    inject(Router)
      .events.pipe(
        filter((event) => event instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe((event) => {
        const canonical = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
        if (!canonical) return;
        const url = new URL(event.urlAfterRedirects.split(/[?#]/)[0], canonical.href).href;
        canonical.href = url;
        document.querySelector('meta[property="og:url"]')?.setAttribute('content', url);
      });
  }
}
