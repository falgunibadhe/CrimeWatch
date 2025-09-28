

// import { Routes } from '@angular/router';
// import { DashboardComponent } from './dashboard/dashboard';
// import { AlertsComponent } from './alerts/alerts';

// export const routes: Routes = [
//   { path: 'dashboard', component: DashboardComponent },
//   { path: 'alerts', component: AlertsComponent },
//   { path: '', redirectTo: '/dashboard', pathMatch: 'full' }
 
// ];



import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'dashboard',
    loadComponent: () => import('./dashboard/dashboard').then(m => m.DashboardComponent)
  },
  {
    path: 'alerts',
    loadComponent: () => import('./alerts/alerts').then(m => m.AlertsComponent)
  },
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' }
];
