import React, { useRef, useEffect } from "react";

/**
 * Props:
 *  - isStreaming (boolean)
 *  - onAlert (function)
 *  - captureIntervalMs (number) default 5000
 */
const WebcamFeed = ({ isStreaming, onAlert, captureIntervalMs = 5000 }) => {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);
  const lastAlertRef = useRef(""); // prevent spam alerts

  useEffect(() => {
    const startStream = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
      } catch (err) {
        console.error("Error accessing webcam:", err);
        alert("Allow camera permissions.");
      }
    };

    const stopStream = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      if (videoRef.current) videoRef.current.srcObject = null;
    };

    const sendFrameToServer = async () => {
      try {
        if (!videoRef.current) return;

        const video = videoRef.current;
        const w = video.videoWidth || 640;
        const h = video.videoHeight || 480;

        const canvas = canvasRef.current || document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, w, h);

        canvas.toBlob(async (blob) => {
          if (!blob) return;

          const token = localStorage.getItem("token"); // ✅ JWT

          const fd = new FormData();
          fd.append("frame", blob, `frame_${Date.now()}.jpg`);
          fd.append("camera_id", "camera_01"); // ✅ required

          try {
            const res = await fetch("http://localhost:8000/upload-frame", {
              method: "POST",
              headers: {
                Authorization: `Bearer ${token}`, // ✅ FIX
              },
              body: fd,
            });

            if (!res.ok) {
              console.warn("Upload failed:", res.status);
              return;
            }

            const data = await res.json();

            // ✅ Handle alert
            if (
              data?.status &&
              data.status !== "Safe" &&
              data.status !== lastAlertRef.current
            ) {
              lastAlertRef.current = data.status;
              onAlert && onAlert(data);
            }
          } catch (err) {
            console.error("Upload error:", err);
          }
        }, "image/jpeg", 0.8);
      } catch (err) {
        console.error("Frame capture error:", err);
      }
    };

    if (isStreaming) {
      startStream();

      const onLoaded = () => {
        sendFrameToServer(); // first frame
        intervalRef.current = setInterval(sendFrameToServer, captureIntervalMs);
      };

      if (videoRef.current) {
        videoRef.current.addEventListener("loadedmetadata", onLoaded);

        if (videoRef.current.readyState >= 1) {
          onLoaded();
        }
      }

      return () => {
        if (videoRef.current) {
          videoRef.current.removeEventListener("loadedmetadata", onLoaded);
        }
        stopStream();
      };
    } else {
      stopStream();
    }

    return () => stopStream();
  }, [isStreaming, captureIntervalMs, onAlert]);

  return (
    <div className="p-4 bg-gray-900 rounded-xl shadow-2xl text-center">
      <h3 className="text-xl font-semibold mb-4 text-white">
        Live Webcam Feed
      </h3>

      {isStreaming ? (
        <>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="w-full max-w-2xl border-4 border-red-500 rounded-lg"
          />
          <canvas ref={canvasRef} style={{ display: "none" }} />
        </>
      ) : (
        <div className="w-full max-w-2xl h-80 bg-gray-700 flex items-center justify-center rounded-lg">
          <p className="text-white text-lg">Video Feed Stopped</p>
        </div>
      )}
    </div>
  );
};

export default WebcamFeed;