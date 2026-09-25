import { Component, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
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
}

interface Answer {
  status: 'passages_found' | 'no_matches';
  mode: 'local_preview';
  message: string;
  passages: Passage[];
  latency_ms: number;
  estimated_api_cost_usd: number;
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

  protected async ask(): Promise<void> {
    if (this.pending() || this.question.trim().length < 3) return;
    this.pending.set(true);
    this.error.set('');
    this.answer.set(null);
    try {
      this.answer.set(await firstValueFrom(
        this.http.post<Answer>('/api/ask', { question: this.question.trim() }),
      ));
    } catch {
      this.error.set('Search could not finish. Check that the Python server is running, then try again.');
    } finally {
      this.pending.set(false);
    }
  }
}
