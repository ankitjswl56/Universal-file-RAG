# Aperture Cloud Storage — User Manual

Aperture Cloud Storage is a fictional file-syncing service used here purely
as a test fixture for the Universal File RAG ingestion pipeline. This manual
describes account tiers, syncing behavior, password recovery, and billing
policy in enough detail to exercise structure-aware chunking and citation
accuracy across several distinct sections.

## Account Tiers

Aperture offers three account tiers: Free, Plus, and Studio.

The Free tier includes 15 GB of storage, a single connected device, and file
version history limited to 7 days. It is intended for individuals trying the
service before committing to a paid plan.

The Plus tier includes 500 GB of storage, up to 5 connected devices, and 30
days of file version history. Plus accounts also unlock selective sync,
letting a user choose which folders sync to a given device rather than
mirroring the entire account.

The Studio tier includes 2 TB of storage, unlimited connected devices, and 180
days of file version history. Studio accounts add team folders, granular
sharing permissions, and priority support response times.

Upgrading or downgrading a tier takes effect immediately; storage overages
after a downgrade are handled as described in the Billing Policy section
below.

## Password Recovery

If a user forgets their password, recovery works as follows: the user
requests a reset link from the sign-in screen, Aperture emails a link valid
for 60 minutes, and following that link lets the user set a new password.

For security, a password reset immediately invalidates all existing sessions
on every connected device, requiring the user to sign in again everywhere.
Aperture does not send the current password by email under any circumstance,
since it is never stored in a recoverable form.

Accounts with two-factor authentication enabled require the second factor
during the reset flow as well, not only during normal sign-in. If a user has
lost access to their second factor device, they must go through account
recovery support instead of the standard reset flow, which involves manual
identity verification and can take up to 3 business days.

## Sync Behavior and Conflict Resolution

Aperture syncs files continuously in the background on every connected
device. When the same file is edited offline on two different devices before
either reconnects, a sync conflict occurs once both devices come back online.

Aperture resolves sync conflicts by keeping both versions: the most recently
saved version keeps the original filename, and the older version is renamed
with a suffix indicating the conflicting device name and timestamp, for
example `report (conflicted copy from Ankit's Laptop 2026-03-01).docx`. No
data is silently discarded during a conflict.

Deleted files are not immediately purged. They move to a Trash folder and
are retained there for 30 days on Free and Plus tiers, and 90 days on Studio,
after which they are permanently removed and unrecoverable.

## Storage Quotas and Overages

Each tier has a hard storage quota as described in the Account Tiers section.
When an account exceeds its quota, uploads are paused but existing files
remain fully accessible and continue syncing changes to already-synced
content. New file creation and new uploads resume automatically once the
account is back under quota, either by deleting files or upgrading tier.

Aperture does not delete a user's files to enforce a quota automatically
under any circumstance. An account that remains over quota for more than 90
consecutive days receives a final warning email before being moved to a
read-only state, in which no changes of any kind can be made until the
account is brought back under quota or upgraded.

## Billing Policy

Plus and Studio subscriptions are billed monthly or annually, chosen at
signup, and annual billing includes a 20% discount compared to paying
monthly for twelve months. Billing occurs on the same calendar day each
period as the original signup date.

If a payment fails, Aperture retries the charge three times over 10 days
before downgrading the account to the Free tier. Downgrading to Free does
not delete any files even if the account is then over the Free tier's 15 GB
quota — the account instead enters the read-only overage state described in
the Storage Quotas section above.

Refunds are issued only for annual subscriptions cancelled within the first
14 days of the billing period, prorated to the unused portion of the year.
Monthly subscriptions are not eligible for partial refunds under any
circumstance, though cancellation always takes effect at the end of the
current billing period rather than immediately.

## Sharing and Permissions

Studio tier team folders support three permission levels: Viewer, Editor,
and Owner. Viewers can read and download files but cannot modify or delete
them. Editors can additionally upload, edit, and delete files, but cannot
change folder-level permissions or remove other members. Owners have full
control, including the ability to remove the entire team folder.

Free and Plus tiers support link-based sharing only: a user generates a link
to a single file or folder, optionally protected with a password and an
expiration date, and anyone with the link can view or download the content
depending on the permission chosen at link creation. Link sharing does not
require the recipient to have an Aperture account.

Shared links can be revoked at any time by the original sharer, immediately
invalidating access for anyone who previously received that link, even if
they had already opened it once before.

## Data Retention and Account Deletion

When a user deletes their Aperture account entirely, all files, version
history, and shared links are permanently removed after a 30-day grace
period, during which the account can still be reactivated by signing back
in. After the grace period ends, deletion is irreversible and Aperture
cannot recover any content, even upon request.

Team folders on a Studio account are handled differently on individual
account deletion: if the deleted account was not the sole Owner of a team
folder, the folder and its contents remain with the remaining Owners
untouched. If the deleted account was the sole Owner, ownership transfers
automatically to the longest-tenured Editor on that folder before the
account deletion completes, so a team folder is never left ownerless.
