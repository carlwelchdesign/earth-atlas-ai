import {
  useEffect,
  useId,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";

import {
  ASSESSMENT_DISPOSITIONS,
  AssessmentValidationError,
  dispositionLabel,
  validateAssessmentDraft,
  type AssessmentDisposition,
  type AssessmentDraft,
  type AssessmentEvent,
} from "./assessment";

export interface AssessmentDialogValue {
  requestId: string;
  candidateId: string;
  currentEvent: AssessmentEvent | null;
}

interface AssessmentDialogProps {
  bundleId: string;
  value: AssessmentDialogValue;
  onCancel: () => void;
  onSave: (draft: AssessmentDraft) => Promise<void>;
}

export function AssessmentDialog({
  bundleId,
  value,
  onCancel,
  onSave,
}: AssessmentDialogProps) {
  const titleId = useId();
  const descriptionId = useId();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const continueEditingRef = useRef<HTMLButtonElement>(null);
  const [disposition, setDisposition] = useState<AssessmentDisposition>(
    value.currentEvent?.disposition ?? "supported",
  );
  const [note, setNote] = useState(value.currentEvent?.note ?? "");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [confirmingDiscard, setConfirmingDiscard] = useState(false);

  useEffect(() => headingRef.current?.focus(), []);
  useEffect(() => {
    if (confirmingDiscard) continueEditingRef.current?.focus();
  }, [confirmingDiscard]);

  function requestCancel() {
    if (dirty) {
      setConfirmingDiscard(true);
      return;
    }
    onCancel();
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const source: AssessmentDraft = {
      requestId: value.requestId,
      bundleId,
      candidateId: value.candidateId,
      disposition,
      note,
      ...(value.currentEvent
        ? { supersedesEventId: value.currentEvent.eventId }
        : {}),
    };
    let draft: AssessmentDraft;
    try {
      draft = validateAssessmentDraft(source);
    } catch (validationError: unknown) {
      setError(
        validationError instanceof AssessmentValidationError
          ? validationError.message
          : "The assessment is invalid.",
      );
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave(draft);
    } catch (saveError: unknown) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : "The assessment could not be saved.",
      );
      setSaving(false);
    }
  }

  return (
    <div className="dialog-backdrop">
      <section
        className="assessment-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        onKeyDown={(event) => trapDialogFocus(event, requestCancel, saving)}
      >
        <form onSubmit={(event) => void submit(event)}>
          <div className="dialog-heading">
            <div>
              <p className="overline">
                {value.currentEvent
                  ? "Append correction"
                  : "Analyst assessment"}
              </p>
              <h2 ref={headingRef} id={titleId} tabIndex={-1}>
                {value.candidateId}
              </h2>
            </div>
            <button
              className="icon-button"
              type="button"
              aria-label="Close assessment"
              onClick={requestCancel}
              disabled={saving}
            >
              ×
            </button>
          </div>
          {confirmingDiscard ? (
            <div className="discard-confirmation" role="alert">
              <h3>Discard unsaved assessment draft?</h3>
              <p id={descriptionId}>
                Your selected action and note have not been saved. Discarding
                closes this dialog and cannot restore the draft.
              </p>
              <div className="dialog-actions">
                <button
                  ref={continueEditingRef}
                  className="primary-button"
                  type="button"
                  onClick={() => setConfirmingDiscard(false)}
                >
                  Continue editing
                </button>
                <button
                  className="danger-button"
                  type="button"
                  onClick={onCancel}
                >
                  Discard draft
                </button>
              </div>
            </div>
          ) : (
            <>
              <p className="dialog-boundary" id={descriptionId}>
                Record your review of this machine-generated candidate. This
                does not establish real-world change, damage, cause, intent, or
                operational status.
              </p>
              {value.currentEvent ? (
                <div className="correction-notice">
                  The new event will supersede {value.currentEvent.eventId}. The
                  prior event remains in the audit history.
                </div>
              ) : null}
              <fieldset className="assessment-options" disabled={saving}>
                <legend>Assessment action</legend>
                {ASSESSMENT_DISPOSITIONS.map((option) => (
                  <label key={option}>
                    <input
                      type="radio"
                      name="assessment-disposition"
                      value={option}
                      checked={disposition === option}
                      onChange={() => {
                        setDisposition(option);
                        setDirty(true);
                      }}
                    />
                    <span>
                      <strong>{dispositionLabel(option)}</strong>
                      <small>{dispositionDescription(option)}</small>
                    </span>
                  </label>
                ))}
              </fieldset>
              <label className="note-field">
                <span>
                  Analyst note
                  {disposition === "needs-context"
                    ? " (required)"
                    : " (optional)"}
                </span>
                <textarea
                  value={note}
                  onChange={(event) => {
                    setNote(event.target.value);
                    setDirty(true);
                  }}
                  maxLength={500}
                  rows={5}
                  disabled={saving}
                  aria-describedby="note-count"
                />
                <small id="note-count">{note.length} / 500 characters</small>
              </label>
              {error ? (
                <div className="save-error" role="alert">
                  <strong>Assessment not saved</strong>
                  <span>
                    {error} Your draft is still here. Retry when ready.
                  </span>
                </div>
              ) : null}
              <div className="dialog-actions">
                <button
                  className="secondary-button"
                  type="button"
                  onClick={requestCancel}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  className="primary-button"
                  type="submit"
                  disabled={saving}
                >
                  {saving
                    ? "Saving…"
                    : error
                      ? "Retry save"
                      : "Append assessment"}
                </button>
              </div>
            </>
          )}
        </form>
      </section>
    </div>
  );
}

function trapDialogFocus(
  event: KeyboardEvent<HTMLElement>,
  onCancel: () => void,
  saving: boolean,
) {
  if (event.key === "Escape" && !saving) {
    event.preventDefault();
    onCancel();
    return;
  }
  if (event.key !== "Tab") return;
  const controls = Array.from(
    event.currentTarget.querySelectorAll<HTMLElement>(
      'button, input, textarea, [tabindex="0"]',
    ),
  ).filter((control) => !control.hasAttribute("disabled"));
  const first = controls[0];
  const last = controls.at(-1);
  if (!first || !last) return;
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function dispositionDescription(disposition: AssessmentDisposition): string {
  const descriptions: Record<AssessmentDisposition, string> = {
    supported: "Evidence supports keeping this candidate in review.",
    rejected: "Evidence does not support this machine candidate.",
    "needs-context": "More evidence or domain context is required.",
  };
  return descriptions[disposition];
}
