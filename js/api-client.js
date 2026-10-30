/**
 * ProofVoice - Unified API Client
 *
 * When Django is reachable on port 8000, requests go to /api/v1/.
 * When Django is offline, the client falls back to the local demonstration store.
 *
 * Gnani AI keys must never be stored in frontend JavaScript.
 * Voice calls are proxied through /api/v1/ai/speech-to-text/ and /api/v1/ai/text-to-speech/.
 */

const API_CONFIG = {
  USE_REAL_BACKEND: true,
  BASE_URL: 'http://127.0.0.1:8000/api/v1',
  TIMEOUT_MS: 15000
};

const SESSION_TOKEN_KEY = 'proofvoice_auth_token';
const SESSION_USER_KEY = 'proofvoice_session_user';
const SESSION_ROLE_KEY = 'proofvoice_active_role';
const SESSION_TENANT_KEY = 'proofvoice_active_tenant';
const PREFER_DEMO_KEY = 'proofvoice_prefer_demo';

function formatApiErrorPayload(errorData) {
  if (!errorData) return 'Request failed.';
  if (typeof errorData === 'string') return errorData;
  if (errorData.detail) return String(errorData.detail);
  if (errorData.error) return String(errorData.error);
  if (errorData.message) return String(errorData.message);
  const parts = [];
  Object.keys(errorData).forEach((key) => {
    const value = errorData[key];
    const label = key === 'non_field_errors' ? '' : key.replace(/_/g, ' ') + ': ';
    let text = '';
    if (Array.isArray(value)) {
      text = value.map((item) => (typeof item === 'string' ? item : JSON.stringify(item))).join(' ');
    } else if (value && typeof value === 'object') {
      text = formatApiErrorPayload(value);
    } else {
      text = String(value);
    }
    parts.push((label + text).trim());
  });
  return parts.join('. ') || 'Request failed.';
}

