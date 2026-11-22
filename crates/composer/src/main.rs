#![forbid(unsafe_code)]
use midly::{Format, Header, MetaMessage, MidiMessage, Smf, Timing, TrackEvent, TrackEventKind};
use serde::{Deserialize, Serialize};
use std::{
    collections::{HashMap, VecDeque},
    error::Error,
    fs, io,
    path::{Path, PathBuf},
};
type Result<T> = std::result::Result<T, Box<dyn Error>>;
#[derive(Clone, Debug, Serialize)]
struct Note {
    at: u32,
    len: u32,
    pitch: u8,
    velocity: u8,
}
struct Clip {
    notes: Vec<Note>,
    ppq: u32,
    bar: u32,
    tempo: u32,
    end: u32,
}
#[derive(Deserialize)]
struct Request {
    version: u8,
    melody: PathBuf,
    drums: Option<PathBuf>,
    output: PathBuf,
    bars: u32,
    seed: u32,
    kicks: Vec<u8>,
    tonic: Option<u8>,
    attack_ms: f64,
    release_ms: f64,
}
#[derive(Serialize)]
struct Response {
    version: u8,
    ppq: u32,
    tempo: u32,
    continuation_at: u32,
    melody: Vec<Note>,
    candidates: Vec<Candidate>,
}
#[derive(Serialize)]
struct Candidate {
    file: PathBuf,
    notes: Vec<Note>,
}
fn read(path: &Path) -> Result<Clip> {
    let bytes = fs::read(path)?;
    let smf = Smf::parse(&bytes)?;
    let Timing::Metrical(res) = smf.header.timing else {
        return Err("PPQ MIDI required".into());
    };
    let ppq = u32::from(res.as_int());
    if ppq == 0 || smf.header.format == Format::Sequential {
        return Err("Expected a format 0 or 1 clip".into());
    }
    let mut notes = Vec::new();
    let mut tempos = vec![(0, 500000)];
    let mut meters = vec![(0, 4 * ppq)];
    let mut end = 0;
    for track in smf.tracks {
        let mut at = 0u32;
        let mut active = HashMap::<(u8, u8), VecDeque<(u32, u8)>>::new();
        for e in track {
            at = at.checked_add(e.delta.as_int()).ok_or("tick overflow")?;
            if at > 0x03ffffff {
                return Err("clip exceeds supported length".into());
            }
            match e.kind {
                TrackEventKind::Meta(MetaMessage::Tempo(t)) => tempos.push((at, t.as_int())),
                TrackEventKind::Meta(MetaMessage::TimeSignature(n, d, _, _)) => {
                    if d > 7 {
                        return Err("Unsupported meter".into());
                    }
                    meters.push((at, 4 * ppq * u32::from(n) / (1 << d)));
                }
                TrackEventKind::Midi { channel, message } => match message {
                    MidiMessage::NoteOn { key, vel } if vel.as_int() > 0 => active
                        .entry((channel.as_int(), key.as_int()))
                        .or_default()
                        .push_back((at, vel.as_int())),
                    MidiMessage::NoteOn { key, .. } | MidiMessage::NoteOff { key, .. } => {
                        if let Some((start, velocity)) = active
                            .get_mut(&(channel.as_int(), key.as_int()))
                            .and_then(VecDeque::pop_front)
                        {
                            notes.push(Note {
                                at: start,
                                len: (at - start).max(1),
                                pitch: key.as_int(),
                                velocity,
                            })
                        }
                    }
                    _ => {}
                },
                _ => {}
            }
        }
        if active.values().any(|q| !q.is_empty()) {
            return Err("Melody contains unclosed notes".into());
        }
        end = end.max(at);
    }
    notes.sort_by_key(|n| (n.at, n.pitch));
    let first = notes.first().ok_or("No playable notes")?.at;
    let timing = |mut events: Vec<(u32, u32)>| -> Result<u32> {
        events.sort_by_key(|e| e.0);
        let value = events.iter().rev().find(|e| e.0 <= first).unwrap().1;
        if value == 0 || events.iter().any(|&(at, v)| at > first && v != value) {
            return Err("Export a constant tempo and meter region".into());
        }
        Ok(value)
    };
    let tempo = timing(tempos)?;
    let bar = timing(meters)?;
    let origin = first / bar * bar;
    for note in &mut notes {
        note.at -= origin
    }
    end -= origin;
    Ok(Clip {
        notes,
        ppq,
        bar,
        tempo,
        end,
    })
}
fn write(path: &Path, notes: &[Note], end: u32, ppq: u32) -> Result<()> {
    let mut events = Vec::new();
    for n in notes {
        events.push((n.at, true, n.pitch, n.velocity));
        events.push((n.at + n.len, false, n.pitch, 0))
    }
    events.sort_unstable();
    let mut last = 0;
    let mut track = Vec::new();
    for (at, on, key, vel) in events {
        let message = if on {
            MidiMessage::NoteOn {
                key: key.into(),
                vel: vel.into(),
            }
        } else {
            MidiMessage::NoteOff {
                key: key.into(),
                vel: vel.into(),
            }
        };
        track.push(TrackEvent {
            delta: (at - last).into(),
            kind: TrackEventKind::Midi {
                channel: 0.into(),
                message,
            },
        });
        last = at;
    }
    track.push(TrackEvent {
        delta: (end - last).into(),
        kind: TrackEventKind::Meta(MetaMessage::EndOfTrack),
    });
    Smf {
        header: Header::new(Format::SingleTrack, Timing::Metrical((ppq as u16).into())),
        tracks: vec![track],
    }
    .save(path)?;
    Ok(())
}
fn generate(r: &Request) -> Result<Response> {
    if r.version != 1
        || !(1..=16).contains(&r.bars)
        || r.tonic.is_some_and(|v| v > 11)
        || ![r.attack_ms, r.release_ms]
            .iter()
            .all(|v| v.is_finite() && *v >= 0.)
    {
        return Err("Invalid request settings".into());
    }
    let c = read(&r.melody)?;
    let drum = r.drums.as_deref().map(read).transpose()?;
    let end = c.bar * r.bars;
    let period = c.end.max(1).div_ceil(c.bar) * c.bar;
    let slow = r.attack_ms >= 75.;
    let long = r.release_ms >= 300.;
    let motif_start = period.saturating_sub(c.bar * 2);
    let motif: Vec<_> = c.notes.iter().filter(|n| n.at >= motif_start).collect();
    if motif.is_empty() {
        return Err("Trim trailing silent bars from the melody".into());
    }
    let cycle = period - motif_start;
    let kicks: Vec<_> = drum
        .iter()
        .flat_map(|d| {
            d.notes
                .iter()
                .filter(|n| r.kicks.contains(&n.pitch))
                .map(move |n| n.at as u64 * c.ppq as u64 / d.ppq as u64)
        })
        .collect();
    let drum_period = drum.as_ref().map_or(1, |d| {
        ((d.end.max(1).div_ceil(d.bar) * d.bar) as u64 * c.ppq as u64 / d.ppq as u64).max(1)
    });
    let mut sets = Vec::new();
    for variant in 0..3 {
        let mut notes: Vec<Note> = Vec::new();
        for base in (0..end).step_by(cycle as usize) {
            for (i, src) in motif.iter().enumerate() {
                let offset = if variant == 1 && i % 2 == 1 {
                    c.ppq / 8
                } else {
                    0
                };
                let at = base + src.at - motif_start + offset;
                if at >= end
                    || ((slow || variant == 2)
                        && notes.last().is_some_and(|n| at < n.at + c.ppq / 2))
                    || kicks.iter().any(|k| {
                        k.abs_diff(u64::from(at) % drum_period) < u64::from((c.ppq / 8).max(1))
                    })
                {
                    continue;
                }
                let other = motif[(i + variant + r.seed as usize % motif.len()) % motif.len()];
                let mut len = if slow { src.len.max(c.ppq) } else { src.len };
                if long {
                    len = (len * 2 / 3).max(1)
                }
                notes.push(Note {
                    at,
                    len: len.min(end - at),
                    pitch: other.pitch,
                    velocity: src.velocity,
                });
            }
        }
        notes.sort_by_key(|n| n.at);
        if let Some(last) = notes.last_mut() {
            let root = r.tonic.unwrap_or(c.notes[0].pitch % 12);
            let pc = (root + [0, 7, 0][variant]) % 12;
            last.pitch = (0u8..=127)
                .filter(|p| p % 12 == pc)
                .min_by_key(|p| p.abs_diff(last.pitch))
                .unwrap();
        } else {
            return Err("All notes conflict with the drum pattern; change kick mapping".into());
        }
        for i in 1..notes.len() {
            let gap = notes[i].at - notes[i - 1].at;
            if gap > 0 {
                notes[i - 1].len = notes[i - 1].len.min(gap)
            }
        }
        sets.push(notes);
    }
    fs::create_dir(&r.output)?; // A fresh directory protects previously generated files.
    let mut candidates = Vec::new();
    for (i, notes) in sets.into_iter().enumerate() {
        let file = r.output.join(format!("candidate-{}.mid", i + 1));
        write(&file, &notes, end, c.ppq)?;
        candidates.push(Candidate { file, notes })
    }
    Ok(Response {
        version: 1,
        ppq: c.ppq,
        tempo: c.tempo,
        continuation_at: period,
        melody: c.notes,
        candidates,
    })
}
fn main() {
    if let Err(e) = (|| -> Result<()> {
        let req = serde_json::from_reader(io::stdin().lock())?;
        serde_json::to_writer(io::stdout().lock(), &generate(&req)?)?;
        Ok(())
    })() {
        eprintln!("{e}");
        std::process::exit(1)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn logic_export_keeps_pickup_with_project_offset() {
        // Logic may put the initial tempo and meter at the region's project position.
        let bytes = include_bytes!("../../../tests/native/melody.mid");
        let mut smf = Smf::parse(bytes).unwrap();
        smf.tracks[0][0].delta = 23040.into();
        let first_note = smf.tracks[0]
            .iter_mut()
            .find(|e| matches!(e.kind, TrackEventKind::Midi { .. }))
            .unwrap();
        first_note.delta = 120.into();
        let path = std::env::temp_dir().join(format!("merlai-offset-{}.mid", std::process::id()));
        smf.save(&path).unwrap();
        let clip = read(&path).unwrap();
        assert_eq!(clip.notes[0].at, 120);
        assert_eq!(clip.tempo, 535716);
        fs::remove_file(path).unwrap();
    }
    #[test]
    fn compose_and_reimport() {
        let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../tests/native");
        let dir = std::env::temp_dir().join(format!("merlai-test-{}", std::process::id()));
        let mut req = Request {
            version: 1,
            melody: root.join("melody.mid"),
            drums: Some(root.join("groove.mid")),
            output: dir.clone(),
            bars: 2,
            seed: 42,
            kicks: vec![36],
            tonic: Some(6),
            attack_ms: 0.,
            release_ms: 0.,
        };
        let result = generate(&req).unwrap();
        assert_eq!(result.candidates.len(), 3);
        assert_eq!(result.continuation_at, 3840);
        let original = fs::read(&result.candidates[0].file).unwrap();
        let pluck = read(&result.candidates[0].file).unwrap();
        assert_eq!(pluck.notes.len(), 12);
        assert_eq!(pluck.end, 3840);
        assert!(pluck.notes.iter().all(|n| n.at % 960 != 0 && n.len == 120));
        assert!(generate(&req).is_err());
        fs::remove_dir_all(&dir).unwrap();
        let repeated = generate(&req).unwrap();
        assert_eq!(original, fs::read(&repeated.candidates[0].file).unwrap());
        fs::remove_dir_all(&dir).unwrap();
        req.attack_ms = 150.;
        req.release_ms = 500.;
        let pad = generate(&req).unwrap();
        assert_ne!(original, fs::read(&pad.candidates[0].file).unwrap());
        fs::remove_dir_all(&dir).unwrap();
    }
}
