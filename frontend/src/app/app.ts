import { Component, ElementRef, effect, inject, signal, untracked, viewChild } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

export interface Passage {
  id: string;
  document_id: string;
  title: string;
  source_url: string | null;
  license: string;
  kind: 'synthetic' | 'technical';
  paragraph: number;
  text: string;
  // Recorded answers did not keep retrieval scores.
  score: number | null;
  source_section: string | null;
  source_locator: string | null;
  attribution: {
    authors: string[];
    publication_date: string;
    doi: string;
    license_url: string;
    copyright: string;
    changes: string;
    source_sha256: string;
  } | null;
}

export interface Replay {
  example_id: string;
  label: string;
  note: string;
  recorded: { study_id: string; recorded_on: string; model: string; configuration: string };
}

export interface Answer {
  status: 'passages_found' | 'no_matches' | 'answered' | 'insufficient_evidence';
  mode: 'local_preview' | 'openai';
  message: string;
  sections: { text: string; citation_ids: string[] }[];
  passages: Passage[];
  latency_ms: number | null;
  model: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  estimated_api_cost_usd: number | null;
  notice?: string | null;
  fallback_reason?: string | null;
  live_answers_remaining?: number | null;
  replay?: Replay | null;
}

export interface Example {
  id: string;
  title: string;
  question: string;
  label: string;
}

export interface DemoStatus {
  live_answers: 'enabled' | 'demo_only' | 'not_configured';
  visitor_daily_limit: number;
  global_daily_limit: number;
  visitor_remaining: number | null;
  remaining_today: number | null;
  visitor_keys: boolean;
  turnstile_site_key: string | null;
  examples: Example[];
}

interface Turnstile {
  render(container: HTMLElement, options: Record<string, unknown>): string;
  reset(widget: string): void;
}

const TURNSTILE_SCRIPT = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';

/** A 403/429 body that carries the free preview instead of a live answer. */
function fallbackAnswer(error: unknown): Answer | null {
  const body = error instanceof HttpErrorResponse ? error.error : null;
  return body && typeof body.status === 'string' && Array.isArray(body.passages) ? body : null;
}

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css', './demo.css'],
})
export class App {
  private readonly http = inject(HttpClient);
  private readonly turnstileHost = viewChild<ElementRef<HTMLElement>>('turnstile');
  private turnstileWidget: string | null = null;
  private turnstileToken = '';
  protected question = 'Which surface inspection methods report limitations from illumination?';
  // Held in memory for this tab only; never written to storage.
  protected visitorKey = '';
  protected readonly answer = signal<Answer | null>(null);
  protected readonly pending = signal(false);
  protected readonly error = signal('');
  protected readonly demo = signal<DemoStatus | null>(null);
  protected readonly mode = signal<'local_preview' | 'openai' | 'connecting' | 'unknown'>(
    'connecting',
  );

  constructor() {
    this.http.get<{ mode: 'local_preview' | 'openai' }>('/api/health').subscribe({
      next: (health) => this.mode.set(health.mode),
      error: () => this.mode.set('unknown'),
    });
    // Older backends have no demo endpoint; the app then works exactly as before.
    this.http.get<DemoStatus>('/api/demo').subscribe({
      next: (status) => this.demo.set(status),
      error: () => this.demo.set(null),
    });
    // The widget host appears once the demo status has rendered.
    effect(() => {
      const siteKey = this.demo()?.turnstile_site_key;
      const host = this.turnstileHost()?.nativeElement;
      if (siteKey && host) untracked(() => this.renderTurnstile(siteKey, host));
    });
  }

  protected heading(status: Answer['status']): string {
    return {
      answered: 'Answer with source references',
      insufficient_evidence: 'Insufficient evidence',
      no_matches: 'No matching passages',
      passages_found: 'Retrieved passages',
    }[status];
  }

  protected citedPassages(result: Answer, ids: string[]): Passage[] {
    return result.passages.filter((passage) => ids.includes(passage.id));
  }

