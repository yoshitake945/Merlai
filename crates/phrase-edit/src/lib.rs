//! Fixed vocabulary editor. Called on the plug-in UI thread.
#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Note {
    pub start: f64,
    pub end: f64,
    pub pitch: u8,
    pub velocity: u8,
    pub channel: u8,
}

#[repr(C)]
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Onset {
    pub frame: u32,
    pub strength: f32,
    /// 0 is dominated by low frequencies, 1 by fast/high-frequency changes.
    pub brightness: f32,
}

/// Fixed-size streaming detector state. It is initialized off the audio thread
/// and performs no allocation, locking or I/O while processing a block.
#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct AudioAnalyzerState {
    envelope: f32,
    high_envelope: f32,
    baseline: f32,
    previous: f32,
    previous_sample: f32,
    cooldown: u32,
}

impl Default for AudioAnalyzerState {
    fn default() -> Self {
        Self {
            envelope: 0.,
            high_envelope: 0.,
            baseline: 0.002,
            previous: 0.,
            previous_sample: 0.,
            cooldown: 0,
        }
    }
}

fn detect_onsets(
    state: &mut AudioAnalyzerState,
    samples: &[f32],
    sample_rate: f64,
    output: &mut [Onset],
) -> usize {
    if !sample_rate.is_finite() || sample_rate <= 0. || output.is_empty() {
        return 0;
    }
    let refractory = (sample_rate * 0.045) as u32;
    let mut count = 0;
    for (frame, sample) in samples.iter().enumerate() {
        let magnitude = sample.abs().min(4.);
        let high = (sample - state.previous_sample).abs().min(4.);
        let prior_envelope = state.envelope;
        let threshold = (state.baseline * 2.2).max(0.008);
        // Compare the unsmoothed attack with the envelope from the preceding
        // sample. Comparing two smoothed samples made the maximum rise about
        // 1.22x, so the old 1.35x condition could only re-arm after near
        // silence. Real drum loops (especially closed hats) never get that
        // quiet between hits.
        let impulsive = magnitude > prior_envelope * 1.65 + 0.003;
        state.envelope += 0.18 * (magnitude - state.envelope);
        state.high_envelope += 0.18 * (high - state.high_envelope);
        state.baseline += 0.0002 * (state.envelope - state.baseline);
        if state.cooldown > 0 {
            state.cooldown -= 1;
        }
        if state.cooldown == 0 && magnitude > threshold && impulsive {
            if count < output.len() {
                output[count] = Onset {
                    frame: frame as u32,
                    strength: (magnitude / threshold).min(4.) / 4.,
                    brightness: (high / (magnitude + high + 1e-6)).clamp(0., 1.),
                };
                count += 1;
            }
            state.cooldown = refractory;
        }
        state.previous = state.envelope;
        state.previous_sample = *sample;
    }
    count
}

fn edit(input: &[Note], span: f64, text: &str) -> Result<Vec<Note>, ()> {
    let normalized = text.replace([' ', '　', '。', '、', '！', '!', '，', ','], "");
    let mut rest = normalized.as_str();
    let half_only = rest.starts_with("後半だけ") || rest.starts_with("後半の");
    rest = rest
        .trim_start_matches("後半だけ")
        .trim_start_matches("後半の");
    let action = [
        "音数を半分にして",
        "音数を半分に",
        "半分にして",
        "半分に",
        "休符を増やして",
        "休符を増やす",
        "もう少し減らして",
    ]
    .into_iter()
    .find(|action| rest.starts_with(action))
    .ok_or(())?;
    rest = &rest[action.len()..];
    let keep_last = match rest {
        "" => false,
        "最後の音は残して" | "最後の音を残して" | "最後の音を残す" => true,
        _ => return Err(()),
    };
    let mut notes = input.to_vec();
    notes.sort_by(|a, b| a.start.total_cmp(&b.start));
    let last = notes.last().ok_or(())?.start;
    let mut beat = None;
    let mut group = 0usize;
    let stride = if action == "もう少し減らして" {
        3
    } else {
        2
    };
    notes.retain(|n| {
        if half_only && n.start < span / 2. {
            return true;
        }
        if beat != Some(n.start) {
            group += 1;
            beat = Some(n.start);
        }
        // When protecting the ending, discard the first onset of each pair.
        (keep_last && n.start == last)
            || if keep_last {
                group % stride != 1
            } else {
                group % stride != 0
            }
    });
    Ok(notes)
}

