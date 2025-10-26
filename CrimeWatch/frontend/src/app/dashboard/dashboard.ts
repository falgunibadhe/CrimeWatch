import { Component, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, HttpClientModule],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class DashboardComponent implements OnDestroy {
  @ViewChild('liveVideo', { static: false }) liveVideoRef!: ElementRef<HTMLVideoElement>;

  isLive = false;
  mediaStream: MediaStream | null = null;
  currentTime: string = '';
  private timeInterval: any = null;
  private liveUploadInterval: any = null;

  // FastAPI backend endpoint
  private backendUrl = 'http://localhost:8000/upload-video/';

  constructor(private http: HttpClient) {}

  /** ------------ Start Live Video ------------ **/
  async startLiveVideo() {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      const videoElem = this.liveVideoRef.nativeElement;
      videoElem.srcObject = this.mediaStream;

      this.isLive = true;
      this.startTimestamp();

      // Start uploading snapshots every 2 seconds
      this.liveUploadInterval = setInterval(() => this.uploadLiveFrame(), 2000);
    } catch (err) {
      console.error('Could not start live video:', err);
    }
  }

  /** ------------ Stop Live Video ------------ **/
  stopLiveVideo() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    this.isLive = false;
    this.stopTimestamp();

    if (this.liveUploadInterval) {
      clearInterval(this.liveUploadInterval);
      this.liveUploadInterval = null;
    }
  }

  /** ------------ Timestamp Logic ------------ **/
  private startTimestamp() {
    this.updateTime();
    this.timeInterval = setInterval(() => this.updateTime(), 1000);
  }

  private stopTimestamp() {
    if (this.timeInterval) {
      clearInterval(this.timeInterval);
      this.timeInterval = null;
    }
    this.currentTime = '';
  }

  private updateTime() {
    const now = new Date();
    const h = now.getHours().toString().padStart(2, '0');
    const m = now.getMinutes().toString().padStart(2, '0');
    const s = now.getSeconds().toString().padStart(2, '0');
    this.currentTime = `${h}:${m}:${s}`;
  }

  /** ------------ Upload Live Frame to Backend ------------ **/
  private uploadLiveFrame() {
    if (!this.liveVideoRef || !this.liveVideoRef.nativeElement) return;

    const video = this.liveVideoRef.nativeElement;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (blob) {
        const formData = new FormData();
        formData.append('video', new File([blob], `live_frame_${Date.now()}.png`, { type: 'image/png' }));

        // Send to FastAPI silently
        this.http.post(this.backendUrl, formData).subscribe({
          next: (res) => console.log('Live frame uploaded:', res),
          error: (err) => console.error('Live frame upload failed:', err)
        });
      }
    }, 'image/png');
  }

  ngOnDestroy() {
    this.stopLiveVideo();
  }
}
