"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import {
  login as apiLogin,
  logout as apiLogout,
  refreshAccessToken,
  getOrganizations,
  setOrganizationId,
  getOrganizationId,
  health,
} from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [currentOrgId, setCurrentOrgId] = useState(null);
  const [currentOrg, setCurrentOrg] = useState(null);
  const [role, setRole] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isBackendHealthy, setIsBackendHealthy] = useState(null);
  const [authError, setAuthError] = useState(null);

  // Restore session on mount
  const checkSession = useCallback(async () => {
    setIsLoading(true);
    setAuthError(null);
    try {
      // 1. Health check
      try {
        await health();
        setIsBackendHealthy(true);
      } catch {
        setIsBackendHealthy(false);
      }

      // 2. Try refresh
      const token = await refreshAccessToken();
      if (!token) {
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      // 3. Fetch user organizations
      const orgs = await getOrganizations();
      setOrganizations(orgs || []);

      if (orgs && orgs.length > 0) {
        const savedOrgId = getOrganizationId();
        const active = orgs.find((o) => o.organization_id === savedOrgId) || orgs[0];
        setCurrentOrgId(active.organization_id);
        setCurrentOrg(active);
        setRole(active.role);
        setOrganizationId(active.organization_id);
      }

      setIsAuthenticated(true);
    } catch (err) {
      setIsAuthenticated(false);
      setAuthError(err.message || "Failed to restore session.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  const login = async (email, password) => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const data = await apiLogin(email, password);
      setUser(data.user || null);

      const orgs = await getOrganizations();
      setOrganizations(orgs || []);

      if (orgs && orgs.length > 0) {
        const active = orgs[0];
        setCurrentOrgId(active.organization_id);
        setCurrentOrg(active);
        setRole(active.role);
        setOrganizationId(active.organization_id);
      }

      setIsAuthenticated(true);
      return data;
    } catch (err) {
      setAuthError(err.message || "Sign in failed.");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await apiLogout();
    } finally {
      setUser(null);
      setOrganizations([]);
      setCurrentOrgId(null);
      setCurrentOrg(null);
      setRole(null);
      setIsAuthenticated(false);
      setIsLoading(false);
    }
  };

  const switchOrganization = (orgId) => {
    const target = organizations.find((o) => o.organization_id === orgId);
    if (target) {
      setCurrentOrgId(target.organization_id);
      setCurrentOrg(target);
      setRole(target.role);
      setOrganizationId(target.organization_id);
    }
  };

  // RBAC Permission helpers
  const isOwner = role === "organization_owner";
  const isAdmin = isOwner || role === "organization_admin";
  const isAnalyst = isAdmin || role === "analyst";
  const isViewer = isAnalyst || role === "viewer";

  const canCreateResearch = isAnalyst;
  const canManageEvidence = isAnalyst;
  const canManageUsers = isAdmin;
  const canViewReports = isViewer;

  const value = {
    user,
    organizations,
    currentOrgId,
    currentOrg,
    role,
    isAuthenticated,
    isLoading,
    isBackendHealthy,
    authError,
    login,
    logout,
    switchOrganization,
    checkSession,
    isOwner,
    isAdmin,
    isAnalyst,
    isViewer,
    canCreateResearch,
    canManageEvidence,
    canManageUsers,
    canViewReports,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
