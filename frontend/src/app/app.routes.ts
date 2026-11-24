import { Routes } from '@angular/router';
import { Home } from './home/home';

export const routes: Routes = [
  { path: '', component: Home, title: 'ResearchLens: answers that cite their source passages' },
  {
    path: 'ask',
    loadComponent: () => import('./ask/ask').then((m) => m.Ask),
    title: 'Ask the papers | ResearchLens',
  },
  { path: '**', redirectTo: '' },
];
