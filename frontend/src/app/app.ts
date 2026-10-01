import { Component, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

interface Passage {
  id: string;
  document_id: string;
  title: string;
  source_url: string | null;
  license: string;
  kind: 'synthetic' | 'technical';
  paragraph: number;
  text: string;
  score: number;
  source_section: string | null;
  source_locator: string | null;
  attribution: {
    authors: string[];
    publication_date: string;
    doi: string;
    license_url: string;
    copyright: string;
    changes: string;
  } | null;
}

interface Answer {
  status: 'passages_found' | 'no_matches' | 'answered' | 'insufficient_evidence';
  mode: 'local_preview' | 'openai';
  message: string;
  sections: { text: string; citation_ids: string[] }[];
  passages: Passage[];
  latency_ms: number;
  model: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
}

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly http = inject(HttpClient);
  protected question = 'Which surface inspection methods report limitations from illumination?';
  protected readonly answer = signal<Answer | null>(null);
  protected readonly pending = signal(false);
  protected readonly error = signal('');
  protected readonly mode = signal<'local_preview' | 'openai' | 'unknown'>('unknown');

  constructor() {
    this.http.get<{ mode: 'local_preview' | 'openai' }>('/api/health').subscribe({
      next: (health) => this.mode.set(health.mode),
      error: () => this.mode.set('unknown'),
    });
  }

  protected heading(status: Answer['status']): string {
    return {
      answered: 'Document-supported answer',
      insufficient_evidence: 'Insufficient evidence',
      no_matches: 'No matching passages',
      passages_found: 'Retrieved passages',
    }[status];
  }

  protected citedPassages(result: Answer, ids: string[]): Passage[] {
    return result.passages.filter((passage) => ids.includes(passage.id));
  }

  protected async ask(): Promise<void> {
    if (this.pending() || this.question.trim().length < 3) return;
    this.pending.set(true);
    this.error.set('');
    this.answer.set(null);
    try {
      const result = await firstValueFrom(
        this.http.post<Answer>('/api/ask', { question: this.question.trim() }),
      );
      this.answer.set(result);
      this.mode.set(result.mode);
    } catch (error: unknown) {
      this.error.set(
        error instanceof HttpErrorResponse && typeof error.error?.detail === 'string'
          ? error.error.detail
          : 'The request could not finish. Check that the Python server is running, then try again.',
      );
    } finally {
      this.pending.set(false);
    }
  }
}