  protected citationNumber(result: Answer, id: string): number {
    return result.passages.findIndex((passage) => passage.id === id) + 1;
  }

  /** Whether the next question can get a generated answer. */
  protected answersAvailable(): boolean {
    if (this.usingVisitorKey()) return true;
    const status = this.demo();
    const exhausted =
      status?.live_answers === 'enabled' &&
      (status.visitor_remaining === 0 || status.remaining_today === 0);
    return this.mode() === 'openai' && !exhausted;
  }

  protected usingVisitorKey(): boolean {
    return !!this.demo()?.visitor_keys && this.visitorKey.trim().length > 0;
  }

  protected questionError(): string {
    const length = this.question.trim().length;
    if (length < 3) return 'Enter at least 3 characters, excluding surrounding spaces.';
    if (length > 2000) return 'Use no more than 2,000 characters.';
    return '';
  }

  protected async replayExample(example: Example): Promise<void> {
    if (this.pending()) return;
    this.question = example.question;
    await this.run(() =>
      firstValueFrom(this.http.get<Answer>(`/api/examples/${encodeURIComponent(example.id)}`)),
    );
  }

  protected async ask(): Promise<void> {
    if (this.pending() || this.questionError()) return;
    const body: { question: string; turnstile_token?: string } = {
      question: this.question.trim(),
    };
    if (this.turnstileToken && !this.usingVisitorKey()) body.turnstile_token = this.turnstileToken;
    const headers = this.usingVisitorKey()
      ? new HttpHeaders({ 'X-OpenAI-API-Key': this.visitorKey.trim() })
      : undefined;
    await this.run(() => firstValueFrom(this.http.post<Answer>('/api/ask', body, { headers })));
    this.resetTurnstile();
  }

  private async run(request: () => Promise<Answer>): Promise<void> {
    this.pending.set(true);
    this.error.set('');
    this.answer.set(null);
    try {
      this.show(await request());
    } catch (error: unknown) {
      const fallback = fallbackAnswer(error);
      if (fallback) {
        this.show(fallback);
      } else {
        this.error.set(
          error instanceof HttpErrorResponse && typeof error.error?.detail === 'string'
            ? error.error.detail
            : 'The request could not finish. Check that the Python server is running, then try again.',
        );
      }
    } finally {
      this.pending.set(false);
    }
  }

  private show(result: Answer): void {
    this.answer.set(result);
    // Replays, fallbacks and visitor-key answers say nothing about the server's own mode.
    if (!result.replay && !result.fallback_reason && !this.usingVisitorKey()) {
      this.mode.set(result.mode);
    }
    const remaining = result.live_answers_remaining;
    const demo = this.demo();
    if (demo && typeof remaining === 'number') {
      this.demo.set({ ...demo, visitor_remaining: remaining });
    }
  }

  private renderTurnstile(siteKey: string, host: HTMLElement): void {
    if (this.turnstileWidget !== null || host.dataset['loading']) return;
    host.dataset['loading'] = 'true';
    const render = () => {
      const turnstile = (window as unknown as { turnstile?: Turnstile }).turnstile;
      if (!turnstile) return;
      this.turnstileWidget = turnstile.render(host, {
        sitekey: siteKey,
        action: 'ask',
        callback: (token: string) => (this.turnstileToken = token),
        'expired-callback': () => (this.turnstileToken = ''),
        'error-callback': () => (this.turnstileToken = ''),
      });
    };
    const script = document.createElement('script');
    script.src = TURNSTILE_SCRIPT;
    script.async = true;
    script.onload = render;
    document.head.appendChild(script);
  }

  private resetTurnstile(): void {
    // Tokens are single use; request a fresh one for the next live question.
    this.turnstileToken = '';
    const turnstile = (window as unknown as { turnstile?: Turnstile }).turnstile;
    if (turnstile && this.turnstileWidget !== null) turnstile.reset(this.turnstileWidget);
  }
}
