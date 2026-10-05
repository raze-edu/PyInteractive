"""Procedural sound synthesizer for the educational app.
Generates pleasant, subtle tones in memory without external audio files.
Fails completely gracefully in headless or silent environments.
"""
import math
from typing import Optional
import pygame

class SoundManager:
    """Manages synthesised UI sounds for clicks, dings, chimes, and errors."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._sound_cache = {}
        self._mixer_ready = False
        
        if self.enabled:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                self._mixer_ready = True
            except Exception:
                self._mixer_ready = False

    def _generate_tone(self, freq: float, duration: float, volume: float = 0.2, decay: bool = True) -> Optional[pygame.mixer.Sound]:
        """Generates a soft sine wave tone with envelope."""
        if not self._mixer_ready:
            return None
            
        try:
            import numpy as np
            sample_rate = 44100
            n_samples = int(sample_rate * duration)
            t = np.linspace(0, duration, n_samples, False)
            
            # Sine wave
            waveform = np.sin(2 * np.pi * freq * t)
            
            # Envelope
            if decay:
                envelope = np.exp(-3.5 * t / duration)
            else:
                envelope = np.ones_like(t)
                
            audio = (waveform * envelope * volume * 32767).astype(np.int16)
            # Stereo array
            stereo = np.column_stack((audio, audio))
            return pygame.sndarray.make_sound(stereo)
        except Exception:
            return None

    def play_click(self) -> None:
        """Plays a gentle tap sound."""
        if not self._mixer_ready or not self.enabled:
            return
        if "click" not in self._sound_cache:
            self._sound_cache["click"] = self._generate_tone(800, 0.04, volume=0.15)
        sound = self._sound_cache.get("click")
        if sound:
            sound.play()

    def play_snap(self) -> None:
        """Plays a tile placement snap sound."""
        if not self._mixer_ready or not self.enabled:
            return
        if "snap" not in self._sound_cache:
            self._sound_cache["snap"] = self._generate_tone(520, 0.06, volume=0.2)
        sound = self._sound_cache.get("snap")
        if sound:
            sound.play()

    def play_correct(self) -> None:
        """Plays a cheerful two-tone success chime."""
        if not self._mixer_ready or not self.enabled:
            return
        try:
            import numpy as np
            sample_rate = 44100
            dur1, dur2 = 0.12, 0.28
            t1 = np.linspace(0, dur1, int(sample_rate * dur1), False)
            t2 = np.linspace(0, dur2, int(sample_rate * dur2), False)
            
            # E5 (659.25 Hz) then A5 (880 Hz)
            tone1 = np.sin(2 * np.pi * 659.25 * t1) * np.exp(-2.0 * t1 / dur1)
            tone2 = np.sin(2 * np.pi * 880.00 * t2) * np.exp(-3.0 * t2 / dur2)
            
            combined = np.concatenate((tone1, tone2))
            audio = (combined * 0.22 * 32767).astype(np.int16)
            stereo = np.column_stack((audio, audio))
            sound = pygame.sndarray.make_sound(stereo)
            sound.play()
        except Exception:
            pass

    def play_error(self) -> None:
        """Plays a gentle soft error tone."""
        if not self._mixer_ready or not self.enabled:
            return
        try:
            import numpy as np
            sample_rate = 44100
            duration = 0.18
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            # Low boop 220Hz
            tone = (np.sin(2 * np.pi * 220.0 * t) + 0.3 * np.sin(2 * np.pi * 110.0 * t)) * np.exp(-4.0 * t / duration)
            audio = (tone * 0.25 * 32767).astype(np.int16)
            stereo = np.column_stack((audio, audio))
            sound = pygame.sndarray.make_sound(stereo)
            sound.play()
        except Exception:
            pass

sound_manager = SoundManager()