#[repr(u32)]
#[derive(Clone, Copy, Debug, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum GenerationPurpose {
    Edit = 0,
    Bass = 1,
    Chords = 2,
    CounterMelody = 3,
    Continue = 4,
}

/// Optional non-realtime generator inserted after the captured phrase has
/// become an immutable snapshot. Implementations may call a local or remote
/// model, but must return a complete candidate rather than mutating `input`.
pub trait GenerationModel {
    fn generate(
        &self,
        input: &[Note],
        span: f64,
        purpose: GenerationPurpose,
        instruction: &str,
    ) -> Result<Vec<Note>, ()>;
}

/// Provider-neutral byte transport. Network access, authentication and model
/// selection stay outside the generation engine and its Audio Unit.
pub trait ModelTransport {
    fn complete(&self, request: &[u8]) -> Result<Vec<u8>, ()>;
}

#[derive(serde::Serialize)]
struct ModelRequest<'a> {
    version: u8,
    instruction: &'a str,
    purpose: GenerationPurpose,
    span: f64,
    notes: Vec<ModelNote>,
}

#[derive(Clone, Copy, serde::Deserialize, serde::Serialize)]
struct ModelNote {
    start: f64,
    end: f64,
    pitch: u8,
    velocity: u8,
    channel: u8,
}

impl From<&Note> for ModelNote {
    fn from(note: &Note) -> Self {
        Self {
            start: note.start,
            end: note.end,
            pitch: note.pitch,
            velocity: note.velocity,
            channel: note.channel,
        }
    }
}

impl From<ModelNote> for Note {
    fn from(note: ModelNote) -> Self {
        Self {
            start: note.start,
            end: note.end,
            pitch: note.pitch,
            velocity: note.velocity,
            channel: note.channel,
        }
    }
}

#[derive(serde::Deserialize)]
struct ModelResponse {
    notes: Vec<ModelNote>,
}

/// JSON adapter shared by local and remote providers. It only runs when passed
/// to `generate_candidate`, which the Audio Unit invokes on its worker queue.
pub struct JsonGenerationModel<T> {
    transport: T,
}

impl<T> JsonGenerationModel<T> {
    pub fn new(transport: T) -> Self {
        Self { transport }
    }
}

impl<T: ModelTransport> GenerationModel for JsonGenerationModel<T> {
    fn generate(
        &self,
        input: &[Note],
        span: f64,
        purpose: GenerationPurpose,
        instruction: &str,
    ) -> Result<Vec<Note>, ()> {
        let request = serde_json::to_vec(&ModelRequest {
            version: 1,
            instruction,
            purpose,
            span,
            notes: input.iter().map(ModelNote::from).collect(),
        })
        .map_err(|_| ())?;
        let response = self.transport.complete(&request)?;
        Ok(serde_json::from_slice::<ModelResponse>(&response)
            .map_err(|_| ())?
            .notes
            .into_iter()
            .map(Note::from)
            .collect())
    }
}

fn bass_pitch(pitch: u8) -> u8 {
    36 + pitch % 12
}