function titleCaseStatus(status) {
  if (!status) return '';
  return String(status).replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

function mapBackendRole(role) {
  const r = String(role || '').toUpperCase();
  if (r === 'PLATFORM_SUPERADMIN' || r === 'SUPERADMIN') return 'superadmin';
  if (r === 'INSTITUTION_ADMIN' || r === 'ADMIN') return 'admin';
  return 'student';
}

function initialsFromName(fullName) {
  return String(fullName || '')
    .split(' ')
    .map((n) => n[0])
    .filter(Boolean)
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

class ProofVoiceApiClient {
  constructor() {
    this.config = API_CONFIG;
    if (localStorage.getItem(PREFER_DEMO_KEY) === 'true') {
      this.config.USE_REAL_BACKEND = false;
    } else {
      this.checkBackendHealth();
    }
  }

  async checkBackendHealth() {
    try {
      const res = await fetch(`${this.config.BASE_URL}/institutions/`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000)
      });
      if (res.ok) {
        this.config.USE_REAL_BACKEND = true;
        console.log('[ProofVoice API] Connected to live Django backend at ' + this.config.BASE_URL);
      }
    } catch (e) {
      console.warn('[ProofVoice API] Django backend not detected on :8000, falling back to local demo store.');
      this.config.USE_REAL_BACKEND = false;
    }
  }

  isLiveSession() {
    const token = localStorage.getItem(SESSION_TOKEN_KEY);
    return Boolean(this.config.USE_REAL_BACKEND && token && !String(token).startsWith('demo_token_'));
  }

  persistSession(token, user, institution) {
    if (token) {
      localStorage.setItem(SESSION_TOKEN_KEY, token);
    }
    if (user) {
      localStorage.setItem(SESSION_USER_KEY, JSON.stringify(user));
      localStorage.setItem(SESSION_ROLE_KEY, user.role);
    }
    if (institution && institution.code) {
      localStorage.setItem(SESSION_TENANT_KEY, institution.code);
    }
  }

  clearSession() {
    localStorage.removeItem(SESSION_TOKEN_KEY);
    localStorage.removeItem(SESSION_USER_KEY);
    localStorage.removeItem(SESSION_ROLE_KEY);
    localStorage.removeItem(SESSION_TENANT_KEY);
  }

  getStoredUser() {
    try {
      const raw = localStorage.getItem(SESSION_USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  getToken() {
    return localStorage.getItem(SESSION_TOKEN_KEY);
  }

  normalizeUser(payload) {
    const data = payload || {};
    const user = data.user || data;
    const profile = user.student_profile || user.admin_profile || {};
    const institution = data.institution || null;
    const fullName = user.full_name || user.fullName || '';
    let profileImage = user.profile_image_url || user.profile_image || profile.profile_image || null;
    if (profileImage && typeof profileImage === 'string' && profileImage.startsWith('/')) {
      profileImage = `http://127.0.0.1:8000${profileImage}`;
    }
    return {
      id: user.id,
      email: user.email,
      fullName,
      role: mapBackendRole(user.role || data.role),
      backendRole: user.role || data.role,
      institutionId: profile.institution || (institution && institution.id) || null,
      institutionName: profile.institution_name || (institution && institution.name) || '',
      institutionCode: profile.institution_code || (institution && institution.code) || '',
      studentIdentifier: profile.student_id || '',
      department: profile.department || '',
      course: profile.course || '',
      yearSemester: profile.semester || '',
      residentialAddress: profile.address || '',
      phone: profile.phone || '',
      designation: profile.designation || '',
      profileImage,
      avatar: initialsFromName(fullName),
      profileComplete: Boolean(profile.is_profile_complete),
      isApproved: data.is_approved !== false
    };
  }

  normalizeComplaint(c) {
    if (!c) return null;
    const historySource = c.status_history || c.history || [];
    return {
      id: c.complaint_id || c.id,
      numericId: c.id,
      title: c.title,
      location: c.full_issue_location || c.location || '',
      category: c.category_name || c.category || 'General',
      status: titleCaseStatus(c.status),
      rawStatus: c.status,
      priority: titleCaseStatus(c.priority || 'MEDIUM'),
      submittedAt: c.submission_timestamp || c.created_at || c.submittedAt,
      assignedDepartment: c.assigned_department_name || c.department_name || c.assignedDepartment || '',
      studentName: c.student_name || c.studentName || '',
      studentIdentifier: c.student_email || c.studentIdentifier || '',
      originalTranscription: c.original_description || c.original_transcription || c.originalTranscription || '',
      formalApplication: c.final_submitted_application || c.formalApplication || '',
      resolutionSummary: c.resolution_details || c.resolutionSummary || '',
      originalInputMethod: String(c.source_type || c.originalInputMethod || 'TEXT').toLowerCase() === 'voice' ? 'voice' : 'text',
      recipientAuthority: c.recipientAuthority || 'The Dean',
      history: historySource.map((h) => ({
        status: titleCaseStatus(h.new_status || h.status),
        timestamp: h.timestamp,
        actor: h.changed_by_name || h.actor || 'System',
        remarks: h.public_remark || h.remarks || ''
      }))
    };
  }

  unwrapList(data) {
    if (!data) return [];
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.results)) return data.results;
    if (Array.isArray(data.notifications)) return data.notifications;
    if (Array.isArray(data.complaints)) return data.complaints;
    if (Array.isArray(data.users)) return data.users;
    if (Array.isArray(data.departments)) return data.departments;
    if (Array.isArray(data.categories)) return data.categories;
    return [];
  }

  getHeaders() {
    const token = localStorage.getItem(SESSION_TOKEN_KEY);
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
    if (token && !String(token).startsWith('demo_token_')) {
      headers.Authorization = `Token ${token}`;
    }
    return headers;
  }

  async handleResponse(response) {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errMessage = formatApiErrorPayload(errorData) || `HTTP ${response.status}`;
      const err = new Error(errMessage);
      err.status = response.status;
      err.data = errorData;
      throw err;
    }
    if (response.status === 204) return {};
    const contentType = response.headers.get('Content-Type') || '';
    if (contentType.includes('application/json')) {
      return response.json();
    }
    return response;
  }

  async login(email, password, roleHint) {
    if (this.config.USE_REAL_BACKEND) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/auth/login/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await this.handleResponse(res);
        const user = this.normalizeUser(data);
        if (data.token) {
          this.persistSession(data.token, user, data.institution);
        }
        return { ...data, user, role: user.role, success: true };
      } catch (err) {
        const isNetworkErr = !err.status && (
          !err.data ||
          (err.message && /failed to fetch|networkerror|load failed|fetch failed|refused|abort/i.test(err.message))
        );
        if (isNetworkErr) {
          console.warn('[ProofVoice API] Django backend unreachable on :8000. Falling back to demonstration mode.');
          this.config.USE_REAL_BACKEND = false;
          return {
            ...this.demoLogin(roleHint),
            isOfflineFallback: true
          };
        }
        throw err;
      }
    }
    return this.demoLogin(roleHint);
  }

  demoLogin(roleHint) {
    const db = window.proofVoiceDb;
    const user = db.switchRole(roleHint || 'student');
    return {
      success: true,
      token: 'demo_token_' + Date.now(),
      user,
      role: roleHint ? roleHint.toLowerCase() : 'student'
    };
  }

  async logout() {
    if (this.isLiveSession()) {
      try {
        await fetch(`${this.config.BASE_URL}/auth/logout/`, {
          method: 'POST',
          headers: this.getHeaders()
        });
      } catch (e) {
        // Token is still cleared locally even if the network call fails.
      }
    }
    this.clearSession();
    return { success: true };
  }

  async registerStudent(payload) {
    if (this.config.USE_REAL_BACKEND) {
      const password = payload.password;
      if (!password) {
        throw new Error('Password is required.');
      }
      const backendPayload = {
        email: payload.email,
        password,
        full_name: payload.fullName,
        institution_id: payload.institutionId ? parseInt(payload.institutionId, 10) : null,
        student_id: payload.studentIdentifier || '',
        department: payload.department || '',
        course: payload.course || payload.department || '',
        semester: payload.yearSemester || '',
        phone: payload.phone || '',
        address: payload.residentialAddress || ''
      };

      const res = await fetch(`${this.config.BASE_URL}/auth/register/student/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(backendPayload)
      });
      const data = await this.handleResponse(res);
      const user = this.normalizeUser(data);
      if (data.token) {
        this.persistSession(data.token, user, data.institution);
      }
      // Also register student into local store so campus users desk sees the record immediately
      try {
        const db = window.proofVoiceDb;
        if (db) {
          const dbData = db.getDb();
          const studentEntry = {
            id: user.id || ('usr_student_' + Date.now()),
            role: 'student',
            fullName: user.fullName || payload.fullName,
            email: user.email || payload.email,
            institutionId: user.institutionId || payload.institutionId,
            studentIdentifier: user.studentIdentifier || payload.studentIdentifier || 'AIT-STU',
            studentId: user.studentIdentifier || payload.studentIdentifier || 'AIT-STU',
            identifier: user.studentIdentifier || payload.studentIdentifier || 'AIT-STU',
            department: user.department || payload.department || 'General Campus',
            yearSemester: payload.yearSemester || '',
            residentialAddress: payload.residentialAddress || '',
            phone: payload.phone || '',
            avatar: initialsFromName(user.fullName || payload.fullName),
            status: 'verified',
            profileComplete: true,
            registeredAt: new Date().toISOString()
          };
          const existingIdx = (dbData.users || []).findIndex(u => u.email === user.email || String(u.id) === String(user.id));
          if (existingIdx >= 0) {
            dbData.users[existingIdx] = studentEntry;
          } else {
            dbData.users.unshift(studentEntry);
          }
          db.saveDb(dbData);
        }
      } catch (e) {}
      return { ...data, user, success: true };
    }

    const db = window.proofVoiceDb;
    const newStudentUser = {
      id: 'usr_student_' + Date.now(),
      role: 'student',
      fullName: payload.fullName,
      email: payload.email,
      institutionId: payload.institutionId,
      studentIdentifier: payload.studentIdentifier || '',
      department: payload.department || '',
      yearSemester: payload.yearSemester || '',
      residentialAddress: payload.residentialAddress || '',
      phone: payload.phone || '',
      avatar: initialsFromName(payload.fullName),
      status: payload.studentIdentifier ? 'verified' : 'pending_verification',
      profileComplete: Boolean(payload.residentialAddress && payload.studentIdentifier),
      registeredAt: new Date().toISOString()
    };

    const dbData = db.getDb();
    dbData.users.push(newStudentUser);
    dbData.currentSession.userId = newStudentUser.id;
    dbData.currentSession.role = 'student';
    dbData.currentSession.institutionId = payload.institutionId;
    db.saveDb(dbData);

    return {
      success: true,
      message: 'Student registered.',
      user: newStudentUser
    };
  }

  async registerAdmin(payload) {
    if (this.config.USE_REAL_BACKEND) {
      const res = await fetch(`${this.config.BASE_URL}/auth/register/institution-admin/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({
          email: payload.email,
          password: payload.password,
          full_name: payload.fullName,
          institution_id: parseInt(payload.institutionId, 10),
          designation: payload.designation || 'Staff Administrator',
          department_name: payload.departmentName || ''
        })
      });
      const data = await this.handleResponse(res);
      const user = this.normalizeUser(data);
      if (data.token) {
        this.persistSession(data.token, user, data.institution);
      }
      // Also register administrator into local store
      try {
        const db = window.proofVoiceDb;
        if (db) {
          const dbData = db.getDb();
          const adminEntry = {
            id: user.id || ('usr_admin_' + Date.now()),
            role: 'admin',
            fullName: user.fullName || payload.fullName,
            email: user.email || payload.email,
            institutionId: user.institutionId || payload.institutionId,
            studentId: 'STAFF-AUTH',
            identifier: 'STAFF-AUTH',
            department: payload.departmentName || payload.designation || 'Academic Administration',
            designation: payload.designation || 'Staff Administrator',
            avatar: initialsFromName(user.fullName || payload.fullName),
            status: 'verified',
            profileComplete: true,
            registeredAt: new Date().toISOString()
          };
          const existingIdx = (dbData.users || []).findIndex(u => u.email === user.email || String(u.id) === String(user.id));
          if (existingIdx >= 0) {
            dbData.users[existingIdx] = adminEntry;
          } else {
            dbData.users.unshift(adminEntry);
          }
          db.saveDb(dbData);
        }
      } catch (e) {}
      return { ...data, user, success: true };
    }
    return { success: false, message: 'Administrator registration requires the Django backend.' };
  }

  async getCurrentUser() {
    if (this.isLiveSession()) {
      const res = await fetch(`${this.config.BASE_URL}/auth/me/`, {
        headers: this.getHeaders()
      });
      const data = await this.handleResponse(res);
      const user = this.normalizeUser(data);
      this.persistSession(localStorage.getItem(SESSION_TOKEN_KEY), user, null);
      return user;
    }
    return window.proofVoiceDb.getCurrentUser();
  }

  async updateUserProfile(userId, profileData) {
    if (this.isLiveSession()) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/auth/profile/`, {
          method: 'PATCH',
          headers: this.getHeaders(),
          body: JSON.stringify({
            full_name: profileData.fullName || profileData.full_name,
            student_id: profileData.studentIdentifier || profileData.student_id,
            institution_id: profileData.institutionId || profileData.institution_id,
            department: profileData.department,
            course: profileData.course || profileData.department,
            semester: profileData.yearSemester || profileData.semester,
            phone: profileData.phone,
            address: profileData.residentialAddress || profileData.address,
            designation: profileData.designation
          })
        });
        const data = await this.handleResponse(res);
        const stored = this.getStoredUser() || {};
        if (data && data.user) {
          const normalized = this.normalizeUser(data.user);
          const merged = { ...stored, ...normalized };
          if (!merged.profileImage && stored.profileImage) {
            merged.profileImage = stored.profileImage;
          }
          localStorage.setItem(SESSION_USER_KEY, JSON.stringify(merged));
        }
        return data;
      } catch (err) {
        console.warn('[ProofVoice API] Live updateUserProfile failed, saving locally:', err);
      }
    }
    return window.proofVoiceDb.updateUserProfile(userId, profileData);
  }

  async uploadProfilePhoto(file) {
    if (this.isLiveSession()) {
      try {
        const formData = new FormData();
        formData.append('photo', file);
        const token = this.getToken();
        const headers = {};
        if (token && !String(token).startsWith('demo_token_')) {
          headers.Authorization = `Token ${token}`;
        }
        const res = await fetch(`${this.config.BASE_URL}/auth/profile/photo/`, {
          method: 'POST',
          headers,
          body: formData
        });
        const data = await this.handleResponse(res);
        const currentUser = this.getStoredUser() || (window.proofVoiceDb ? window.proofVoiceDb.getCurrentUser() : null);
        if (currentUser && data.profile_image_url) {
          currentUser.profileImage = data.profile_image_url;
          localStorage.setItem(SESSION_USER_KEY, JSON.stringify(currentUser));
        }
        if (window.proofVoiceDb && currentUser) {
          try {
            const dbData = window.proofVoiceDb.getDb();
            const target = dbData.users.find(u => u.id === currentUser.id || u.email === currentUser.email);
            if (target) {
              target.profileImage = data.profile_image_url;
              window.proofVoiceDb.saveDb(dbData);
            }
          } catch (e) {}
        }
        return data;
      } catch (err) {
        // If it was a real validation error from Django (e.g. status 400), throw so UI shows detail
        if (err && err.message && !err.message.includes('Failed to fetch') && !err.message.includes('NetworkError') && !err.message.includes('fetch')) {
          throw err;
        }
        console.warn('[ProofVoice API] Live photo upload failed with network error, saving photo locally:', err);
      }
    }

    // Graceful offline fallback: convert file to data-URL and store in browser storage
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const photoUrl = e.target.result;
        const currentUser = this.getStoredUser() || (window.proofVoiceDb ? window.proofVoiceDb.getCurrentUser() : null);
        if (currentUser) {
          currentUser.profileImage = photoUrl;
          localStorage.setItem(SESSION_USER_KEY, JSON.stringify(currentUser));
          if (window.proofVoiceDb) {
            try {
              const dbData = window.proofVoiceDb.getDb();
              const target = dbData.users.find(u => u.id === currentUser.id || u.email === currentUser.email);
              if (target) {
                target.profileImage = photoUrl;
                window.proofVoiceDb.saveDb(dbData);
              }
            } catch (err) {}
          }
        }
        resolve({ success: true, profile_image_url: photoUrl });
      };
      reader.readAsDataURL(file);
    });
  }

  async removeProfilePhoto() {
    if (this.isLiveSession()) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/auth/profile/photo/`, {
          method: 'DELETE',
          headers: this.getHeaders()
        });
        await this.handleResponse(res);
      } catch (err) {
        console.warn('[ProofVoice API] Live removeProfilePhoto failed, removing locally:', err);
      }
    }
    const currentUser = this.getStoredUser() || (window.proofVoiceDb ? window.proofVoiceDb.getCurrentUser() : null);
    if (currentUser) {
      currentUser.profileImage = null;
      localStorage.setItem(SESSION_USER_KEY, JSON.stringify(currentUser));
    }
    if (window.proofVoiceDb && currentUser) {
      try {
        const dbData = window.proofVoiceDb.getDb();
        const target = dbData.users.find(u => u.id === currentUser.id || u.email === currentUser.email);
        if (target) {
          target.profileImage = null;
          window.proofVoiceDb.saveDb(dbData);
        }
      } catch (e) {}
    }
    return { success: true, message: 'Profile photo removed successfully.', profile_image_url: null };
  }

  async processGrievanceWithAi(text) {
    if (this.config.USE_REAL_BACKEND) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/ai/process/`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify({ text })
        });
        if (res.ok) {
          const data = await res.json();
          return data.data || data;
        }
      } catch (e) {
        console.warn('AI processing call fallback:', e);
      }
    }
    return {
      title: 'Campus Grievance Application',
      category: 'OTHER',
      suggested_department: 'Student Affairs',
      suggested_priority: 'MEDIUM',
      confidence: 0.85,
      summary: text ? text.slice(0, 140) : '',
      refined_description: text || ''
    };
  }

  async refineTextWithAi(text) {
    if (this.config.USE_REAL_BACKEND) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/ai/refine/`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify({ text })
        });
        if (res.ok) {
          const data = await res.json();
          return data.refined_text || text;
        }
      } catch (e) {
        console.warn('AI refine call fallback:', e);
      }
    }
    return text;
  }

  async getInstitutions() {
    if (this.config.USE_REAL_BACKEND) {
      const res = await fetch(`${this.config.BASE_URL}/institutions/`, {
        headers: { 'Accept': 'application/json' }
      });
      const data = await this.handleResponse(res);
      return this.unwrapList(data);
    }
    return window.proofVoiceDb.getInstitutions();
  }

  async requestInstitution(payload) {
    if (this.config.USE_REAL_BACKEND) {
      const res = await fetch(`${this.config.BASE_URL}/institutions/registration-requests/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          institution_name: payload.name || payload.institution_name,
          institution_type: (payload.type || payload.institution_type || 'UNIVERSITY').toUpperCase(),
          official_email: payload.officialEmail || payload.official_email,
          official_address: payload.officialAddress || payload.official_address,
          state: payload.state || '',
          city: payload.city || '',
          website: payload.website || '',
          applicant_designation: payload.contactDesignation || payload.applicant_designation || 'Administrator'
        })
      });
      return this.handleResponse(res);
    }
    const inst = window.proofVoiceDb.requestInstitution(payload);
    return { success: true, institution: inst, status: 'pending_review' };
  }

  async requestAdminAccess(payload) {
    if (this.config.USE_REAL_BACKEND) {
      return this.registerAdmin({
        email: payload.officialEmail || payload.email,
        password: payload.password,
        fullName: payload.fullName,
        institutionId: payload.institutionId,
        designation: payload.designation,
        departmentName: payload.department || payload.departmentName
      });
    }
    const req = window.proofVoiceDb.requestAdminAccess(payload);
    return { success: true, request: req, status: 'pending_approval' };
  }

  async getComplaints(filter = {}, forceRole = null) {
    if (this.isLiveSession()) {
      const query = new URLSearchParams();
      if (filter.status && filter.status !== 'All' && filter.status !== 'Unassigned') {
        query.set('status', String(filter.status).replace(/\s+/g, '_').toUpperCase());
      }
      if (filter.search) {
        query.set('search', filter.search);
      }
      const qs = query.toString();
      const user = this.getStoredUser() || {};
      const isAdmin = forceRole === 'admin' || user.role === 'admin' || user.role === 'superadmin' || user.backendRole === 'INSTITUTION_ADMIN';
      const endpoint = isAdmin
        ? `${this.config.BASE_URL}/admin/complaints/`
        : `${this.config.BASE_URL}/complaints/`;

      try {
        let res = await fetch(`${endpoint}${qs ? '?' + qs : ''}`, {
          headers: this.getHeaders()
        });
        if (!res.ok && isAdmin && (res.status === 404 || res.status === 403)) {
          // Fallback to /complaints/
          res = await fetch(`${this.config.BASE_URL}/complaints/${qs ? '?' + qs : ''}`, {
            headers: this.getHeaders()
          });
        }
        const data = await this.handleResponse(res);
        let list = this.unwrapList(data).map((item) => this.normalizeComplaint(item));
        if (filter.category && filter.category !== 'All') {
          list = list.filter((c) => c.category === filter.category);
        }
        if (filter.department && filter.department !== 'All') {
          list = list.filter((c) => c.assignedDepartment === filter.department);
        }
        if (filter.status === 'Unassigned') {
          list = list.filter((c) => !c.assignedDepartment || c.assignedDepartment === 'Unassigned');
        }
        return list;
      } catch (err) {
        console.warn('[ProofVoice API] Live complaints query failed, using local demo store:', err);
        return window.proofVoiceDb.getComplaints(filter, forceRole || (isAdmin ? 'admin' : null));
      }
    }
    return window.proofVoiceDb.getComplaints(filter, forceRole);
  }

  async getComplaint(id, forceRole = null) {
    if (this.isLiveSession()) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/complaints/${id}/`, {
          headers: this.getHeaders()
        });
        if (res.ok) {
          const data = await this.handleResponse(res);
          return this.normalizeComplaint(data);
        }
      } catch (e) {
        console.warn('[ProofVoice API] Live complaint by ID failed, falling back to local store:', e);
      }
    }
    const complaint = window.proofVoiceDb.getComplaintById(id, forceRole);
    if (!complaint) throw new Error('Complaint not found or unauthorized.');
    return complaint;
  }

  async generateApplication(data) {
    if (this.isLiveSession()) {
      const res = await fetch(`${this.config.BASE_URL}/complaints/generate-application/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data)
      });
      return this.handleResponse(res);
    }
    return null;
  }

  async submitComplaint(complaintData) {
    if (this.isLiveSession()) {
      const res = await fetch(`${this.config.BASE_URL}/complaints/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          title: complaintData.title,
          original_description: complaintData.originalDescription || complaintData.originalTranscription || complaintData.description,
          original_transcription: complaintData.originalTranscription || '',
          final_submitted_application: complaintData.finalApplicationLetter || complaintData.formalApplication || complaintData.final_submitted_application || '',
          category: complaintData.category || complaintData.categoryName || '',
          category_id: complaintData.categoryId ? parseInt(complaintData.categoryId, 10) : null,
          priority: complaintData.priority ? String(complaintData.priority).toUpperCase() : 'MEDIUM',
          source_type: (complaintData.sourceType || complaintData.originalInputMethod || 'TEXT').toString().toUpperCase() === 'VOICE' ? 'VOICE' : 'TEXT',
          building: complaintData.locationBuilding || complaintData.building || '',
          floor: complaintData.locationFloor || complaintData.floor || '',
          room_number: complaintData.locationRoom || complaintData.room_number || '',
          full_issue_location: complaintData.location || complaintData.full_issue_location || '',
          submit_now: true
        })
      });
      const data = await this.handleResponse(res);
      const normalized = this.normalizeComplaint(data.complaint || data);
      if (normalized && normalized.id) {
        sessionStorage.setItem('proofvoice_current_complaint_id', normalized.id);
        localStorage.setItem('proofvoice_last_viewed_complaint_id', normalized.id);
      }
      // Keep local store in sync for offline viewing and cross-tab viewing
      try {
        if (window.proofVoiceDb) {
          window.proofVoiceDb.addComplaint({
            ...complaintData,
            id: normalized.id,
            complaint_id: normalized.id,
            numericId: normalized.numericId,
            status: normalized.status || 'Submitted',
            title: normalized.title,
            category: normalized.category,
            location: normalized.location,
            formalApplication: normalized.formalApplication || complaintData.formalApplication,
            originalTranscription: normalized.originalTranscription || complaintData.originalTranscription,
            submittedAt: normalized.submittedAt || new Date().toISOString()
          });
        }
      } catch (e) {}
      return normalized;
    }
    return window.proofVoiceDb.addComplaint(complaintData);
  }

  async updateComplaintStatus(id, newStatus, publicRemark, internalNote, department, assignedTo) {
    let liveUpdated = null;
    if (this.isLiveSession()) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/admin/complaints/${id}/status/`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify({
            status: String(newStatus).replace(/\s+/g, '_').toUpperCase(),
            public_remark: publicRemark,
            internal_note: internalNote,
            department: department,
            assigned_to: assignedTo
          })
        });
        if (res.ok) {
          liveUpdated = await this.handleResponse(res);
        }
      } catch (err) {
        console.warn('[ProofVoice API] Live status update error, syncing local store:', err);
      }
    }
    const localUpdated = window.proofVoiceDb.updateComplaintStatus(id, newStatus, publicRemark, internalNote, department, assignedTo);
    return liveUpdated || localUpdated;
  }

  async reopenComplaint(id, reason) {
    let liveReopened = null;
    if (this.isLiveSession()) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/complaints/${id}/reopen/`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify({ reason })
        });
        if (res.ok) {
          liveReopened = await this.handleResponse(res);
        }
      } catch (err) {
        console.warn('[ProofVoice API] Live reopen call failed, saving locally:', err);
      }
    }
    const localReopened = window.proofVoiceDb.reopenComplaint(id, reason);
    return liveReopened || localReopened;
  }

  async speechToText(audioBlob, languageCode = 'en-IN') {
    if (this.config.USE_REAL_BACKEND) {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');
      formData.append('language_code', languageCode);
      const token = localStorage.getItem(SESSION_TOKEN_KEY);
      const headers = {};
      if (token && !String(token).startsWith('demo_token_')) {
        headers.Authorization = `Token ${token}`;
      }
      try {
        const res = await fetch(`${this.config.BASE_URL}/ai/speech-to-text/`, {
          method: 'POST',
          headers,
          body: formData
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          return {
            success: false,
            status: res.status,
            is_configured: data.is_configured,
            error: data.error || data.detail || `Backend responded with HTTP ${res.status}`
          };
        }
        return data;
      } catch (err) {
        return {
          success: false,
          error: err.message || 'Network error reaching speech-to-text service'
        };
      }
    }
    return {
      success: true,
      transcript: 'The ceiling projector in Computer Lab 304 has had intermittent power flickering and shuts off during our practical sessions. Please send the technician to inspect and fix the HDMI splitter.',
      confidence: 0.94,
      isDemo: true,
      connectedToGnaniAi: false
    };
  }

  async textToSpeech(text, complaintId) {
    if (this.config.USE_REAL_BACKEND) {
      const res = await fetch(`${this.config.BASE_URL}/ai/text-to-speech/`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ text, complaint_id: complaintId })
      });
      if (res.headers.get('Content-Type')?.includes('audio')) {
        const blob = await res.blob();
        return URL.createObjectURL(blob);
      }
      const data = await this.handleResponse(res);
      return data.audio_url || null;
    }
    return null;
  }

  async getNotifications() {
    if (this.isLiveSession()) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/notifications/`, {
          headers: this.getHeaders()
        });
        if (res.ok) {
          const data = await this.handleResponse(res);
          const notifs = this.unwrapList(data);
          const unreadCount = (data && data.unread_count !== undefined) 
            ? data.unread_count 
            : notifs.filter(n => !n.is_read && !n.read).length;
          
          if (window.updateNotificationBadges) {
            window.updateNotificationBadges(unreadCount);
          }
          return notifs;
        }
      } catch (err) {
        console.warn('[ProofVoice API] Live notifications error, falling back:', err);
      }
    }
    const localNotifs = window.proofVoiceDb ? window.proofVoiceDb.getNotifications() : [];
    if (window.updateNotificationBadges) {
      window.updateNotificationBadges(localNotifs.filter(n => !n.read && !n.is_read).length);
    }
    return localNotifs;
  }

  async markNotificationRead(id) {
    if (this.isLiveSession()) {
      try {
        if (!isNaN(id) || String(id).match(/^\d+$/)) {
          await fetch(`${this.config.BASE_URL}/notifications/${id}/read/`, {
            method: 'POST',
            headers: this.getHeaders()
          });
        }
      } catch (e) {
        console.warn('[ProofVoice API] Live mark read error:', e);
      }
    }
    if (window.proofVoiceDb) {
      window.proofVoiceDb.markNotificationRead(id);
    }
    const currentUnread = parseInt(localStorage.getItem('proofvoice_unread_count') || '1', 10);
    const newCount = Math.max(0, currentUnread - 1);
    if (window.updateNotificationBadges) {
      window.updateNotificationBadges(newCount);
    }
    return { success: true };
  }

  async markAllNotificationsRead() {
    if (this.isLiveSession()) {
      try {
        await fetch(`${this.config.BASE_URL}/notifications/read-all/`, {
          method: 'POST',
          headers: this.getHeaders()
        });
      } catch (e) {
        console.warn('[ProofVoice API] Live mark all read error:', e);
      }
    }
    if (window.proofVoiceDb) {
      window.proofVoiceDb.markAllNotificationsRead();
    }
    if (window.updateNotificationBadges) {
      window.updateNotificationBadges(0);
    }
    return { success: true };
  }

  async getCampusUsers(role = null, search = null) {
    if (this.isLiveSession()) {
      try {
        const query = new URLSearchParams();
        if (role && role !== 'All') query.set('role', role);
        if (search) query.set('search', search);
        const qs = query.toString();
        const res = await fetch(`${this.config.BASE_URL}/users/${qs ? '?' + qs : ''}`, {
          headers: this.getHeaders()
        });
        if (res.ok) {
          const data = await this.handleResponse(res);
          return this.unwrapList(data);
        }
      } catch (e) {
        console.warn('[ProofVoice API] Live campus users error:', e);
      }
    }
    return [];
  }

  async getDepartments() {
    let list = [];
    if (this.isLiveSession()) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/institutions/me/departments/`, {
          headers: this.getHeaders()
        });
        if (res.ok) {
          const data = await this.handleResponse(res);
          list = this.unwrapList(data);
        }
      } catch (e) {
        console.warn('[ProofVoice API] Live departments query failed:', e);
      }
    }
    // Always merge any custom departments saved locally
    try {
      const customDepts = JSON.parse(localStorage.getItem('proofvoice_custom_departments') || '[]');
      customDepts.forEach(cd => {
        if (cd && !list.some(item => (item.name || item) === cd)) {
          list.push({ id: `cust_${Date.now()}`, name: cd });
        }
      });
    } catch (e) {}
    return list;
  }

  async addDepartment(name, contactEmail = '') {
    // Save to local custom departments cache first
    try {
      let customDepts = JSON.parse(localStorage.getItem('proofvoice_custom_departments') || '[]');
      if (!customDepts.includes(name)) {
        customDepts.push(name);
        localStorage.setItem('proofvoice_custom_departments', JSON.stringify(customDepts));
      }
    } catch (e) {}

    if (this.isLiveSession()) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/institutions/me/departments/`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify({ name, contact_email: contactEmail })
        });
        if (res.ok) {
          return await this.handleResponse(res);
        }
      } catch (e) {
        console.warn('[ProofVoice API] Live add department failed:', e);
      }
    }
    return { name, contact_email: contactEmail, is_active: true };
  }
}

window.proofVoiceApi = new ProofVoiceApiClient();
window.formatApiErrorPayload = formatApiErrorPayload;
window.mapBackendRole = mapBackendRole;
window.titleCaseStatus = titleCaseStatus;
