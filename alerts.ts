import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';   

@Component({
  selector: 'app-alerts',
  standalone: true,
  imports: [CommonModule],                       
  templateUrl: './alerts.html',
  styleUrls: ['./alerts.css']
})
export class AlertsComponent {
  alerts = [
    { time: '12:35 PM', location: 'Station Road', type: 'Weapon Detected', status: 'Unresolved' },
    { time: '01:10 PM', location: 'City Mall', type: 'Violence Detected', status: 'Resolved' },
    { time: '02:05 PM', location: 'Bus Stop', type: 'Suspicious Activity', status: 'Unresolved' }
  ];
}
