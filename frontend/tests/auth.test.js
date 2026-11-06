import { test, describe } from "node:test";
import assert from "node:assert/strict";

describe("ACIS Frontend Role-Based Access Control Rules", () => {
  const getPermissions = (role) => {
    const isOwner = role === "organization_owner";
    const isAdmin = isOwner || role === "organization_admin";
    const isAnalyst = isAdmin || role === "analyst";
    const isViewer = isAnalyst || role === "viewer";

    return {
      canCreateResearch: isAnalyst,
      canManageEvidence: isAnalyst,
      canManageUsers: isAdmin,
      canViewReports: isViewer,
    };
  };

  test("organization_owner has all permissions", () => {
    const perms = getPermissions("organization_owner");
    assert.equal(perms.canCreateResearch, true);
    assert.equal(perms.canManageEvidence, true);
    assert.equal(perms.canManageUsers, true);
    assert.equal(perms.canViewReports, true);
  });

  test("organization_admin can manage users, create research, and review evidence", () => {
    const perms = getPermissions("organization_admin");
    assert.equal(perms.canCreateResearch, true);
    assert.equal(perms.canManageEvidence, true);
    assert.equal(perms.canManageUsers, true);
    assert.equal(perms.canViewReports, true);
  });

  test("analyst can create research and review evidence, but cannot manage users", () => {
    const perms = getPermissions("analyst");
    assert.equal(perms.canCreateResearch, true);
    assert.equal(perms.canManageEvidence, true);
    assert.equal(perms.canManageUsers, false);
    assert.equal(perms.canViewReports, true);
  });

  test("viewer can only view reports and research, cannot create or edit", () => {
    const perms = getPermissions("viewer");
    assert.equal(perms.canCreateResearch, false);
    assert.equal(perms.canManageEvidence, false);
    assert.equal(perms.canManageUsers, false);
    assert.equal(perms.canViewReports, true);
  });
});

describe("Strategic Recommendation Timeline Normalization", () => {
  const normalizeTimeHorizon = (horizon) => {
    const map = {
      immediate: "Immediate (0–30 days)",
      "0-30 days": "Immediate (0–30 days)",
      near_term: "Short term (1–3 months)",
      short_term: "Short term (1–3 months)",
      "1-3 months": "Short term (1–3 months)",
      medium_term: "Medium term (3–6 months)",
      "3-6 months": "Medium term (3–6 months)",
      long_term: "Long term (6–12 months)",
      "6-12 months": "Long term (6–12 months)",
    };
    return map[horizon?.toLowerCase()] || "Medium term (3–6 months)";
  };

  test("normalizes immediate horizon to 0–30 days", () => {
    assert.equal(normalizeTimeHorizon("immediate"), "Immediate (0–30 days)");
    assert.equal(normalizeTimeHorizon("0-30 days"), "Immediate (0–30 days)");
  });

  test("normalizes near_term and short_term to 1–3 months", () => {
    assert.equal(normalizeTimeHorizon("near_term"), "Short term (1–3 months)");
    assert.equal(normalizeTimeHorizon("short_term"), "Short term (1–3 months)");
  });

  test("normalizes medium_term to 3–6 months", () => {
    assert.equal(normalizeTimeHorizon("medium_term"), "Medium term (3–6 months)");
  });

  test("normalizes long_term to 6–12 months", () => {
    assert.equal(normalizeTimeHorizon("long_term"), "Long term (6–12 months)");
  });
});
