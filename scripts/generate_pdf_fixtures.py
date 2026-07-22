"""Regenerates the PDF test fixtures under tests/fixtures/.

Run from the repo root: .venv/bin/python scripts/generate_pdf_fixtures.py
"""

import fitz

SECTIONS = [
    ("Overview", [
        "Nimbus Notes is a fictional note-taking application used purely as a test "
        "fixture for the Universal File RAG PDF ingestion pipeline. It is not a "
        "real product and none of the policies described here apply to any actual "
        "service.",
        "It supports notebooks, tags, and offline editing, and this document "
        "describes account limits, sync behavior, sharing permissions, and export "
        "formats in enough detail to exercise structure-aware chunking and page "
        "citation accuracy across several distinct sections and multiple pages.",
        "The document is intentionally verbose in places so that its total length "
        "clears the length gate used to decide whether a hierarchical outline is "
        "worth building for a given file, rather than falling back to plain "
        "vector-only indexing.",
    ]),
    ("Account Limits", [
        "Free accounts may create up to 100 notes and 5 notebooks, with a total "
        "attachment storage cap of 200 MB across the whole account. Notes beyond "
        "the 100 note limit cannot be created until existing notes are deleted or "
        "archived.",
        "Pro accounts remove the note and notebook count limits entirely and raise "
        "the attachment storage cap to 50 GB. Pro accounts also unlock offline "
        "mobile sync, which Free accounts cannot use at all under any "
        "circumstance, even temporarily.",
        "Exceeding the Free tier's storage cap blocks new attachment uploads but "
        "never blocks creating or editing plain text notes, since text notes do "
        "not count against the attachment storage cap at all.",
        "Team accounts, available only as an add-on to Pro, allow up to 20 members "
        "sharing a pool of notebooks with individually assignable read or write "
        "permissions per notebook, configurable by the team administrator.",
    ]),
    ("Sync and Conflicts", [
        "Nimbus Notes syncs every 30 seconds while online. If the same note is "
        "edited on two devices while offline, the version with the later edit "
        "timestamp wins automatically once both devices reconnect and sync "
        "completes.",
        "The losing version is never deleted outright: it is saved into a Note "
        "History panel accessible from that note for 60 days, after which older "
        "history entries are purged automatically to save storage and cannot be "
        "recovered afterward.",
        "Manual conflict resolution is available as a setting for Pro accounts, "
        "which pauses automatic conflict resolution and instead prompts the user "
        "to choose which version to keep, or to merge both versions manually into "
        "a new note.",
    ]),
    ("Export Formats", [
        "Notes can be exported as Markdown, plain text, or PDF. Markdown export "
        "preserves headings, bold and italic formatting, and checklist items, but "
        "does not preserve inline images, which are only included in PDF export.",
        "Bulk export of an entire notebook produces a single zip archive "
        "containing one file per note, named after each note's title with "
        "duplicate titles disambiguated by appending a numeric suffix such as "
        "'(2)' or '(3)'.",
        "Exported PDFs always embed the note's creation and last-modified "
        "timestamps in the footer of every page, regardless of whether the "
        "original note displayed them in the app itself.",
    ]),
    ("Sharing and Permissions", [
        "Individual notes can be shared via a link with view-only or "
        "comment-only permission on any account tier, including Free. Edit "
        "permission via shared link is a Pro-only feature.",
        "Shared links can be set to expire after a chosen number of days, or left "
        "permanently active until manually revoked by the note's owner at any "
        "time, immediately invalidating the link for anyone who has it.",
        "Team notebook permissions always take precedence over an individual "
        "note's link sharing settings: a Viewer-only team member cannot gain "
        "edit access to a note in that notebook even via a link marked as "
        "editable.",
    ]),
    ("Billing and Refunds", [
        "Pro subscriptions bill monthly or annually, chosen at signup, with annual "
        "billing discounted 20 percent versus paying monthly for twelve months. "
        "Billing always occurs on the same calendar day each period as the "
        "original signup date, adjusted to the last day of shorter months when "
        "needed.",
        "If a renewal payment fails, Nimbus Notes retries the charge daily for 7 "
        "days before downgrading the account to Free. Downgrading never deletes "
        "notes or notebooks even if the account then exceeds Free tier limits; "
        "excess notebooks simply become read-only until upgraded again or "
        "trimmed below the limit.",
        "Refunds are issued only for annual subscriptions cancelled within 14 "
        "days of the billing date, prorated to the unused portion of the year. "
        "Monthly subscriptions are never eligible for partial refunds, though "
        "cancellation always takes effect at the end of the current billing "
        "period rather than immediately upon request.",
    ]),
    ("Data Retention", [
        "When a user deletes their Nimbus Notes account entirely, all notes, "
        "attachments, and shared links are permanently removed after a 30 day "
        "grace period, during which the account can still be reactivated by "
        "signing back in with the original credentials.",
        "After the grace period ends, deletion is irreversible and Nimbus Notes "
        "cannot recover any content under any circumstance, even upon a direct "
        "request from the account owner or a formal support escalation.",
        "Team notebooks are handled differently on individual account deletion: "
        "if the deleted account was not the sole administrator of a team "
        "notebook, the notebook and its contents remain with the remaining team "
        "members untouched and fully accessible.",
        "If the deleted account was the sole administrator of a team notebook, "
        "administrator rights transfer automatically to the longest-tenured "
        "remaining team member before the account deletion completes, so a team "
        "notebook is never left without an administrator.",
    ]),
    ("Support Response Times", [
        "Free tier support requests are answered over email only, with a target "
        "response time of 5 business days and no guaranteed resolution time.",
        "Pro tier support requests are answered within 1 business day, and Team "
        "add-on accounts additionally get access to live chat support during "
        "business hours in the account owner's configured timezone. Live chat "
        "availability does not extend to weekends or public holidays observed in "
        "that timezone, during which requests fall back to the standard 1 "
        "business day email response target.",
    ]),
]


def make_structured_pdf(path: str, use_toc: bool) -> None:
    doc = fitz.open()
    toc = []
    for title, paragraphs in SECTIONS:
        page = doc.new_page()
        y = 72
        page.insert_text((72, y), title, fontsize=18, fontname="helv")
        toc.append([1, title, page.number + 1])
        y += 30
        for para in paragraphs:
            rect = fitz.Rect(72, y, 523, 792 - 40)
            page.insert_textbox(rect, para, fontsize=10, fontname="helv")
            y += 14 * (len(para) // 75 + 2)
    if use_toc:
        doc.set_toc(toc)
    doc.save(path)
    doc.close()


def make_short_pdf(path: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(
        fitz.Rect(72, 72, 523, 300),
        "Reminder: the office guest wifi password is Sunflower42, rotated monthly. "
        "Ask Priya at the front desk for parking validation stickers.",
        fontsize=11,
        fontname="helv",
    )
    doc.save(path)
    doc.close()


if __name__ == "__main__":
    make_structured_pdf("tests/fixtures/sample_manual_toc.pdf", use_toc=True)
    make_structured_pdf("tests/fixtures/sample_manual_fonts.pdf", use_toc=False)
    make_short_pdf("tests/fixtures/sample_note.pdf")
    print("done")
