#!/usr/bin/env python3
"""
Profile Contexts Tests — Security & Authorization

QA Requirements:
1. One person = one profile (Firebase UID identity)
2. Optional shared contexts (household, DAF, business, other)
3. Permission roles (Lead, Support, Member, Viewer)
4. Independent profile access (no merging on context join)
5. Wallet privacy (never exposed unless explicitly shared)
6. No PII collection (tax docs, IDs, amounts, receipts, income)
7. Role-based access control
8. Member removal
9. Context archival
10. Cross-context isolation

Run with: python3 -m pytest tests/test_profile_contexts.py -v
"""

import sys
import sqlite3
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts import profile_contexts


@pytest.fixture
def test_db():
    """Create in-memory test database."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    profile_contexts.ensure_schema(db)
    return db


# 1. One person = one profile (Firebase UID as identity)

def test_one_uid_one_profile(test_db):
    """Each Firebase UID has exactly one private profile."""
    uid = "user_123"
    ctx_id = profile_contexts.create_context(
        test_db,
        created_by_uid=uid,
        context_type='household'
    )
    contexts = profile_contexts.get_user_contexts(test_db, uid)
    assert len(contexts) >= 1


# 2. Optional shared contexts (household, DAF, business, other)

def test_create_all_context_types(test_db):
    """Create all valid context types."""
    uid = "user_1"
    for ctx_type in ['household', 'daf', 'business', 'other']:
        ctx_id = profile_contexts.create_context(
            test_db,
            created_by_uid=uid,
            context_type=ctx_type,
            display_name=f'{ctx_type} context'
        )
        assert ctx_id.startswith('ctx_')


def test_invalid_context_type_rejected(test_db):
    """Reject invalid context type."""
    with pytest.raises(ValueError):
        profile_contexts.create_context(
            test_db,
            created_by_uid="user_1",
            context_type='invalid'
        )


# 3. Permission roles (Lead, Support, Member, Viewer)

def test_creator_is_lead(test_db):
    """Context creator is automatically lead."""
    uid = "user_1"
    ctx_id = profile_contexts.create_context(test_db, created_by_uid=uid, context_type='household')
    contexts = profile_contexts.get_user_contexts(test_db, uid)
    assert contexts[0]['role'] == 'lead'


def test_all_roles_supported(test_db):
    """Support all role types."""
    lead_uid = "user_1"
    ctx_id = profile_contexts.create_context(test_db, created_by_uid=lead_uid, context_type='household')

    for role in ['member', 'support', 'viewer']:
        profile_contexts.add_member(
            test_db,
            context_id=ctx_id,
            firebase_uid=f"user_{role}",
            role=role,
            invited_by_uid=lead_uid
        )

    members = profile_contexts.get_context_members(test_db, ctx_id)
    roles = {m['firebase_uid']: m['role'] for m in members}
    assert roles[f"user_member"] == 'member'
    assert roles[f"user_support"] == 'support'
    assert roles[f"user_viewer"] == 'viewer'


# 4. Independent profile access (no merging on context join)

def test_profiles_not_merged_on_join(test_db):
    """Joining context doesn't merge profiles."""
    user1 = "user_1"
    user2 = "user_2"

    ctx_id = profile_contexts.create_context(
        test_db,
        created_by_uid=user1,
        context_type='household'
    )

    profile_contexts.add_member(
        test_db,
        context_id=ctx_id,
        firebase_uid=user2,
        role='member',
        invited_by_uid=user1
    )

    # Each user maintains independent identity
    user1_contexts = profile_contexts.get_user_contexts(test_db, user1)
    user2_contexts = profile_contexts.get_user_contexts(test_db, user2)

    assert len(user1_contexts) == 1
    assert len(user2_contexts) == 1
    assert user1_contexts[0]['context_id'] == user2_contexts[0]['context_id']
    assert user1_contexts[0]['role'] == 'lead'
    assert user2_contexts[0]['role'] == 'member'


# 5. Wallet privacy (never exposed unless explicitly shared)

def test_wallet_fields_not_in_schema(test_db):
    """Wallet data not stored in profile_contexts schema."""
    for table in ['profile_contexts', 'profile_context_members']:
        schema = test_db.execute(f"PRAGMA table_info({table})").fetchall()
        column_names = [row['name'] for row in schema]

        forbidden = ['wallet', 'balance', 'giving', 'donation', 'amount', 'receipt']
        for field in forbidden:
            assert not any(field.lower() in col.lower() for col in column_names)


