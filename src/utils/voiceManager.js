  class VoiceManager {
  constructor() {
    this.synthesis = window.speechSynthesis;
    this.recognition = null;
    this.isListening = false;
    this.voices = [];
    
    // Initialize Speech Recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false; // Set to true for continuous listening
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US';
    }
  }

  // --- TTS Methods ---

  getVoices() {
    return new Promise((resolve) => {
      let voices = this.synthesis.getVoices();
      if (voices.length) {
        this.voices = voices;
        resolve(voices);
      } else {
        this.synthesis.onvoiceschanged = () => {
          voices = this.synthesis.getVoices();
          this.voices = voices;
          resolve(voices);
        };
      }
    });
  }

  speak(text, voiceName = null, rate = 1.0, pitch = 1.0) {
    if (!this.synthesis) {
        console.warn("SpeechSynthesis API not available");
        return;
    }

    this.cancel(); // Stop any current speech (Barge-in)
    
    const utterance = new SpeechSynthesisUtterance(text);
    this.currentUtterance = utterance; // Prevent garbage collection
    
    utterance.rate = rate;
    utterance.pitch = pitch;
    
    utterance.onend = () => {
        this.currentUtterance = null;
    };

    utterance.onerror = (err) => {
        console.error("TTS Error:", err);
        this.currentUtterance = null;
    };

    if (this.voices.length === 0) {
      this.getVoices().then((voices) => {
         this.setVoice(utterance, voiceName, voices);
         this.synthesis.speak(utterance);
      });
    } else {
      this.setVoice(utterance, voiceName, this.voices);
      this.synthesis.speak(utterance);
    }
    
    return utterance;
  }

  setVoice(utterance, voiceName, voices) {
    if (voiceName) {
      const voice = voices.find(v => v.name === voiceName);
      if (voice) utterance.voice = voice;
    }
  }

  cancel() {
    if (this.synthesis.speaking) {
      this.synthesis.cancel();
    }
  }

  // --- STT Methods ---

  startListening(onResult, onEnd, onError) {
    if (!this.recognition) return false;

    if (this.isListening) {
        this.stopListening();
        return;
    }

    this.recognition.onstart = () => {
      this.isListening = true;
    };

    this.recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0].transcript)
        .join('');
      const isFinal = event.results[0].isFinal;
      onResult(transcript, isFinal);
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      this.isListening = false;
      if (onError) onError(event.error);
    };

    this.recognition.onend = () => {
      this.isListening = false;
      if (onEnd) onEnd();
    };

    try {
        this.recognition.start();
        return true;
    } catch (e) {
        console.error("Failed to start recognition:", e);
        return false;
    }
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }
}

export const voiceManager = new VoiceManager();
