# Chord Progression Analyzer - Project Plan

## Overview
Build a full-stack chord progression analyzer with real-time timeline, clickable chords, MIDI extraction, and in-house AI - no external APIs.

## Phase 1: Core Project Structure, Audio Upload, and Basic Timeline UI ✅
**Goal**: Set up the foundation with project management, audio upload, waveform display, and basic timeline interface.

- [x] Create database models (Project, AudioFile, AnalysisJob, ChordSegment, NoteEvent) with SQLAlchemy
- [x] Build REST API endpoints: POST /projects, POST /projects/{id}/upload, GET /projects/{id}
- [x] Implement audio file upload with validation (mp3, wav, flac, ogg support)
- [x] Generate low-resolution waveform preview for visualization
- [x] Create main timeline UI component with waveform display
- [x] Add project list sidebar with create/select/delete functionality
- [x] Build transport controls (play, pause, stop, scrub position indicator)
- [x] Set up Web Audio API integration for audio playback

---

## Phase 2: Beat Detection, Tempo Analysis, and Timeline Grid ✅
**Goal**: Implement beat/tempo detection pipeline and display synchronized beat grid on timeline.

- [x] Install and configure librosa, numpy, scipy, soundfile for audio processing
- [x] Implement beat tracking algorithm (librosa.beat.beat_track with dynamic tempo)
- [x] Build tempo curve estimation and confidence scoring
- [x] Create beat grid data structure with measures and beat-in-measure indexing
- [x] Render beat grid lines on timeline synchronized with waveform
- [x] Add zoom controls (in/out, fit-to-view) with beat grid scaling
- [x] Display tempo (BPM) and time signature in timeline header
- [x] Add "Analyze Audio" button that triggers beat detection
- [x] Implement background analysis using async processing
- [x] Show loading state during analysis

---

## Phase 3: Key Detection and Chord Recognition Pipeline ✅
**Goal**: Build the in-house AI chord detection system with key detection, chroma extraction, and HMM-based chord recognition.

- [x] Implement key detection using Krumhansl-Schmuckler algorithm on chroma features
- [x] Build chroma/HPCP extraction pipeline (constant-Q transform based)
- [x] Create chord template library (major, minor, maj7, min7, dom7, dim, aug, sus2, sus4, add9)
- [x] Implement HMM-based chord recognition with Viterbi decoding
- [x] Build chord transition probability matrix and key-informed priors
- [x] Extend analysis service to include chord detection after beat detection
- [x] Store detected chords in project data with confidence scores and MIDI note arrays
- [x] Display chord chips on timeline aligned to detected segments
- [x] Add chord label tooltips showing inversion, confidence, and note names
- [x] Add detected key display in timeline header (e.g., "Key: C Major")

---

## Phase 4: Interactive Chord Playback and Click-to-Audition
**Goal**: Enable users to click chord chips to hear synthesized chord notes in real-time.

- [ ] Extend audio_player.js with Web Audio API synthesizer for chord note generation
- [ ] Build chord voicing engine with proper note spacing and octave placement
- [ ] Create client-side chord scheduling with <120ms latency target
- [ ] Add click handlers to chord chips for instant audition (on_click event)
- [ ] Implement chord track generation synchronized with original audio playback
- [ ] Build audio mixer for blending original audio + generated chord track
- [ ] Add volume controls for original audio and chord track (independent sliders)
- [ ] Create solo/mute toggles for chord layer
- [ ] Display currently playing chord with visual highlight on timeline
- [ ] Add keyboard shortcuts for audition (spacebar play/pause, arrow keys navigate chords)

---

## Phase 5: Manual Chord Editing and Online Learning System
**Goal**: Allow users to edit chord labels with immediate feedback and model improvement through online learning.

- [ ] Build inline chord editor (dropdown or text input with chord symbol validation)
- [ ] Implement chord update functionality for editing detected chords
- [ ] Add segment boundary editing (drag handles to adjust start/end times)
- [ ] Create merge/split segment controls
- [ ] Implement online learning system: update chord priors and transition probabilities from user edits
- [ ] Store user corrections and model adaptations in project data
- [ ] Add "Re-analyze with corrections" button to re-run chord detection with updated priors
- [ ] Display edit history and model confidence changes in UI
- [ ] Implement undo/redo stack for chord edits

---

## Phase 6: Advanced Layer Detection (Melody, Bass, Drums) and MIDI Export
**Goal**: Implement melody, bass, and drum note tracking with layer visualization and MIDI file export.

- [ ] Install pretty_midi or mido for MIDI generation
- [ ] Implement melody extraction: pitch contour tracking with note segmentation
- [ ] Build bass note tracking: low-frequency centroid analysis with onset detection
- [ ] Create drum onset detection with kick/snare/hi-hat classification templates
- [ ] Build layer tracks UI: separate rows for melody, bass, chords, drums on timeline
- [ ] Implement solo/mute/volume controls for each layer
- [ ] Create layer visibility toggles and color coding
- [ ] Build MIDI export engine with layer selection params
- [ ] Generate Standard MIDI file with tempo map, separate tracks per layer, and quantization options
- [ ] Add MIDI export modal with options: layer selection, quantization strength, humanization
- [ ] Implement chord chart export (JSON and TXT formats)
- [ ] Add project export bundle (analysis JSON + audio + MIDI + chord chart)

---

## Phase 7: Optional Source Separation, Advanced Features, and Polish
**Goal**: Add optional stem separation for higher quality analysis, reharmonization suggestions, and final UI polish.

- [ ] Research and optionally install local source separation model (demucs or spleeter)
- [ ] Add separation toggle in analysis quality presets (fast=no separation, hq=with separation)
- [ ] Implement stem extraction (drums, bass, vocals, other) when separation enabled
- [ ] Build separate analysis pipelines for separated stems vs. full mix
- [ ] Implement key modulation detection for songs with section-based key changes
- [ ] Create harmonic function tagging (I, IV, V, etc.) for detected chords
- [ ] Build reharmonization suggestion engine based on voice-leading and model priors
- [ ] Add "Suggestions" panel showing alternative chord interpretations
- [ ] Implement loop region selection on timeline with loop playback mode
- [ ] Add waveform color themes and visualization options (spectral, linear, log scale)
- [ ] Create keyboard shortcut reference modal (accessible via "?" key)
- [ ] Implement loading states, skeleton loaders, and smooth transitions
- [ ] Add accessibility: ARIA labels, keyboard navigation, screen reader support
- [ ] Build settings panel: audio device selection, buffer size, synth type, default quality preset
- [ ] Add project search and filter in sidebar
- [ ] Implement auto-save for chord edits and playback position

---

## Current Status
- **Active Phase**: Phase 4
- **Completed**: 3/7 phases (Phase 1 ✅, Phase 2 ✅, Phase 3 ✅)
- **Next Steps**: Implement interactive chord playback with click-to-audition functionality

## Technical Stack Confirmed
- Backend: FastAPI + SQLAlchemy + SQLite (not using REST API - using Reflex state management)
- Audio/ML: librosa, numpy, scipy, soundfile (local processing only)
- MIDI: pretty_midi or mido (planned for Phase 6)
- Frontend: Reflex with Web Audio API integration
- No external API dependencies

## Notes
- All ML/DSP runs locally - no API keys needed
- Progressive analysis: show tempo/beats first, then chords, then layers
- Target latencies: <200ms playback jitter, <120ms click-to-audition
- Focus on feature-complete, production-ready implementation
- Using Reflex state management instead of separate REST API
