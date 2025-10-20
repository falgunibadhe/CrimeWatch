// import { Component } from '@angular/core';

// @Component({
//   selector: 'app-dashboard',
//   standalone: true,
//   templateUrl: './dashboard.html',
//   styleUrls: ['./dashboard.css']
// })

// export class DashboardComponent {
//   latestAlert = {
//     time: '12:35 PM',
//     location: 'Station Road',
//     type: 'Weapon Detected',
//     status: 'Unresolved'
//   };

//   selectedVideo: File | null = null;
//   uploadedVideoUrl: string | null = null;
//   isLive: boolean = false;
//   mediaStream: MediaStream | null = null;

//   onVideoSelected(event: Event) {
//     const input = event.target as HTMLInputElement;
//     if (input.files && input.files.length > 0) {
//       this.selectedVideo = input.files[0];
//       this.uploadedVideoUrl = URL.createObjectURL(this.selectedVideo);
//     }
//   }

//   uploadVideo() {
//     // Here you would send the video to your backend
//     alert('Video uploaded: ' + (this.selectedVideo?.name || ''));
//   }

//   async startLiveVideo() {
//     if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
//       try {
//         this.mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
//         const videoElem = document.querySelector('video#liveVideo') as HTMLVideoElement;
//         if (videoElem) {
//           videoElem.srcObject = this.mediaStream;
//         }
//         this.isLive = true;
//       } catch (err) {
//         alert('Could not start live video: ' + err);
//       }
//     }
//   }

//   stopLiveVideo() {
//     if (this.mediaStream) {
//       this.mediaStream.getTracks().forEach(track => track.stop());
//       this.mediaStream = null;
//     }
//     const videoElem = document.querySelector('video#liveVideo') as HTMLVideoElement;
//     if (videoElem) {
//       videoElem.srcObject = null;
//     }
//     this.isLive = false;
//   }
// }


import { Component, ViewChild, ElementRef } from '@angular/core';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class DashboardComponent {
  @ViewChild('liveVideo', { static: false }) liveVideoRef!: ElementRef<HTMLVideoElement>;

  latestAlert = {
    time: '12:35 PM',
    location: 'Station Road',
    type: 'Weapon Detected',
    status: 'Unresolved'
  };

  selectedVideo: File | null = null;
  uploadedVideoUrl: string | null = null;
  isLive: boolean = false;
  mediaStream: MediaStream | null = null;

  onVideoSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedVideo = input.files[0];
      this.uploadedVideoUrl = URL.createObjectURL(this.selectedVideo);
    }
  }

  uploadVideo() {
    alert('Video uploaded: ' + (this.selectedVideo?.name || ''));
  }

  async startLiveVideo() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        if (this.liveVideoRef && this.liveVideoRef.nativeElement) {
          this.liveVideoRef.nativeElement.srcObject = this.mediaStream;
        }
        this.isLive = true;
      } catch (err) {
        alert('Could not start live video: ' + err);
      }
    }
  }
//stop live stream
  stopLiveVideo() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    if (this.liveVideoRef && this.liveVideoRef.nativeElement) {
      this.liveVideoRef.nativeElement.srcObject = null;
    }
    this.isLive = false;
  }
}