fn generate(input: &[Note], span: f64, purpose: GenerationPurpose) -> Result<Vec<Note>, ()> {
    if input.is_empty() || !span.is_finite() || span <= 0. {
        return Err(());
    }
    let mut sorted = input.to_vec();
    sorted.sort_by(|a, b| a.start.total_cmp(&b.start).then(a.pitch.cmp(&b.pitch)));
    let generated = match purpose {
        GenerationPurpose::Edit => sorted,
        GenerationPurpose::Bass => {
            let mut result = Vec::new();
            let analyzed_drums = sorted.iter().all(|note| {
                note.channel == 9 && matches!(note.pitch, 36 | 38 | 42) && note.end > note.start
            });
            if analyzed_drums {
                let has_kick = sorted.iter().any(|note| note.pitch == 36);
                for note in sorted.iter().filter(|note| !has_kick || note.pitch == 36) {
                    result.push(Note {
                        start: note.start,
                        end: (note.start + 0.2).min(span),
                        pitch: 36,
                        velocity: note.velocity.clamp(48, 112),
                        channel: 0,
                    });
                }
                return Ok(result);
            }
            let mut beat = -1_i64;
            for note in &sorted {
                let current = note.start.floor() as i64;
                if current != beat {
                    beat = current;
                    result.push(Note {
                        start: current as f64,
                        end: ((current + 1) as f64 - 0.05).min(span),
                        pitch: bass_pitch(note.pitch),
                        velocity: note.velocity.clamp(48, 105),
                        channel: note.channel,
                    });
                }
            }
            result
        }
        GenerationPurpose::Chords => {
            let mut result = Vec::new();
            let windows = (span / 2.).ceil() as usize;
            for window in 0..windows {
                let start = window as f64 * 2.;
                let Some(root_note) = sorted
                    .iter()
                    .filter(|n| n.start >= start && n.start < start + 2.)
                    .min_by_key(|n| n.pitch)
                else {
                    continue;
                };
                let root = 48 + root_note.pitch % 12;
                let minor = sorted.iter().any(|n| {
                    n.start >= start
                        && n.start < start + 2.
                        && (n.pitch + 12 - root_note.pitch) % 12 == 3
                });
                for interval in [0, if minor { 3 } else { 4 }, 7] {
                    result.push(Note {
                        start,
                        end: (start + 1.9).min(span),
                        pitch: root + interval,
                        velocity: root_note.velocity.clamp(42, 92),
                        channel: root_note.channel,
                    });
                }
            }
            result
        }
        GenerationPurpose::CounterMelody => sorted
            .iter()
            .enumerate()
            .filter(|(index, _)| index % 2 == 0)
            .map(|(_, note)| Note {
                start: note.start,
                end: note.end.min(span),
                pitch: note
                    .pitch
                    .saturating_sub(if note.pitch % 12 == 4 { 4 } else { 3 }),
                velocity: note.velocity.saturating_sub(10).max(35),
                channel: note.channel,
            })
            .collect(),
        GenerationPurpose::Continue => sorted,
    };
    (!generated.is_empty()).then_some(generated).ok_or(())
}

fn scale_intervals(scale: u32) -> &'static [u8] {
    match scale {
        1 => &[0, 2, 4, 5, 7, 9, 11],
        2 => &[0, 2, 3, 5, 7, 8, 10],
        _ => &[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    }
}

fn quantize_pitch(pitch: u8, key_root: u32, scale: u32) -> u8 {
    if key_root > 11 || scale == 0 {
        return pitch;
    }
    let allowed = scale_intervals(scale);
    (0..=127)
        .min_by_key(|candidate| {
            let class = (*candidate as u32 + 12 - key_root) % 12;
            let outside = !allowed.contains(&(class as u8));
            (outside, (*candidate as i16 - pitch as i16).unsigned_abs())
        })
        .unwrap_or(pitch)
}

fn generate_context(
    primary: &[Note],
    harmony: &[Note],
    source_span: f64,
    purpose: GenerationPurpose,
    target_span: f64,
    key_root: u32,
    scale: u32,
    variation: u32,
) -> Result<Vec<Note>, ()> {
    if primary.is_empty()
        || !source_span.is_finite()
        || source_span <= 0.
        || !target_span.is_finite()
        || target_span <= 0.
    {
        return Err(());
    }
    let mut result = if purpose == GenerationPurpose::Continue {
        let mut source = primary.to_vec();
        source.sort_by(|a, b| a.start.total_cmp(&b.start).then(a.pitch.cmp(&b.pitch)));
        let mut output = Vec::new();
        let repeats = (target_span / source_span).ceil() as usize;
        for repeat in 0..repeats {
            let offset = repeat as f64 * source_span;
            let transpose = if variation > 0 && repeat % 2 == 1 {
                2
            } else {
                0
            };
            for note in &source {
                if note.start + offset >= target_span || output.len() >= 2048 {
                    continue;
                }
                let mut copy = *note;
                copy.start += offset;
                copy.end = (copy.end + offset).min(target_span);
                copy.pitch = quantize_pitch(copy.pitch.saturating_add(transpose), key_root, scale);
                output.push(copy);
            }
        }
        output
    } else {
        let basis = if !harmony.is_empty()
            && matches!(purpose, GenerationPurpose::Bass | GenerationPurpose::Chords)
        {
            harmony
        } else {
            primary
        };
        generate(basis, source_span, purpose)?
    };
    if purpose != GenerationPurpose::Edit {
        for note in &mut result {
            note.pitch = quantize_pitch(note.pitch, key_root, scale);
        }
    }
    (!result.is_empty() && result.len() <= 2048)
        .then_some(result)
        .ok_or(())
}

