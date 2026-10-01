import type { Answer, Passage } from '../src/app/app';

// Presentation fixtures matching backend/researchlens/models.py on main.
// These are mocked UI examples, not an evaluation dataset or scientific findings.
export const technicalPassage: Passage = {
  id: 'pmc11510794:p2:w0',
  document_id: 'pmc11510794',
  title: 'Dual-Modal Illumination System for Defect Detection of Aircraft Glass Canopies',
  source_url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11510794/',
  license: 'CC-BY-4.0',
  kind: 'technical',
  paragraph: 2,
  text: 'Mock passage: forward and backward illumination reveal different defect features under the reported experimental conditions.',
  score: 0.42,
  source_section: 'Introduction',
  source_locator: './body/sec[1]/p[1]',
  attribution: {
    authors: ['Zijian Li', 'Yong Yao', 'Runyuan Wen', 'Qiyang Liu'],
    publication_date: '2024-10-18',
    doi: '10.3390/s24206717',
    license_url: 'https://creativecommons.org/licenses/by/4.0/',
    copyright: '© 2024 by the authors.',
    changes: 'Mock display text. Production extraction omits figures, tables and formulas.',
    source_sha256: '31f8405e3cd752a53e1b30247defef69104a562ad312052d68ce72fef1f1df24',
  },
};

export const syntheticPassage: Passage = {
  id: 'surface-fixture:p1:w0',
  document_id: 'surface-fixture',
  title: 'Surface inspection test fixture',
  source_url: null,
  license: 'CC0-1.0',
  kind: 'synthetic',
  paragraph: 1,
  text: 'Synthetic fixture: illumination changes may affect inspection results.',
  score: 0.2,
  source_section: null,
  source_locator: null,
  attribution: null,
};

const preview: Answer = {
  status: 'passages_found',
  mode: 'local_preview',
  message:
    'These passages share terms with your question. Review them below; this preview cannot determine whether they answer it.',
  sections: [],
  passages: [technicalPassage],
  latency_ms: 12.5,
  model: null,
  input_tokens: null,
  output_tokens: null,
  estimated_api_cost_usd: 0,
};

export const responses = {
  preview,
  answered: {
    ...preview,
    status: 'answered',
    mode: 'openai',
    message: 'Answer based on the supplied passages.',
    sections: [
      {
        text: 'Mock answer: the two illumination directions reveal different defect features.',
        citation_ids: [technicalPassage.id],
      },
    ],
    model: 'mock-model',
    input_tokens: 900,
    output_tokens: 120,
    estimated_api_cost_usd: null,
  },
  noMatches: {
    ...preview,
    status: 'no_matches',
    message:
      'No matching passages were found. This does not prove the corpus has no answer: lexical search can miss synonyms.',
    passages: [],
  },
  insufficient: {
    ...preview,
    status: 'insufficient_evidence',
    mode: 'openai',
    message: 'The retrieved passages do not provide enough evidence to answer this question.',
    model: 'mock-model',
    input_tokens: 800,
    output_tokens: 40,
    estimated_api_cost_usd: null,
  },
} satisfies Record<string, Answer>;
