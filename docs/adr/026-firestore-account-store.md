# ADR 026 — Firestore for the Account Store

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

ADR 022 put accounts, invites and sessions behind an `AccountStore` interface
and shipped a JSON-file store, saying a Firestore store would follow for the
cloud. On Cloud Run the container's disk is wiped on every restart and every
scale to zero (ADR 025), so with the JSON store every user, invite and session
would disappear whenever the instance stops. That blocks the closed beta.

The owner has created the Google Cloud project with Firestore in Native mode,
and a runtime service account with the `datastore.user` role.

## Decision

1. **Firestore in Native mode** holds accounts in the cloud, through the
   official `google-cloud-firestore` client.
2. **Same shape as the JSON store.** Three collections, `users` and `invites`
   keyed by email and `sessions` keyed by the token's SHA-256 hash, holding
   the same fields. Only hashes of passwords, invite codes and tokens are
   stored, as before.
3. **Chosen by setting.** `ACCOUNT_STORE` is `json` (the default, so local
   development and tests need no cloud) or `firestore`, which uses
   `GCP_PROJECT_ID` and `FIRESTORE_DATABASE`. `FIRESTORE_COLLECTION_PREFIX`
   lets staging and production share one database without sharing accounts.
4. **Credentials from the environment.** On Cloud Run the client uses the
   runtime service account. The owner's invite script uses their own
   Application Default Credentials. No key file is created or committed.

### Dependencies this allows

- `google-cloud-firestore`: the Firestore client. It adds itself and
  `google-cloud-core`; its gRPC and auth libraries are already installed for
  the Cloud Trace exporter (ADR 024).

## Consequences

- **Easier:** accounts survive restarts, scale to zero and new revisions, and
  the owner can invite friends from their own machine against the cloud store.
- **Concurrency.** Each change is a whole-document write, as with the JSON
  store. With one instance (ADR 025) that is safe enough; more instances would
  need transactions for the failed-login counter before the limit is raised.
- **Cost.** At beta volume, reads and writes are expected to stay within
  Firestore's free daily allowance; the owner checks the current pricing page.
- **Tests** run the full account service suite against both stores, using an
  in-memory fake of the Firestore client, so no test needs the network.