fn valid_candidate(notes: &[Note], span: f64) -> bool {
    !notes.is_empty()
        && notes.len() <= 2048
        && notes.iter().all(|note| {
            note.start.is_finite()
                && note.end.is_finite()
                && note.start >= 0.
                && note.end > note.start
                && note.end <= span
                && note.pitch <= 127
                && note.velocity <= 127
                && note.channel <= 15
        })
}

/// Runs an optional model on the UI/worker side and falls back to the existing
/// deterministic rules on errors or malformed output. The fallback keeps
/// generation usable when no model is configured or a provider is unavailable.
pub fn generate_candidate(
    input: &[Note],
    span: f64,
    purpose: GenerationPurpose,
    instruction: &str,
    model: Option<&dyn GenerationModel>,
) -> Result<Vec<Note>, ()> {
    if let Some(model) = model {
        if let Ok(candidate) = model.generate(input, span, purpose, instruction) {
            if valid_candidate(&candidate, span) {
                return Ok(candidate);
            }
        }
    }
    generate(input, span, purpose)
}

/// Returns the count, or -1 for an unrecognized instruction.
/// # Safety
/// Caller supplies count initialized notes, count writable output slots, and a NUL-terminated UTF-8 command.
#[no_mangle]
pub unsafe extern "C" fn merlai_edit(
    input: *const Note,
    count: usize,
    span: f64,
    text: *const std::ffi::c_char,
    output: *mut Note,
) -> i32 {
    if count == 0 || count > 2048 || input.is_null() || output.is_null() || text.is_null() {
        return -1;
    }
    let Ok(cmd) = std::ffi::CStr::from_ptr(text).to_str() else {
        return -1;
    };
    match edit(std::slice::from_raw_parts(input, count), span, cmd) {
        Ok(result) => {
            std::ptr::copy_nonoverlapping(result.as_ptr(), output, result.len());
            result.len() as i32
        }
        Err(()) => -1,
    }
}

/// Generates a deterministic accompaniment candidate. Returns its note count,
/// or -1 when the input or purpose is invalid.
/// # Safety
/// Caller supplies count initialized notes and at least 2048 writable output slots.
#[no_mangle]
pub unsafe extern "C" fn merlai_generate(
    input: *const Note,
    count: usize,
    span: f64,
    purpose: u32,
    output: *mut Note,
) -> i32 {
    if count == 0 || count > 2048 || input.is_null() || output.is_null() {
        return -1;
    }
    let purpose = match purpose {
        0 => GenerationPurpose::Edit,
        1 => GenerationPurpose::Bass,
        2 => GenerationPurpose::Chords,
        3 => GenerationPurpose::CounterMelody,
        _ => return -1,
    };
    match generate_candidate(
        std::slice::from_raw_parts(input, count),
        span,
        purpose,
        "",
        None,
    ) {
        Ok(result) if result.len() <= 2048 => {
            std::ptr::copy_nonoverlapping(result.as_ptr(), output, result.len());
            result.len() as i32
        }
        _ => -1,
    }
}

