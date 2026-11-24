import { Component, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { author } from '../shared/author';
import { SiteHeader } from '../shared/site-header';

interface Segment {
  text: string;
  marked?: boolean;
}

interface ExampleSource {
  number: number;
  section: string;
  paragraph: number;
  segments: Segment[];
}

const repository = 'https://github.com/Timerk/ResearchLens';

/**
 * Real example from the 2026-10-15 development evaluation (the run behind
 * docs/images/desktop-answer.png). Answer text and citations are verbatim; the
 * highlighted spans are added on this page to show which words support the claim.
 */
const example = {
  question: 'Why combine forward and backward lighting for aircraft glass canopy inspection?',
  answer:
    'They image the same cover under forward and backward lighting because defects can become visible under one lighting direction but not the other; using both helps avoid missed or false detections and gives a more complete basis for detection.',
  paper: 'Dual-Modal Illumination System for Defect Detection of Aircraft Glass Canopies',
  sources: [
    {
      number: 1,
      section: '5. Conclusions',
      paragraph: 57,
      segments: [
        {
          text: 'To address the issue of surface defect detection on aircraft glass canopies, where ',
        },
        {
          text: 'relying on a single-modal lighting condition often leads to missed or false detections',
          marked: true,
        },
        {
          text: ', we have proposed a dual-modal illumination system for transparent material defect detection. This system ',
        },
        {
          text: 'utilizes both forward lighting and backward lighting to capture defect images, facilitating a more comprehensive and accurate defect detection process',
          marked: true,
        },
        { text: '.' },
      ],
    },
    {
      number: 2,
      section: 'Abstract',
      paragraph: 1,
      segments: [
        {
          text: 'Defect detection in transparent materials typically relies on specific lighting conditions. However, through our work on defect detection for aircraft glass canopies, we found that using a single lighting condition often led to missed or false detections. This limitation arises from the optical properties of transparent materials, where ',
        },
        {
          text: 'certain defects only become sufficiently visible under specific lighting angles',
          marked: true,
        },
        {
          text: '. To address this issue, we developed a dual-modal illumination system that integrates both forward and backward lighting to capture defect images.',
        },
      ],
    },
  ] satisfies ExampleSource[],
};

@Component({
  selector: 'rl-home',
  imports: [RouterLink, SiteHeader],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home {
  protected readonly repository = repository;
  protected readonly author = author;
  protected readonly example = example;
  protected readonly selected = signal(0);

  protected readonly steps = [
    {
      title: 'Split the papers into passages',
      text: 'The article XML becomes 207 passages. Each one keeps its section, paragraph number and XML location, so a citation can lead back to the exact place in the paper.',
    },
    {
      title: 'Rank them against your question',
      text: 'The server picks a retrieval model that fits the free memory: Qwen3-4B, BGE-M3 or Qwen3-0.6B embeddings, or TF-IDF on small machines.',
    },
    {
      title: 'Fill a fixed reading budget',
      text: 'Top-ranked passages are added in order until 12,000 or 16,000 characters are used. Measuring by characters instead of passage count was the fix the evaluation found.',
    },
    {
      title: 'Answer, or decline',
      text: 'Every part of the answer must cite passages from that budget. The server rejects unknown or missing citations, and returns “insufficient evidence” when the passages don’t support an answer.',
    },
  ];

  protected readonly papers = [
    {
      authors: 'Li, Yao, Wen and Liu',
      year: 2024,
      title: 'Dual-Modal Illumination System for Defect Detection of Aircraft Glass Canopies',
      journal: 'Sensors 24(20)',
      doi: '10.3390/s24206717',
      paragraphs: 61,
    },
    {
      authors: 'Semitela, Pereira, Completo, Lau and Santos',
      year: 2025,
      title:
        'Improving Industrial Quality Control: A Transfer Learning Approach to Surface Defect Detection',
      journal: 'Sensors 25(2)',
      doi: '10.3390/s25020527',
      paragraphs: 50,
    },
    {
      authors: 'Yu, Xu, Wang, Zhang and Tang',
      year: 2024,
      title:
        'Balancing the Efficiency and Sensitivity of Defect Inspection of Non-Patterned Wafers with TDI-Based Dark-Field Scattering Microscopy',
      journal: 'Sensors 24(5)',
      doi: '10.3390/s24051622',
      paragraphs: 18,
    },
    {
      authors: 'Shiferaw and Yao',
      year: 2024,
      title: 'Autoencoder-Based Unsupervised Surface Defect Detection Using Two-Stage Training',
      journal: 'Journal of Imaging 10(5)',
      doi: '10.3390/jimaging10050111',
      paragraphs: 47,
    },
  ];

  protected readonly results = [
    {
      study: 'Development retrieval',
      result: 'Qwen3-4B at 12,000 and 16,000 characters meets all five retrieval targets.',
      doc: 'docs/formula-adoption-results.md',
    },
    {
      study: 'Held-out retrieval, run once',
      result:
        'Qwen3-4B meets 4 of 5 strict targets. Recall at four passages is 77.6%, short of the 80% target.',
      doc: 'docs/held-out-results.md',
    },
    {
      study: 'Answer quality, development set',
      result:
        'Answers with every required claim rise from 19 of 36 (TF-IDF, four passages) to 32 of 36 (Qwen3-4B or BGE-M3, 16,000 characters).',
      doc: 'docs/answer-quality.md',
    },
    {
      study: 'Automated answer judge',
      result:
        'Validated once against the owner’s grading, for required claims and abstention only. Application defaults stay unchanged.',
      doc: 'docs/answer-quality.md',
    },
  ];

  protected select(index: number): void {
    this.selected.set(index);
  }
}
