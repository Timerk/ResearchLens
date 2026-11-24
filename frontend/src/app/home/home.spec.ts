import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Home } from './home';

describe('Landing page', () => {
  let fixture: ComponentFixture<Home>;
  let root: HTMLElement;

  async function render() {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Home],
      providers: [provideRouter([])],
    }).compileComponents();
    fixture = TestBed.createComponent(Home);
    root = fixture.nativeElement;
    await render();
  });

  it('states what the product does and links to the question page', () => {
    expect(root.querySelector('h1')?.textContent).toContain('passage it came from');
    const links = Array.from(root.querySelectorAll('a'), (a) => a.getAttribute('href'));
    expect(links).toContain('/ask');
    expect(links.some((href) => href?.startsWith('/ask?q='))).toBe(true);
  });

  it('switches the example source when a citation is chosen', async () => {
    const [first, second] = Array.from(root.querySelectorAll<HTMLButtonElement>('button.cite'));
    const source = () => root.querySelector('#example-source')!.textContent!;
    expect(first.getAttribute('aria-pressed')).toBe('true');
    expect(source()).toContain('5. Conclusions, paragraph 57');
    second.click();
    await render();
    expect(second.getAttribute('aria-pressed')).toBe('true');
    expect(first.getAttribute('aria-pressed')).toBe('false');
    expect(source()).toContain('Abstract, paragraph 1');
    expect(root.querySelector('#example-source mark')?.textContent).toContain(
      'certain defects only become sufficiently visible',
    );
  });

  it('lists the four papers with DOI links and the evaluation results', () => {
    expect(root.querySelectorAll('.papers li')).toHaveLength(4);
    const doi = root.querySelector<HTMLAnchorElement>('.papers a')!;
    expect(doi.href).toBe('https://doi.org/10.3390/s24206717');
    expect(doi.rel).toBe('noopener noreferrer');
    expect(root.querySelectorAll('.results tbody tr')).toHaveLength(4);
    expect(root.textContent).toContain('77.6%');
  });
});
