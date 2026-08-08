/**
 * P0-SEC-001 — behavioural authorization tests for nonprofit_verifications.
 *
 * STATUS: NOT YET EXECUTED. These require the Firebase emulator
 * (@firebase/rules-unit-testing + a Java runtime), neither of which is
 * installed in this repository. Adding that toolchain is a dependency decision
 * that has not been made. Until these run, P0-SEC-001 is verified only
 * statically by tests/test_firestore_rules_p0_sec_001.py — do not report the
 * package as behaviourally verified.
 *
 * To run once tooling exists:
 *   npm i -D @firebase/rules-unit-testing firebase-tools
 *   npx firebase emulators:exec --only firestore "npx jest tests/firestore_rules"
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

describe('scope guard — wallet rules unchanged', () => {
  test('owner can read and write their own saved_organizations', async () => {
    const db = testEnv.authenticatedContext('user-a').firestore();
    await assertSucceeds(db.doc('user-a/saved_organizations/org1').set({ ein: '123456789' }));
    await assertSucceeds(db.doc('user-a/saved_organizations/org1').get());
  });

  test('another user cannot read someone else\'s saved_organizations', async () => {
    const db = testEnv.authenticatedContext('user-b').firestore();
    await assertFails(db.doc('user-a/saved_organizations/org1').get());
  });

  test('audit logs remain write-denied to clients', async () => {
    const db = testEnv.authenticatedContext('user-a').firestore();
    await assertFails(db.doc('user-a/audit_logs/e1').set({ event: 'x' }));
  });
});
