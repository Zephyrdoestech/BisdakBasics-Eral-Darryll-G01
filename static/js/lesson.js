let activeAudio = null;
const audioStatus = document.querySelector("[data-audio-status]");

document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-play-audio]");
  if (!button) return;

  const audio = document.getElementById(button.dataset.playAudio);
  if (!audio) return;

  if (activeAudio && activeAudio !== audio) {
    activeAudio.pause();
  }
  activeAudio = audio;

  audio.onended = () => {
    if (audioStatus) audioStatus.textContent = "Audio finished. Listen again or try saying the phrase.";
  };

  try {
    await audio.play();
    if (audioStatus) audioStatus.textContent = "Playing native-speaker audio.";
  } catch {
    if (audioStatus) audioStatus.textContent = "Audio could not be played. Please try again.";
  }
});

const recordingPanel = document.querySelector("[data-recording-panel]");
if (recordingPanel) {
  const startButton = recordingPanel.querySelector("[data-start-recording]");
  const stopButton = recordingPanel.querySelector("[data-stop-recording]");
  const replayButton = recordingPanel.querySelector("[data-replay-recording]");
  const status = recordingPanel.querySelector("[data-record-status]");
  const playback = recordingPanel.querySelector("[data-recorded-audio]");
  const csrfInput = recordingPanel.querySelector("[name=csrfmiddlewaretoken]");
  const practicedCountEl = document.getElementById("practiced-count");
  const phraseCountEl = document.getElementById("phrase-count");
  const practiceProgressEl = document.getElementById("practice-progress");
  const progressBar = document.querySelector("[role=progressbar]");
  let mediaRecorder;
  let microphoneStream;
  let recordingUrl;

  startButton.addEventListener("click", async () => {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      status.textContent = "This browser does not support audio recording. Try a recent browser on a secure connection.";
      return;
    }
    try {
      microphoneStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks = [];
      mediaRecorder = new MediaRecorder(microphoneStream);
      mediaRecorder.addEventListener("dataavailable", (event) => {
        if (event.data.size) chunks.push(event.data);
      });
      mediaRecorder.addEventListener("stop", async () => {
        const recording = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
        if (recordingUrl) URL.revokeObjectURL(recordingUrl);
        recordingUrl = URL.createObjectURL(recording);
        playback.src = recordingUrl;
        replayButton.disabled = false;
        microphoneStream.getTracks().forEach((track) => track.stop());
        stopButton.hidden = true;
        startButton.hidden = false;
        status.textContent = "Recording saved on this device. It was not uploaded.";
        await savePractice();
      });
      mediaRecorder.start();
      startButton.hidden = true;
      stopButton.hidden = false;
      replayButton.disabled = true;
      status.textContent = "Recording… say the phrase naturally, then stop when you are ready.";
    } catch (error) {
      status.textContent = error.name === "NotAllowedError"
        ? "Microphone access was denied. Allow microphone access in your browser to record."
        : "The microphone could not be started. Check your device and try again.";
      microphoneStream?.getTracks().forEach((track) => track.stop());
    }
  });

  stopButton.addEventListener("click", () => {
    if (mediaRecorder?.state === "recording") mediaRecorder.stop();
  });

  replayButton.addEventListener("click", async () => {
    if (!playback.src) return;
    if (activeAudio && activeAudio !== playback) {
      activeAudio.pause();
    }
    activeAudio = playback;
    try {
      await playback.play();
      status.textContent = "Playing your recording on this device.";
    } catch {
      status.textContent = "Your recording could not be replayed. Record the phrase again.";
    }
  });

  async function savePractice() {
    try {
      const response = await fetch(recordingPanel.dataset.practiceUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-CSRFToken": csrfInput.value,
          "Accept": "application/json",
        },
      });
      if (!response.ok) throw new Error("Practice could not be saved");
      const result = await response.json();
      if (practicedCountEl) practicedCountEl.textContent = result.practiced_count;
      if (phraseCountEl) phraseCountEl.textContent = result.phrase_count;
      if (practiceProgressEl) practiceProgressEl.style.width = `${result.progress_percent}%`;
      if (progressBar) progressBar.setAttribute("aria-valuenow", result.progress_percent);
      status.textContent = "Practice progress saved. Your recording remains on this device only.";
    } catch {
      status.textContent = "Your recording is ready to replay, but practice progress could not be saved. Check your connection and record again.";
    }
  }

  window.addEventListener("beforeunload", () => {
    if (recordingUrl) URL.revokeObjectURL(recordingUrl);
    microphoneStream?.getTracks().forEach((track) => track.stop());
  });
}
