import { Component } from '@angular/core';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})

export class DashboardComponent {
  latestAlert = {
    time: '12:35 PM',
    location: 'Station Road',
    type: 'Weapon Detected',
    status: 'Unresolved'
  };
}
