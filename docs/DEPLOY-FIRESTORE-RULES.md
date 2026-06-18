# Deploying Firestore Rules

This guide walks through deploying the Firestore security rules to the daanaa-af9c2 Firebase project.

## Prerequisites

- Access to Firebase Console (https://console.firebase.google.com)
- Permission to edit Firestore rules in the daanaa-af9c2 project
- The rules file at `/firestore.rules`

## Step-by-Step Deployment

### 1. Open Firebase Console

Go to https://console.firebase.google.com and select the **daanaa-af9c2** project.

### 2. Navigate to Firestore

In the left sidebar, click **Firestore Database**.

### 3. Click Rules Tab

At the top of the Firestore page, click the **Rules** tab (next to Data and Indexes).

### 4. Copy the Rules

Open the `firestore.rules` file from this repository and copy its entire contents.

### 5. Paste into Console

Clear the existing rules in the Firebase Console editor and paste the new rules.

### 6. Review the Rules

The editor will highlight:
- ✅ Green: Valid syntax
- ❌ Red: Syntax errors

If you see red errors, don't publish. Fix the rules and try again.

### 7. Publish the Rules

Click the blue **Publish** button at the top-right of the editor.

You'll see a confirmation dialog: "Are you sure you want to update the rules?"

Click **Publish** again to confirm.

### 8. Verify Deployment

Once published, you'll see a green success notification:
> "Your security rules have been successfully published."

## Testing Rules After Deployment

After publishing, test that the rules work as expected:

### Test 1: User Can Access Their Own Data

1. In the Rules editor, click **Simulate** at the bottom
2. Set:
   - **Request type**: Get
   - **Document path**: `testuser123/saved_organizations/test_org`
   - **Authentication**: Check the box and set `uid: testuser123`
3. Click **Run**
4. Result should be: **Allowed** ✅

### Test 2: User Cannot Access Another User's Data

1. Click **Simulate** again
2. Set:
   - **Request type**: Get
   - **Document path**: `otheruser/saved_organizations/test_org`
   - **Authentication**: Check the box and set `uid: testuser123`
3. Click **Run**
4. Result should be: **Denied** ✅

### Test 3: Nonprofit Can Access Verification Records

1. Click **Simulate** again
2. Set:
   - **Request type**: Get
   - **Document path**: `nonprofit_verifications/12345/record1`
   - **Authentication**: Check the box and set `uid: nonprofit_staff_123`
3. Click **Run**
4. Result should be: **Allowed** ✅

## Rollback (If Needed)

If the rules cause issues:

1. Go back to the Rules tab
2. Revert to the previous rules (Firebase keeps version history)
3. Click the clock icon (⏰) in the top-right to see previous versions
4. Click on a previous version and click **Restore**

## Verifying Production Behavior

After deployment, test in the actual application:

1. Sign in to Daanaa at https://daanaa.org/wallet
2. Add a saved organization
3. Log volunteer hours
4. Verify that data is saved in Firestore

To check Firestore data:

1. Go to Firestore Console → Data tab
2. Look for a collection named with your Firebase UID
3. Inside, you should see `saved_organizations`, `volunteer_hour_logs`, etc.
4. Click into each collection to verify your data is saved

## Troubleshooting

### "Blocked by firestore rules" Error

If users see this error when trying to save wallet data:

1. Verify the rules were published (check green success message)
2. Check that user is authenticated (signed in with Google)
3. Check browser console (F12) for the exact error message
4. Test the rules in Simulate to see what's being denied

### Collections Not Appearing in Console

Collections auto-create on first write. If you don't see a collection:

1. It hasn't been created yet (no user has saved data to it)
2. Or, the write was blocked by rules

To manually create a test collection:

1. Go to Firestore Data tab
2. Click "Start collection"
3. Enter: `testuser/saved_organizations`
4. Click "Next"
5. Click "Auto ID" for document name
6. Add a test field: `name: "Test Org"`
7. Click "Save"

This creates the collection so you can verify the structure.

## Rolling Out to Production

Once rules are tested locally:

1. ✅ Test in Firebase Simulator (as above)
2. ✅ Test in Staging (if available)
3. ✅ Publish to production (as above)
4. ✅ Monitor Firestore usage in Console
5. ✅ Check error logs in browser console for rule violations

## Related Files

- [firestore.rules](../../firestore.rules) - The actual rules
- [FIRESTORE-SETUP.md](./FIRESTORE-SETUP.md) - Full Firestore setup documentation
- [WALLET-SETUP.md](./WALLET-SETUP.md) - Wallet troubleshooting

## Questions?

If rules deployment fails or you need to adjust rules:

1. Check the error message in the Firebase Console
2. Review the rules documentation in [FIRESTORE-SETUP.md](./FIRESTORE-SETUP.md)
3. Test individual rules in the Simulate panel before publishing