/// Generates from a primary phrase plus optional harmonic context. The legacy
/// `merlai_generate` entry point remains available for v1 callers.
/// # Safety
/// Callers supply initialized note arrays and at least 2048 output slots.
#[no_mangle]
pub unsafe extern "C" fn merlai_generate_context(
    primary: *const Note,
    primary_count: usize,
    harmony: *const Note,
    harmony_count: usize,
    source_span: f64,
    purpose: u32,
    target_span: f64,
    key_root: u32,
    scale: u32,
    variation: u32,
    output: *mut Note,
) -> i32 {
    if primary_count == 0
        || primary_count > 2048
        || harmony_count > 2048
        || primary.is_null()
        || output.is_null()
        || (harmony_count > 0 && harmony.is_null())
    {
        return -1;
    }
    let purpose = match purpose {
        0 => GenerationPurpose::Edit,
        1 => GenerationPurpose::Bass,
        2 => GenerationPurpose::Chords,
        3 => GenerationPurpose::CounterMelody,
        4 => GenerationPurpose::Continue,
        _ => return -1,
    };
    let harmony = if harmony_count == 0 {
        &[]
    } else {
        std::slice::from_raw_parts(harmony, harmony_count)
    };
    match generate_context(
        std::slice::from_raw_parts(primary, primary_count),
        harmony,
        source_span,
        purpose,
        target_span,
        key_root,
        scale,
        variation,
    ) {
        Ok(result) => {
            std::ptr::copy_nonoverlapping(result.as_ptr(), output, result.len());
            result.len() as i32
        }
        Err(()) => -1,
    }
}

/// Detects percussive onsets in one mono audio block without allocation.
/// Returns the number of initialized output events.
/// # Safety
/// The caller supplies one valid state, `frames` readable samples, and
/// `capacity` writable output events. State is owned by one audio thread.
#[no_mangle]
pub unsafe extern "C" fn merlai_detect_onsets(
    state: *mut AudioAnalyzerState,
    samples: *const f32,
    frames: usize,
    sample_rate: f64,
    output: *mut Onset,
    capacity: usize,
) -> usize {
    if state.is_null() || samples.is_null() || output.is_null() || capacity == 0 {
        return 0;
    }
    detect_onsets(
        &mut *state,
        std::slice::from_raw_parts(samples, frames),
        sample_rate,
        std::slice::from_raw_parts_mut(output, capacity),
    )
}

