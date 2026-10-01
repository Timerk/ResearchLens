import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { App, type Answer } from './app';
import { responses, syntheticPassage, technicalPassage } from '../../testing/fixtures';

describe('Research question workflow', () => {
  let fixture: ComponentFixture<App>;
  let http: HttpTestingController;
  let root: HTMLElement;

  async function render() {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  }

  async function health(mode: 'openai' | 'local_preview' = 'openai') {
    http.expectOne('/api/health').flush({ status: 'ok', mode });
    await render();
  }

  async function question(value: string) {
    const input = root.querySelector('textarea')!;
    input.value = value;
    input.dispatchEvent(new Event('input'));
    await render();
  }

  function submit() {
    root
      .querySelector('form')!
      .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    fixture.detectChanges();
  }

  async function respond(answer: Answer) {
    submit();
    http.expectOne('/api/ask').flush(answer);
    await render();
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(App);
    root = fixture.nativeElement;
    await render();
  });

  afterEach(() => http.verify());

  it('labels the question and exposes connecting, active mode, and input guidance', async () => {
    expect(root.textContent).toContain('Connecting to backend');
    expect(root.querySelector('label')?.htmlFor).toBe('question');
    expect(root.querySelector('textarea')?.getAttribute('aria-describedby')).toBe(
      'question-help question-validation',
    );
    await health();
    expect(root.textContent).toContain('OpenAI · Document-only answers');
    expect(root.textContent).toContain('they do not prove factual support');
    expect(root.textContent).not.toContain('Retrieval uses word matching');
  });

  it('reports a failed health check and still permits a request', async () => {
    http.expectOne('/api/health').flush({}, { status: 503, statusText: 'Unavailable' });
    await render();
    expect(root.textContent).toContain('Backend status unavailable');
    await respond(responses.preview);
    expect(root.textContent).toContain('Local preview · No API charges');
  });

  it.each(['', '  ', 'ab', ' a ', 'x'.repeat(2001)])(
    'rejects invalid question %# without a request',
    async (value) => {
      await health();
      await question(value);
      expect(root.querySelector('textarea')?.getAttribute('aria-invalid')).toBe('true');
      expect(root.querySelector('button')?.disabled).toBe(true);
      expect(root.querySelector('button')?.getAttribute('aria-disabled')).toBe('true');
      expect(root.querySelector('#question-validation')?.textContent?.trim()).not.toBe('');
      submit(); // Exercise the handler too, bypassing the disabled button.
      http.expectNone('/api/ask');
    },
  );

  it.each(['  What limits inspection?  ', 'x'.repeat(2000)])(
    'submits only the trimmed question at valid boundaries %#',
    async (value) => {
      await health();
      await question(value);
      expect(root.querySelector('textarea')?.getAttribute('aria-invalid')).toBe('false');
      submit();
      const request = http.expectOne('/api/ask');
      expect(request.request.method).toBe('POST');
      expect(request.request.body).toEqual({ question: value.trim() });
      request.flush(responses.preview);
      await render();
    },
  );

  it('announces loading, prevents edits and duplicate submits, then allows another request', async () => {
    await health();
    await respond(responses.answered);
    submit();
    expect(root.querySelector('[role="status"]')?.textContent).toContain('Searching documents');
    expect(root.querySelector('section')?.getAttribute('aria-busy')).toBe('true');
    expect(root.querySelector('textarea')?.readOnly).toBe(true);
    expect(root.querySelector('button')?.getAttribute('aria-disabled')).toBe('true');
    expect(root.querySelector('article')).toBeNull();
    const request = http.expectOne('/api/ask');
    submit();
    submit();
    http.expectNone('/api/ask');
    request.flush(responses.preview);
    await render();
    expect(root.querySelector('textarea')?.readOnly).toBe(false);
    expect(root.querySelector('button')?.getAttribute('aria-disabled')).toBe('false');
    expect(root.querySelector('section')?.getAttribute('aria-busy')).toBe('false');
    expect(root.querySelector('[role="status"]')?.textContent).toContain(
      'Retrieved passages ready',
    );
    await respond(responses.noMatches);
  });

  it('renders the answer, cited passage, metadata and safe source links', async () => {
    await health();
    await respond(responses.answered);
    expect(root.querySelector('h2')?.textContent).toBe('Answer with source references');
    const answer = root.querySelector('article')!;
    expect(answer.textContent).toContain(responses.answered.sections[0].text);
    expect(answer.querySelector('summary')?.textContent).toContain(technicalPassage.title);
    expect(answer.querySelector('blockquote')?.textContent).toBe(technicalPassage.text);
    const reference = root.querySelectorAll('article')[1];
    expect(reference.querySelector('summary')?.getAttribute('aria-label')).toBe(
      'Inspect reference: ' + technicalPassage.title + ', paragraph 2',
    );
    expect(reference.textContent).toContain(technicalPassage.source_locator);
    expect(reference.textContent).toContain('Zijian Li, Yong Yao');
    expect(reference.textContent).toContain('2024-10-18');
    expect(reference.textContent).toContain('10.3390/s24206717');
    const links = reference.querySelectorAll('a');
    expect(Array.from(links, (a) => a.getAttribute('href'))).toEqual([
      technicalPassage.attribution!.license_url,
      technicalPassage.source_url,
    ]);
    for (const link of links) {
      expect(link.target).toBe('_blank');
      expect(link.rel).toBe('noopener noreferrer');
    }
    expect(root.textContent).toContain('mock-model · 900 input tokens ·');
    expect(root.textContent).toContain('120 output tokens (including reasoning)');
  });

  it('associates each section only with its cited passages', async () => {
    await health();
    await respond({
      ...responses.answered,
      passages: [technicalPassage, syntheticPassage],
      sections: [
        responses.answered.sections[0],
        { text: 'A synthetic example.', citation_ids: [syntheticPassage.id] },
      ],
    });
    const articles = root.querySelectorAll('article');
    expect(articles[0].querySelectorAll('details')).toHaveLength(1);
    expect(articles[0].textContent).not.toContain(syntheticPassage.title);
    expect(articles[1].textContent).toContain(syntheticPassage.title);
    expect(articles[1].textContent).not.toContain(technicalPassage.title);
  });

  it('displays API text as text rather than executable markup', async () => {
    await health();
    const text = '<img src=x onerror="alert(1)">';
    await respond({
      ...responses.answered,
      sections: [{ text, citation_ids: [technicalPassage.id] }],
    });
    expect(root.querySelector('article p')?.textContent).toBe(text);
    expect(root.querySelector('img')).toBeNull();
  });

  it('shows a local preview without generated sections or token claims', async () => {
    await health('local_preview');
    await respond({ ...responses.preview, passages: [syntheticPassage] });
    expect(root.querySelector('h2')?.textContent).toBe('Retrieved passages');
    expect(root.querySelectorAll('article')).toHaveLength(1);
    expect(root.textContent).toContain('synthetic · Paragraph 1');
    expect(root.textContent).toContain('Local synthetic fixture; no external publication');
    expect(root.querySelector('section a')).toBeNull();
    expect(root.textContent).not.toContain('input tokens');
    expect(root.textContent).toContain('this preview cannot determine whether they answer it');
  });

  it('shows no matches without evidence cards or an error alert', async () => {
    await health();
    await respond(responses.noMatches);
    expect(root.querySelector('h2')?.textContent).toBe('No matching passages');
    expect(root.textContent).toContain('This does not prove the corpus has no answer');
    expect(root.querySelector('article')).toBeNull();
    expect(root.querySelector('[role="alert"]')).toBeNull();
  });

  it('distinguishes insufficient evidence from no matches and retains inspectable passages', async () => {
    await health();
    await respond(responses.insufficient);
    expect(root.querySelector('h2')?.textContent).toBe('Insufficient evidence');
    expect(root.textContent).toContain('do not provide enough evidence');
    expect(root.querySelectorAll('article')).toHaveLength(1);
    expect(root.querySelector('summary')?.textContent?.trim()).toBe('Inspect reference');
    expect(root.querySelector('[role="alert"]')).toBeNull();
  });

  it.each([429, 503, 504])(
    'announces API detail on HTTP %i and clears it on retry',
    async (status) => {
      await health();
      await respond(responses.answered);
      submit();
      http
        .expectOne('/api/ask')
        .flush({ detail: 'Please try again later.' }, { status, statusText: 'API error' });
      await render();
      expect(root.querySelector('[role="alert"]')?.textContent).toBe('Please try again later.');
      expect(root.querySelector('article')).toBeNull();
      expect(root.querySelector('textarea')?.readOnly).toBe(false);
      submit();
      expect(root.querySelector('[role="alert"]')).toBeNull();
      http.expectOne('/api/ask').flush(responses.preview);
      await render();
      expect(root.querySelector('h2')?.textContent).toBe('Retrieved passages');
    },
  );

  it.each(['network', 'validation'])(
    'handles %s errors without rendering structured detail',
    async (kind) => {
      await health();
      submit();
      const request = http.expectOne('/api/ask');
      if (kind === 'network') request.error(new ProgressEvent('error'));
      else
        request.flush(
          { detail: [{ loc: ['body', 'question'], msg: 'Invalid question' }] },
          { status: 422, statusText: 'Invalid' },
        );
      await render();
      expect(root.querySelector('[role="alert"]')?.textContent).toContain(
        'The request could not finish',
      );
      expect(root.textContent).not.toContain('[object Object]');
      expect(root.querySelector('button')?.getAttribute('aria-disabled')).toBe('false');
    },
  );
});