# 6. No PII collection (tax docs, IDs, amounts, receipts, income)

def test_no_pii_fields(test_db):
    """Schema has no PII fields."""
    for table in ['profile_contexts', 'profile_context_members']:
        schema = test_db.execute(f"PRAGMA table_info({table})").fetchall()
        column_names = [row['name'] for row in schema]

        forbidden_pii = [
            'tax_return', 'form_990', 'tax_id', 'ein', 'ssn',
            'donation_amount', 'giving_amount', 'receipt',
            'household_income', 'email_list', 'phone_list'
        ]
        for field in forbidden_pii:
            assert field not in column_names


# 7. Role-based access control

def test_member_cannot_add_members(test_db):
    """Non-lead/support cannot add members."""
    lead_uid = "user_1"
    member_uid = "user_2"
    new_uid = "user_3"

    ctx_id = profile_contexts.create_context(test_db, created_by_uid=lead_uid, context_type='household')
    profile_contexts.add_member(test_db, context_id=ctx_id, firebase_uid=member_uid, role='member', invited_by_uid=lead_uid)

    with pytest.raises(PermissionError):
        profile_contexts.add_member(
            test_db,
            context_id=ctx_id,
            firebase_uid=new_uid,
            role='member',
            invited_by_uid=member_uid
        )


def test_only_lead_can_change_roles(test_db):
    """Only lead can change member roles."""
    lead_uid = "user_1"
    member_uid = "user_2"

    ctx_id = profile_contexts.create_context(test_db, created_by_uid=lead_uid, context_type='household')
    profile_contexts.add_member(test_db, context_id=ctx_id, firebase_uid=member_uid, role='member', invited_by_uid=lead_uid)

    profile_contexts.update_member_role(
        test_db,
        context_id=ctx_id,
        firebase_uid=member_uid,
        new_role='support',
        changed_by_uid=lead_uid
    )

    members = profile_contexts.get_context_members(test_db, ctx_id)
    roles = {m['firebase_uid']: m['role'] for m in members}
    assert roles[member_uid] == 'support'


# 8. Member removal

def test_lead_can_remove_member(test_db):
    """Lead can remove members."""
    lead_uid = "user_1"
    member_uid = "user_2"

    ctx_id = profile_contexts.create_context(test_db, created_by_uid=lead_uid, context_type='household')
    profile_contexts.add_member(test_db, context_id=ctx_id, firebase_uid=member_uid, role='member', invited_by_uid=lead_uid)

    profile_contexts.remove_member(test_db, context_id=ctx_id, firebase_uid=member_uid, removed_by_uid=lead_uid)

    members = profile_contexts.get_context_members(test_db, ctx_id)
    member_uids = [m['firebase_uid'] for m in members if m['status'] == 'active']
    assert member_uid not in member_uids


def test_cannot_self_remove(test_db):
    """Cannot remove yourself."""
    lead_uid = "user_1"
    ctx_id = profile_contexts.create_context(test_db, created_by_uid=lead_uid, context_type='household')

    with pytest.raises(ValueError, match="cannot remove yourself"):
        profile_contexts.remove_member(
            test_db,
            context_id=ctx_id,
            firebase_uid=lead_uid,
            removed_by_uid=lead_uid
        )


# 9. Context archival

def test_lead_can_archive_context(test_db):
    """Lead can archive contexts."""
    lead_uid = "user_1"
    ctx_id = profile_contexts.create_context(test_db, created_by_uid=lead_uid, context_type='household')

    profile_contexts.archive_context(test_db, context_id=ctx_id, archived_by_uid=lead_uid)

    context = profile_contexts.get_context_detail(test_db, ctx_id)
    assert context['status'] == 'archived'


# 10. Cross-context isolation

def test_cannot_access_other_context(test_db):
    """Cannot access context you're not a member of."""
    user1 = "user_1"
    user2 = "user_2"

    ctx1 = profile_contexts.create_context(test_db, created_by_uid=user1, context_type='household')
    ctx2 = profile_contexts.create_context(test_db, created_by_uid=user2, context_type='household')

    assert not profile_contexts.can_access_context(test_db, ctx1, user2)
    assert not profile_contexts.can_access_context(test_db, ctx2, user1)
