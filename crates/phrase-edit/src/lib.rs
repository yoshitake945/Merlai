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
        assert!(edit(&changed, 8., "もう少し減らして").unwrap().len() < changed.len());
        assert!(edit(&notes, 8., "後半だけ音数を半分にして移調").is_err());
    }
}
