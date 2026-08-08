/**
 * P0-SEC-001 — behavioural authorization tests for nonprofit_verifications.
 *
 * STATUS: EXECUTED AND PASSING (2026-08-08). 9/9 against the Firestore emulator.
 *
 * Clean-environment command:
 *   npm install -D @firebase/rules-unit-testing firebase-tools jest
 *   npx firebase emulators:exec --only firestore --project daanaa-rules-test \
 *     "npx jest tests/firestore_rules"
 *
 * Result: Tests: 9 passed, 9 total.
 * Reverting firestore.rules to `allow read, write: if request.auth.uid != null`
 * yields 4 failed / 5 passed, confirming these tests detect the original defect.
 *
 * Requires a Java runtime (default-jre-headless) for the emulator. The emulator
 * is pinned to 127.0.0.1:8571 in firebase.json because port 8080 is held by
 * llama-swap on the Daanaa host.
 *
 * These assert the authorization model in
 * audits/2026-08-daanaa-baseline/16-first-implementation-package.md:
 * unspecified access is denied; clients cannot read or write verification
 * records; no client can self-verify; wallet rules stay owner-scoped.
 */
const fs = require('fs');
const path = require('path');
const {
  initializeTestEnvironment,
  assertFails,
  assertSucceeds,
} = require('@firebase/rules-unit-testing');

let testEnv;

beforeAll(async () => {
  testEnv = await initializeTestEnvironment({
    projectId: 'daanaa-rules-test',
    firestore: {
      rules: fs.readFileSync(path.resolve(__dirname, '../../firestore.rules'), 'utf8'),
    },
  });
});

afterAll(async () => { if (testEnv) await testEnv.cleanup(); });
beforeEach(async () => { if (testEnv) await testEnv.clearFirestore(); });

describe('nonprofit_verifications — client access denied (P0-SEC-001)', () => {
  const DOC = 'nonprofit_verifications/123456789/records/rec1';

  test('anonymous read is denied', async () => {
    const db = testEnv.unauthenticatedContext().firestore();
    await assertFails(db.doc(DOC).get());
  });

  test('anonymous write is denied', async () => {
    const db = testEnv.unauthenticatedContext().firestore();
    await assertFails(db.doc(DOC).set({ status: 'verified' }));
  });

  // The original defect: ANY signed-in user could read/write EVERY nonprofit.
  test('unrelated authenticated user cannot read', async () => {
    const db = testEnv.authenticatedContext('some-random-user').firestore();
    await assertFails(db.doc(DOC).get());
  });

  test('unrelated authenticated user cannot write', async () => {
    const db = testEnv.authenticatedContext('some-random-user').firestore();
    await assertFails(db.doc(DOC).set({ status: 'verified' }));
  });

  // Self-verification: a user whose uid equals the nonprofit id still gets nothing.
  test('a user cannot verify themselves by matching the nonprofit id', async () => {
    const db = testEnv.authenticatedContext('123456789').firestore();
    await assertFails(db.doc(DOC).set({ status: 'verified', confidence_score: 100 }));
  });

  test('nested wildcard documents are also denied', async () => {
    const db = testEnv.authenticatedContext('some-random-user').firestore();
    await assertFails(db.doc('nonprofit_verifications/123456789/a/b/c/d').get());
    await assertFails(db.doc('nonprofit_verifications/123456789/a/b/c/d').set({ x: 1 }));
  });
});

// NOTE on path shape: these rules use `match /{uid}/<name>/{document=**}`, where
// {uid} binds to a top-level COLLECTION and <name> to a DOCUMENT id. A document
// reference therefore needs an even number of segments, e.g.
// `user-a/saved_organizations/items/org1`. A 3-segment path is a collection ref
// and the SDK rejects it before rules are ever consulted.
describe('scope guard — wallet rules unchanged', () => {
  test('owner can read and write their own saved_organizations', async () => {
    const db = testEnv.authenticatedContext('user-a').firestore();
    await assertSucceeds(db.doc('user-a/saved_organizations/items/org1').set({ ein: '123456789' }));
    await assertSucceeds(db.doc('user-a/saved_organizations/items/org1').get());
  });

  test('another user cannot read someone else\'s saved_organizations', async () => {
    const db = testEnv.authenticatedContext('user-b').firestore();
    await assertFails(db.doc('user-a/saved_organizations/items/org1').get());
  });

  test('audit logs remain write-denied to clients', async () => {
    const db = testEnv.authenticatedContext('user-a').firestore();
    await assertFails(db.doc('user-a/audit_logs/items/e1').set({ event: 'x' }));
  });
});
