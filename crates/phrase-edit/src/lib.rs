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
#[derive(Clone, Copy)]
pub enum GenerationPurpose {
    Bass = 0,
    Chords = 1,
    CounterMelody = 2,
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
        GenerationPurpose::Bass => {
            let mut result = Vec::new();
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
    };
    (!generated.is_empty()).then_some(generated).ok_or(())
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
        0 => GenerationPurpose::Bass,
        1 => GenerationPurpose::Chords,
        2 => GenerationPurpose::CounterMelody,
        _ => return -1,
    };
    match generate(std::slice::from_raw_parts(input, count), span, purpose) {
        Ok(result) if result.len() <= 2048 => {
            std::ptr::copy_nonoverlapping(result.as_ptr(), output, result.len());
            result.len() as i32
        }
        _ => -1,
    }
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
    }
}
