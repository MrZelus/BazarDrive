-- Reconcile legacy rows after verification workflow rollout.
-- If a profile was already verified before verification_state existed,
-- preserve trust status by syncing verification_state with is_verified.
UPDATE guest_profiles
SET
    verification_state = 'verified',
    verification_decided_at = COALESCE(verification_decided_at, CURRENT_TIMESTAMP),
    verification_decided_by = COALESCE(verification_decided_by, 'legacy_backfill')
WHERE is_verified = 1
  AND COALESCE(verification_state, '') <> 'verified';

UPDATE guest_profiles
SET verification_state = 'unverified'
WHERE is_verified = 0
  AND COALESCE(verification_state, '') = '';