#[no_mangle]
pub extern "C" fn merlai_analyzer_reset(state: &mut AudioAnalyzerState) {
    *state = AudioAnalyzerState::default();
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn preserves_untouched_notes_and_respects_unknown_instructions() {
        let notes: Vec<_> = (0..16)
            .map(|i| Note {
                start: i as f64 / 2.,
                end: i as f64 / 2. + 0.25,
                pitch: 60 + i,
                velocity: 82,
                channel: 2,
            })
            .collect();
        let changed = edit(&notes, 8., "後半だけ音数を半分に。最後の音は残して").unwrap();
        assert_eq!(&changed[..8], &notes[..8]);
        assert_eq!(changed.len(), 12);
        assert_eq!(changed.last(), notes.last());
        assert_eq!(edit(&notes, 8., "後半だけ半分に").unwrap().len(), 12);
        assert!(edit(&changed, 8., "もう少し減らして").unwrap().len() < changed.len());
        assert!(edit(&notes, 8., "後半だけ音数を半分にして移調").is_err());
    }

    #[test]
    fn generates_three_reproducible_accompaniment_roles() {
        let notes: Vec<_> = (0..8)
            .map(|i| Note {
                start: i as f64 / 2.,
                end: i as f64 / 2. + 0.3,
                pitch: 60 + i,
                velocity: 82,
                channel: 0,
            })
            .collect();
        let bass = generate(&notes, 4., GenerationPurpose::Bass).unwrap();
        assert_eq!(bass.len(), 4);
        assert!(bass.iter().all(|note| (36..48).contains(&note.pitch)));
        let chords = generate(&notes, 4., GenerationPurpose::Chords).unwrap();
        assert_eq!(chords.len(), 6);
        let counter = generate(&notes, 4., GenerationPurpose::CounterMelody).unwrap();
        assert_eq!(counter.len(), 4);
        assert!(counter
            .iter()
            .zip(notes.iter().step_by(2))
            .all(|(a, b)| a.pitch < b.pitch));
        assert_eq!(
            generate(&notes, 4., GenerationPurpose::Edit).unwrap(),
            notes
        );

        let drum_onsets = [
            Note {
                start: 0.,
                end: 0.1,
                pitch: 36,
                velocity: 90,
                channel: 9,
            },
            Note {
                start: 0.75,
                end: 0.85,
                pitch: 42,
                velocity: 70,
                channel: 9,
            },
        ];
        let groove = generate(&drum_onsets, 1., GenerationPurpose::Bass).unwrap();
        assert_eq!(groove.len(), 1);
        assert_eq!(groove[0].start, 0.);
    }

    #[test]
    fn continues_a_phrase_with_key_scale_and_harmonic_context() {
        let primary = [
            Note {
                start: 0.,
                end: 0.5,
                pitch: 61,
                velocity: 80,
                channel: 0,
            },
            Note {
                start: 1.,
                end: 1.5,
                pitch: 64,
                velocity: 80,
                channel: 0,
            },
        ];
        let continued =
            generate_context(&primary, &[], 2., GenerationPurpose::Continue, 6., 0, 1, 1).unwrap();
        assert_eq!(continued.len(), 6);
        assert!(continued
            .iter()
            .all(|note| [0, 2, 4, 5, 7, 9, 11].contains(&(note.pitch % 12))));
        assert!(continued.iter().all(|note| note.end <= 6.));

        let harmony = [Note {
            start: 0.,
            end: 2.,
            pitch: 67,
            velocity: 70,
            channel: 0,
        }];
        let bass =
            generate_context(&primary, &harmony, 2., GenerationPurpose::Bass, 2., 0, 1, 0).unwrap();
        assert_eq!(bass[0].pitch % 12, 7);
    }

    #[test]
    fn model_generation_uses_valid_output_and_falls_back_safely() {
        struct Model(Result<Vec<Note>, ()>);
        impl GenerationModel for Model {
            fn generate(
                &self,
                _input: &[Note],
                _span: f64,
                purpose: GenerationPurpose,
                _instruction: &str,
            ) -> Result<Vec<Note>, ()> {
                assert_eq!(purpose, GenerationPurpose::CounterMelody);
                self.0.clone()
            }
        }

        let input = [Note {
            start: 0.,
            end: 0.5,
            pitch: 64,
            velocity: 80,
            channel: 0,
        }];
        let modeled = Note {
            start: 0.25,
            end: 0.75,
            pitch: 72,
            velocity: 70,
            channel: 0,
        };
        assert_eq!(
            generate_candidate(
                &input,
                1.,
                GenerationPurpose::CounterMelody,
                "もっと跳躍させて",
                Some(&Model(Ok(vec![modeled])))
            )
            .unwrap(),
            vec![modeled]
        );

        let deterministic = generate(&input, 1., GenerationPurpose::CounterMelody).unwrap();
        assert_eq!(
            generate_candidate(
                &input,
                1.,
                GenerationPurpose::CounterMelody,
                "",
                Some(&Model(Err(())))
            )
            .unwrap(),
            deterministic
        );
        let outside_span = Note { end: 2., ..modeled };
        assert_eq!(
            generate_candidate(
                &input,
                1.,
                GenerationPurpose::CounterMelody,
                "",
                Some(&Model(Ok(vec![outside_span])))
            )
            .unwrap(),
            deterministic
        );
    }

    #[test]
    fn json_model_protocol_carries_instruction_and_notes() {
        use std::sync::{Arc, Mutex};

        struct Transport {
            request: Arc<Mutex<Vec<u8>>>,
            response: Vec<u8>,
        }
        impl ModelTransport for Transport {
            fn complete(&self, request: &[u8]) -> Result<Vec<u8>, ()> {
                *self.request.lock().unwrap() = request.to_vec();
                Ok(self.response.clone())
            }
        }

        let captured = Arc::new(Mutex::new(Vec::new()));
        let model = JsonGenerationModel::new(Transport {
            request: Arc::clone(&captured),
            response:
                br#"{"notes":[{"start":0.25,"end":0.75,"pitch":72,"velocity":70,"channel":0}]}"#
                    .to_vec(),
        });
        let input = [Note {
            start: 0.,
            end: 0.5,
            pitch: 64,
            velocity: 80,
            channel: 0,
        }];
        let result = generate_candidate(
            &input,
            1.,
            GenerationPurpose::CounterMelody,
            "もっと跳躍させて",
            Some(&model),
        )
        .unwrap();
        assert_eq!(result[0].pitch, 72);

        let request: serde_json::Value = serde_json::from_slice(&captured.lock().unwrap()).unwrap();
        assert_eq!(request["version"], 1);
        assert_eq!(request["instruction"], "もっと跳躍させて");
        assert_eq!(request["purpose"], "counter_melody");
        assert_eq!(request["span"], 1.);
        assert_eq!(request["notes"][0]["pitch"], 64);

        let malformed = JsonGenerationModel::new(Transport {
            request: Arc::clone(&captured),
            response: b"not json".to_vec(),
        });
        assert_eq!(
            generate_candidate(
                &input,
                1.,
                GenerationPurpose::CounterMelody,
                "自由文",
                Some(&malformed),
            )
            .unwrap(),
            generate(&input, 1., GenerationPurpose::CounterMelody).unwrap()
        );
    }

    #[test]
    fn detects_separated_drum_transients_across_blocks() {
        let rate = 1_000.;
        let mut state = AudioAnalyzerState::default();
        let mut events = [Onset::default(); 8];
        let mut first = vec![0.; 100];
        first[10] = 1.;
        first[11] = 0.6;
        let count = detect_onsets(&mut state, &first, rate, &mut events);
        assert_eq!(count, 1);
        assert_eq!(events[0].frame, 10);
        let mut second = vec![0.; 100];
        second[70] = 0.8;
        let count = detect_onsets(&mut state, &second, rate, &mut events);
        assert_eq!(count, 1);
        assert_eq!(events[0].frame, 70);
        assert!(events[0].strength > 0.);
    }

    #[test]
    fn onset_brightness_separates_low_and_noisy_attacks() {
        let mut low = vec![0.; 256];
        for (i, sample) in low.iter_mut().enumerate().skip(64) {
            *sample = ((i - 64) as f32 * 0.05).sin() * 0.8;
        }
        let mut noisy = vec![0.; 256];
        for (i, sample) in noisy.iter_mut().enumerate().skip(64) {
            *sample = if i % 2 == 0 { 0.8 } else { -0.8 };
        }
        let mut low_state = AudioAnalyzerState::default();
        let mut noisy_state = AudioAnalyzerState::default();
        let mut low_events = [Onset::default(); 4];
        let mut noisy_events = [Onset::default(); 4];
        let low_count = detect_onsets(&mut low_state, &low, 48_000., &mut low_events);
        let noisy_count = detect_onsets(&mut noisy_state, &noisy, 48_000., &mut noisy_events);
        assert!(low_count > 0 && noisy_count > 0);
        assert!(noisy_events[0].brightness > low_events[0].brightness);
    }

    #[test]
    fn detects_drum_hits_over_a_continuous_hat_bed() {
        let rate = 48_000.;
        let mut samples = vec![0.; 24_000];
        for (i, sample) in samples.iter_mut().enumerate() {
            *sample = if i % 2 == 0 { 0.018 } else { -0.018 };
        }
        for &start in &[2_400usize, 9_600, 16_800] {
            samples[start] += 0.9;
            samples[start + 1] += 0.5;
        }
        let mut state = AudioAnalyzerState::default();
        let mut events = [Onset::default(); 16];
        let count = detect_onsets(&mut state, &samples, rate, &mut events);
        // The hat bed itself starts with an onset at frame zero; all three
        // stronger hits must still re-trigger while that bed is continuous.
        assert_eq!(count, 4);
        assert_eq!(events[1].frame, 2_400);
        assert_eq!(events[2].frame, 9_600);
        assert_eq!(events[3].frame, 16_800);
    }
}
