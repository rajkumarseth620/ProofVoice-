/**
 * ProofVoice - Unified API Client
 *
 * When Django is reachable on port 8000, requests go to /api/v1/.
 * When Django is offline, the client falls back to the local demonstration store.
 *
 * Gnani AI keys must never be stored in frontend JavaScript.
 * Voice calls are proxied through /api/v1/ai/speech-to-text/ and /api/v1/ai/text-to-speech/.
 */

/**
 * ProofVoice API Configuration
 *
 * Supports two environments:
 * 1. Local development: http://127.0.0.1:8000/api/v1
 * 2. Production: A configurable HTTPS Django backend URL (e.g. deployed on Render).
 *
 * To point to your deployed production backend, you can:
 * - Set the PRODUCTION_BACKEND_URL constant below, OR
 * - Define window.PROOFVOICE_API_BASE in a script, OR
 * - Set in browser console: localStorage.setItem('proofvoice_api_base_url', 'https://<your-backend>.onrender.com')
 */
const PRODUCTION_BACKEND_URL = ''; // Leave empty until backend is deployed, then paste your Render HTTPS URL here
const LOCAL_BACKEND_URL = 'http://127.0.0.1:8000/api/v1';

function resolveApiBaseUrl() {
  // 1. Runtime override via window global
  if (typeof window !== 'undefined' && window.PROOFVOICE_API_BASE) {
    const base = String(window.PROOFVOICE_API_BASE).trim().replace(/\/+$/, '');
    return base.endsWith('/api/v1') ? base : `${base}/api/v1`;
  }

  // 2. Runtime override via localStorage (enables live switching to production backend without code redeploy)
  if (typeof localStorage !== 'undefined') {
    const custom = localStorage.getItem('proofvoice_api_base_url');
    if (custom && custom.trim()) {
      const base = custom.trim().replace(/\/+$/, '');
      return base.endsWith('/api/v1') ? base : `${base}/api/v1`;
    }
  }

  // 3. Explicit production backend URL constant
  if (PRODUCTION_BACKEND_URL && PRODUCTION_BACKEND_URL.trim()) {
    const base = PRODUCTION_BACKEND_URL.trim().replace(/\/+$/, '');
    return base.endsWith('/api/v1') ? base : `${base}/api/v1`;
  }

  // 4. Default to local development server
  return LOCAL_BACKEND_URL;
}

const API_CONFIG = {
  USE_REAL_BACKEND: true,
  get BASE_URL() {
    return resolveApiBaseUrl();
  },
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
    this.getToken = this.getToken.bind(this);
    this.uploadProfilePhoto = this.uploadProfilePhoto.bind(this);
    this.removeProfilePhoto = this.removeProfilePhoto.bind(this);
    this.getHeaders = this.getHeaders.bind(this);
  }

  isLiveSession() {
    const token = localStorage.getItem(SESSION_TOKEN_KEY);
    return Boolean(token && !String(token).startsWith('demo_token_'));
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
    localStorage.removeItem('proofvoice_unread_count');
    localStorage.removeItem('proofvoice_active_complaint_id');
    localStorage.removeItem(PREFER_DEMO_KEY);
    try {
      sessionStorage.clear();
    } catch (e) {}
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
      const backendOrigin = String(this.config.BASE_URL).replace(/\/api\/v1\/?$/, '');
      profileImage = `${backendOrigin}${profileImage}`;
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
      notifyInApp: profile.notify_in_app !== undefined ? Boolean(profile.notify_in_app) : true,
      notifyEmail: profile.notify_email !== undefined ? Boolean(profile.notify_email) : true,
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
    if (!email || !String(email).trim() || !password) {
      throw new Error('Please enter your email and password.');
    }
    const cleanEmail = String(email).trim().toLowerCase();
    try {
      const res = await fetch(`${this.config.BASE_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ email: cleanEmail, password, role: roleHint || '' })
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
        (err.message && /failed to fetch|networkerror|load failed|fetch failed|refused|abort|connection refused/i.test(err.message))
      );
      if (isNetworkErr) {
        // Fallback for static hosting when backend server is offline or unreachable
        const db = window.proofVoiceDb;
        if (db) {
          const dbData = db.getDb();
          const target = (dbData.users || []).find(
            u => String(u.email || '').trim().toLowerCase() === cleanEmail
          );
          if (target) {
            const isMatch = target.passwordHash
              ? (target.passwordHash === password || target.passwordHash === btoa(password))
              : Boolean(password && String(password).trim().length >= 4);
            if (!isMatch) {
              throw new Error('Invalid email or password.');
            }
            if (!target.passwordHash) {
              target.passwordHash = btoa(password);
              db.saveDb(dbData);
            }
            if (roleHint && roleHint.toLowerCase() === 'admin' && target.role !== 'admin' && target.role !== 'superadmin') {
              throw new Error('Access denied. This account does not have administrator privileges.');
            }
            if (roleHint && roleHint.toLowerCase() === 'student' && target.role !== 'student') {
              throw new Error('Access denied. Please sign in via the Administrator portal.');
            }
            const token = 'pv_auth_' + Date.now();
            const inst = (typeof db.getInstitution === 'function')
              ? db.getInstitution(target.institutionId)
              : (dbData.institutions || []).find(i => String(i.id) === String(target.institutionId));
            const user = {
              id: target.id,
              email: target.email,
              fullName: target.fullName,
              role: target.role || 'student',
              backendRole: (target.role || 'student').toUpperCase(),
              institutionId: inst ? inst.id : null,
              institutionName: inst ? inst.name : (target.institutionName || ''),
              institutionCode: inst ? inst.code : (target.institutionCode || 'INST'),
              studentIdentifier: target.studentIdentifier || target.studentId || '',
              department: target.department || '',
              course: target.course || target.department || '',
              yearSemester: target.yearSemester || target.semester || '',
              residentialAddress: target.residentialAddress || target.address || '',
              phone: target.phone || '',
              avatar: target.avatar || initialsFromName(target.fullName),
              profileComplete: true,
              isApproved: true
            };
            this.persistSession(token, user, inst);
            return {
              token,
              user,
              role: user.role,
              institution: inst,
              is_approved: true,
              message: 'Login successful.',
              success: true
            };
          } else {
            throw new Error('Invalid email or password.');
          }
        }
        throw new Error('Invalid email or password.');
      }
      throw err;
    }
  }

  demoLogin() {
    throw new Error('Demonstration login is disabled. Real authentication is required.');
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
    const password = payload.password;
    if (!password) {
      throw new Error('Password is required.');
    }
    const isOther = payload.institutionId === 'OTHER' || !payload.institutionId || Boolean(payload.customInstitutionName);
    const backendPayload = {
      email: payload.email,
      password,
      full_name: payload.fullName,
      institution_id: isOther ? 'OTHER' : (parseInt(payload.institutionId, 10) || payload.institutionId),
      custom_institution_name: payload.customInstitutionName || payload.custom_institution_name || '',
      institution_type: payload.institutionType || payload.institution_type || '',
      state: payload.state || '',
      city: payload.city || '',
      country: payload.country || 'India',
      official_domain: payload.officialDomain || payload.official_domain || '',
      student_id: payload.studentIdentifier || '',
      department: payload.department || '',
      course: payload.course || payload.department || '',
      semester: payload.yearSemester || '',
      phone: payload.phone || '',
      address: payload.residentialAddress || ''
    };

    try {
      const res = await fetch(`${this.config.BASE_URL}/auth/register/student/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(backendPayload)
      });
      const data = await this.handleResponse(res);
      const user = this.normalizeUser(data);
      if (data.token && !data.requires_approval) {
        this.persistSession(data.token, user, data.institution);
      }
      return { ...data, user, success: true };
    } catch (err) {
      const isNetworkErr = !err.status && (
        !err.data ||
        (err.message && /failed to fetch|networkerror|load failed|fetch failed|refused|abort|connection refused/i.test(err.message))
      );
      if (isNetworkErr) {
        // Fallback for static hosting when backend server is offline or unreachable
        const db = window.proofVoiceDb;
        if (db) {
          const dbData = db.getDb();
          const cleanEmail = String(payload.email).trim().toLowerCase();
          const exists = (dbData.users || []).some(
            u => String(u.email || '').trim().toLowerCase() === cleanEmail
          );
          if (exists) {
            throw new Error('An account with this email already exists.');
          }

          let inst = null;
          if (isOther && backendPayload.custom_institution_name) {
            const instName = backendPayload.custom_institution_name.trim();
            inst = (dbData.institutions || []).find(
              i => String(i.name || '').trim().toLowerCase() === instName.toLowerCase()
            );
            if (!inst) {
              if (typeof db.addInstitution === 'function') {
                inst = db.addInstitution({
                  name: instName,
                  type: backendPayload.institution_type || 'College',
                  officialEmail: backendPayload.official_domain || cleanEmail,
                  city: backendPayload.city,
                  state: backendPayload.state,
                  country: backendPayload.country || 'India',
                  officialAddress: `${backendPayload.city || ''}, ${backendPayload.state || ''}`.trim(', ') || instName,
                  status: 'UNVERIFIED',
                  verificationStatus: 'UNVERIFIED'
                });
              } else {
                const code = instName.split(/\s+/).map(w => w[0]).join('').slice(0, 5).toUpperCase() || 'INST';
                inst = {
                  id: 'inst_' + Date.now(),
                  code,
                  name: instName,
                  type: backendPayload.institution_type || 'College',
                  officialEmail: backendPayload.official_domain || cleanEmail,
                  city: backendPayload.city || '',
                  state: backendPayload.state || '',
                  country: backendPayload.country || 'India',
                  officialAddress: `${backendPayload.city || ''}, ${backendPayload.state || ''}`.trim(', ') || instName,
                  status: 'UNVERIFIED',
                  verificationStatus: 'UNVERIFIED'
                };
                if (!dbData.institutions) dbData.institutions = [];
                dbData.institutions.push(inst);
              }
            }
          } else if (payload.institutionId && payload.institutionId !== 'OTHER') {
            inst = (typeof db.getInstitution === 'function')
              ? db.getInstitution(payload.institutionId)
              : (dbData.institutions || []).find(i => String(i.id) === String(payload.institutionId));
          }

          const newStudentUser = {
            id: 'usr_' + Date.now(),
            role: 'student',
            fullName: payload.fullName,
            email: cleanEmail,
            passwordHash: btoa(password),
            institutionId: inst ? inst.id : 'inst_apex_01',
            institutionName: inst ? inst.name : (backendPayload.custom_institution_name || 'My Institution'),
            institutionCode: inst ? inst.code : 'INST',
            studentIdentifier: payload.studentIdentifier || '',
            department: payload.department || '',
            course: payload.course || payload.department || '',
            yearSemester: payload.yearSemester || '',
            residentialAddress: payload.residentialAddress || '',
            phone: payload.phone || '',
            avatar: initialsFromName(payload.fullName),
            isApproved: true,
            profileComplete: Boolean(payload.residentialAddress && payload.studentIdentifier),
            registeredAt: new Date().toISOString()
          };

          dbData.users.push(newStudentUser);
          db.saveDb(dbData);

          const token = 'pv_auth_' + Date.now();
          const normalized = {
            id: newStudentUser.id,
            email: newStudentUser.email,
            fullName: newStudentUser.fullName,
            role: 'student',
            backendRole: 'STUDENT',
            institutionId: inst ? inst.id : null,
            institutionName: inst ? inst.name : '',
            institutionCode: inst ? inst.code : '',
            studentIdentifier: newStudentUser.studentIdentifier,
            department: newStudentUser.department,
            course: newStudentUser.course,
            yearSemester: newStudentUser.yearSemester,
            residentialAddress: newStudentUser.residentialAddress,
            phone: newStudentUser.phone,
            avatar: newStudentUser.avatar,
            profileComplete: newStudentUser.profileComplete,
            isApproved: true
          };

          this.persistSession(token, normalized, inst);

          return {
            token,
            user: normalized,
            institution: inst,
            is_unlisted_institution: isOther,
            message: isOther
              ? 'Registration successful! Your institution has been added to ProofVoice. Welcome to your Student Dashboard.'
              : 'Registration successful! Welcome to your Student Dashboard.',
            success: true
          };
        }
        throw new Error('Server temporarily unavailable. Please try again later.');
      }
      throw err;
    }
  }

  async registerAdmin(payload) {
    try {
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
      return { ...data, user, success: true };
    } catch (err) {
      const isNetworkErr = !err.status && (
        !err.data ||
        (err.message && /failed to fetch|networkerror|load failed|fetch failed|refused|abort|connection refused/i.test(err.message))
      );
      if (isNetworkErr) {
        throw new Error('Server temporarily unavailable. Please try again later.');
      }
      throw err;
    }
  }

  async getCurrentUser() {
    if (this.isLiveSession()) {
      try {
        const res = await fetch(`${this.config.BASE_URL}/auth/me/`, {
          headers: this.getHeaders()
        });
        const data = await this.handleResponse(res);
        const user = this.normalizeUser(data);
        this.persistSession(localStorage.getItem(SESSION_TOKEN_KEY), user, null);
        return user;
      } catch (err) {
        return this.getStoredUser();
      }
    }
    return null;
  }

  async updateUserProfile(userId, profileData) {
    if (this.isLiveSession()) {
      try {
        const payload = {
          full_name: profileData.fullName || profileData.full_name,
          student_id: profileData.studentIdentifier || profileData.student_id,
          department: profileData.department,
          course: profileData.course || profileData.department,
          semester: profileData.yearSemester || profileData.semester,
          phone: profileData.phone,
          address: profileData.residentialAddress || profileData.address,
          designation: profileData.designation
        };
        if (profileData.institutionId || profileData.institution_id) {
          payload.institution_id = profileData.institutionId || profileData.institution_id;
        }
        if (profileData.notifyInApp !== undefined) {
          payload.notify_in_app = Boolean(profileData.notifyInApp);
        } else if (profileData.notify_in_app !== undefined) {
          payload.notify_in_app = Boolean(profileData.notify_in_app);
        }
        if (profileData.notifyEmail !== undefined) {
          payload.notify_email = Boolean(profileData.notifyEmail);
        } else if (profileData.notify_email !== undefined) {
          payload.notify_email = Boolean(profileData.notify_email);
        }

        const res = await fetch(`${this.config.BASE_URL}/auth/profile/`, {
          method: 'PATCH',
          headers: this.getHeaders(),
          body: JSON.stringify(payload)
        });
        const data = await this.handleResponse(res);
        const stored = this.getStoredUser() || {};
        let merged = stored;
        if (data && data.user) {
          const normalized = this.normalizeUser(data.user);
          merged = { ...stored, ...normalized };
          if (!merged.profileImage && stored.profileImage) {
            merged.profileImage = stored.profileImage;
          }
          localStorage.setItem(SESSION_USER_KEY, JSON.stringify(merged));
          localStorage.setItem('proofvoice_auth_user', JSON.stringify(merged));
        }
        if (window.proofVoiceDb) {
          try {
            window.proofVoiceDb.updateUserProfile(userId || (stored && stored.id), profileData);
          } catch (e) {}
        }
        return { success: true, user: merged, ...data };
      } catch (err) {
        const isNetworkErr = !err.status && (
          !err.data ||
          (err.message && /failed to fetch|networkerror|load failed|fetch failed|refused|abort|connection refused/i.test(err.message))
        );
        if (!isNetworkErr) {
          // Genuine backend error: throw so caller shows real validation error to user
          throw err;
        }
        console.warn('[ProofVoice API] Live backend offline, saving locally:', err);
      }
    }
    // Static hosting offline fallback
    if (window.proofVoiceDb) {
      window.proofVoiceDb.updateUserProfile(userId, profileData);
      const stored = this.getStoredUser() || {};
      const merged = { ...stored, ...profileData };
      localStorage.setItem(SESSION_USER_KEY, JSON.stringify(merged));
      localStorage.setItem('proofvoice_auth_user', JSON.stringify(merged));
      return { success: true, user: merged };
    }
    throw new Error('Unable to update profile. Server is unreachable.');
  }

  async uploadProfilePhoto(file) {
    if (this.isLiveSession()) {
      try {
        const formData = new FormData();
        formData.append('photo', file);
        const token = (this && typeof this.getToken === 'function') 
          ? this.getToken() 
          : localStorage.getItem(SESSION_TOKEN_KEY);
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
        if (data.profile_image_url && typeof data.profile_image_url === 'string' && data.profile_image_url.startsWith('/')) {
          const backendOrigin = String(this.config.BASE_URL).replace(/\/api\/v1\/?$/, '');
          data.profile_image_url = `${backendOrigin}${data.profile_image_url}`;
        }
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
      try {
        const res = await fetch(`${this.config.BASE_URL}/institutions/`, {
          headers: { 'Accept': 'application/json' }
        });
        const data = await this.handleResponse(res);
        return this.unwrapList(data);
      } catch (err) {
        if (window.proofVoiceDb) {
          return typeof window.proofVoiceDb.getInstitutions === 'function'
            ? window.proofVoiceDb.getInstitutions()
            : (window.proofVoiceDb.getAllInstitutions ? window.proofVoiceDb.getAllInstitutions() : (window.proofVoiceDb.getDb().institutions || []));
        }
        return [];
      }
    }
    if (window.proofVoiceDb) {
      return typeof window.proofVoiceDb.getInstitutions === 'function'
        ? window.proofVoiceDb.getInstitutions()
        : (window.proofVoiceDb.getAllInstitutions ? window.proofVoiceDb.getAllInstitutions() : (window.proofVoiceDb.getDb().institutions || []));
    }
    return [];
  }

  async requestInstitution(payload) {
    if (this.config.USE_REAL_BACKEND) {
      try {
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
        return await this.handleResponse(res);
      } catch (e) {
        console.warn('[ProofVoice API] Live requestInstitution failed, saving locally:', e);
      }
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
      try {
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
      } catch (err) {
        console.warn('[ProofVoice API] Live submitComplaint failed, saving to local store:', err);
      }
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

  async chatWithAi(message, history = [], voiceMode = false) {
    if (this.config.USE_REAL_BACKEND) {
      try {
        const token = localStorage.getItem(SESSION_TOKEN_KEY);
        const headers = { 'Content-Type': 'application/json' };
        if (token && !String(token).startsWith('demo_token_')) {
          headers.Authorization = `Token ${token}`;
        }
        const res = await fetch(`${this.config.BASE_URL}/ai/chat/`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ message, history, voice_mode: voiceMode })
        });
        if (res.ok) {
          const data = await res.json();
          return data;
        }
      } catch (err) {
        console.warn('[ProofVoice API] Live AI chat error, falling back to local engine:', err);
      }
    }
    return this._localAiChatFallback(message, history, voiceMode);
  }

  _localAiChatFallback(message, history = [], voiceMode = false) {
    const query = (message || '').trim();
    const queryLower = query.toLowerCase();
    const user = this.getCurrentUser();

    if (!query) {
      return {
        success: true,
        reply: "Hello! I am your ProofVoice Campus AI Assistant. How can I assist you with reporting issues, tracking complaints, or navigating your dashboard today?",
        speak_text: "Hello! I am your ProofVoice Campus AI Assistant. How can I assist you today?",
        topic: 'greeting',
        suggested_actions: [
          "How do I record a voice complaint?",
          "Check my complaint status",
          "How does application review work?",
          "How do I update my profile?"
        ]
      };
    }

    // Greetings
    if (/^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))\b/i.test(queryLower) && query.split(' ').length <= 4) {
      const studentName = user ? (user.fullName || user.full_name || 'Student') : 'Student';
      return {
        success: true,
        reply: `Hello ${studentName}! Welcome to ProofVoice Support. I can help you submit grievances, track your tickets, understand complaint statuses, or update your academic profile. What would you like to know?`,
        speak_text: `Hello ${studentName}! Welcome to ProofVoice Support. What would you like to know?`,
        topic: 'greeting',
        suggested_actions: [
          "What are my active complaints?",
          "How do I record a voice complaint?",
          "What does 'Under Review' mean?",
          "How do notifications work?"
        ]
      };
    }

    // Complaints query
    const isAccountQuery = /my complaint|my complaints|my ticket|my status|status of my|active complaint|track complaint|track my|recent complaint/i.test(queryLower);
    const idMatch = query.match(/\b(PV-[\w\-]+|\b\d{4,6}\b)/i);

    if (isAccountQuery || idMatch) {
      const complaints = (window.proofVoiceDb && typeof window.proofVoiceDb.getComplaints === 'function') 
        ? window.proofVoiceDb.getComplaints() 
        : [];
      const userComplaints = user 
        ? (complaints || []).filter(c => String(c.studentId || c.student_id || c.studentEmail || c.student_email || '') === String(user.id || user.email))
        : (complaints || []);

      if (idMatch) {
        const targetId = idMatch[1].trim().toUpperCase();
        const found = (complaints || []).find(c => (c.id && String(c.id).toUpperCase() === targetId) || (c.complaintId && String(c.complaintId).toUpperCase() === targetId));
        if (found) {
          if (user && user.role === 'student' && found.studentId && found.studentId !== user.id && found.studentEmail !== user.email) {
            return {
              success: true,
              reply: "For student privacy and security, you can only view complaints submitted by your own account.",
              speak_text: "For student privacy and security, you can only view complaints submitted by your own account.",
              topic: 'complaint_privacy_forbidden'
            };
          }
          const reply = `**Complaint Details for \`${found.complaintId || found.id}\`:**\n\n• **Title:** ${found.title}\n• **Status:** **${found.status}**\n• **Category:** ${found.category || 'General'}\n• **Assigned Department:** ${found.assignedDepartment || 'Not assigned yet'}\n• **Location:** ${found.location || found.issueLocation || 'Campus'}\n• **Submitted On:** ${found.submittedAt || found.createdAt || 'Recently'}\n\nYou can view the full timeline on the [Complaint Details page](complaint-details.html?id=${found.complaintId || found.id}).`;
          return {
            success: true,
            reply,
            speak_text: `Complaint ${found.complaintId || found.id} has title: ${found.title}. Current status is: ${found.status}.`,
            topic: 'complaint_single_status',
            complaint_id: found.complaintId || found.id,
            suggested_actions: [`View ${found.complaintId || found.id} Details`, "Check all my complaints", "Report an Issue"]
          };
        } else {
          return {
            success: true,
            reply: `I could not find any complaint matching identifier \`${targetId}\` in your account records. Please check your tracking ID on the **My Complaints** page.`,
            speak_text: `I could not find any complaint matching identifier ${targetId} in your account records.`,
            topic: 'complaint_not_found',
            suggested_actions: ["View My Complaints", "Report an Issue"]
          };
        }
      }

      if (!userComplaints || userComplaints.length === 0) {
        return {
          success: true,
          reply: "You have not submitted any complaints yet. Whenever you encounter a problem with campus facilities, washrooms, classrooms, or hostel rooms, you can click **\"Report an Issue\"** to speak or type your grievance.",
          speak_text: "You have not submitted any complaints yet. Click Report an Issue to speak or type your grievance.",
          topic: 'no_complaints',
          suggested_actions: ["Report an Issue with Voice", "How does voice reporting work?"]
        };
      }

      const lines = [`You have **${userComplaints.length}** complaint${userComplaints.length !== 1 ? 's' : ''} on record:`];
      userComplaints.slice(0, 5).forEach(c => {
        lines.push(`• **${c.complaintId || c.id}** — *${c.title}* [${c.status}]`);
      });
      lines.push(`\nYou can ask me for details about any of these tickets or click **My Complaints** in the sidebar.`);
      return {
        success: true,
        reply: lines.join('\n'),
        speak_text: `You have ${userComplaints.length} complaints on record. The most recent is ${userComplaints[0].title} with status ${userComplaints[0].status}.`,
        topic: 'complaints_summary',
        suggested_actions: [`Status of ${userComplaints[0].complaintId || userComplaints[0].id}`, "View My Complaints", "Report an Issue"]
      };
    }

    // Match topics
    if (/voice|record|mic|speech to text|stt|audio|speak|transcription/i.test(queryLower)) {
      return {
        success: true,
        reply: "**Reporting Issues via Voice:**\n\n1. Click **\"Report an Issue\"** or **\"Create Complaint\"**.\n2. Select the **Voice Input** tab and select your language.\n3. Tap the **Microphone** button and describe your campus concern naturally.\n4. ProofVoice transcribes your speech in real time. You can edit any misheard words and click **\"Generate Formal Application\"**.\n5. Review the formal letter before submitting.",
        speak_text: "To report an issue with voice, click Report an Issue, select Voice Input, tap the microphone, speak naturally, and review your generated application before submitting.",
        topic: 'voice_reporting',
        suggested_actions: ["Can I edit my transcription?", "How do I review before submitting?", "Report an Issue Now"]
      };
    }

    if (/register|unlisted|not listed|college not in list|affiliation|enroll/i.test(queryLower)) {
      return {
        success: true,
        reply: "**Student Registration & Unlisted Institutions:**\n\n1. Visit the **Student Registration** page (`/register.html`).\n2. If your college is not listed, select **\"+ My Institution Is Not Listed\"**.\n3. Enter your institution name, institution type, city, state, country, and official domain.\n4. Complete your academic details. ProofVoice will immediately register your student account and grant access to your dashboard.\n5. Unlisted institutions are placed in administrative verification separately without blocking you.",
        speak_text: "You can register even if your college is not listed. Select My Institution Is Not Listed, fill in your details, and you will get immediate access to your dashboard.",
        topic: 'registration',
        suggested_actions: ["Open Registration Page", "Sign In to Dashboard", "How do I report an issue?"]
      };
    }

    if (/review|letter|formal application|mandatory|checkbox|draft/i.test(queryLower)) {
      return {
        success: true,
        reply: "**Formal Application & Mandatory Review:**\n\nProofVoice never submits a grievance without your explicit review and confirmation:\n\n1. Our AI structures your words into a formal institutional grievance letter addressed to the appropriate authority.\n2. The letter automatically incorporates your saved residential address and department.\n3. You can click **\"Read Aloud\"** to listen to the generated draft.\n4. Check the declaration box and click **\"Submit Authoritative Complaint\"**.",
        speak_text: "ProofVoice never submits a grievance without your explicit review. Our AI structures your words into a formal letter that you confirm before submission.",
        topic: 'review_letter',
        suggested_actions: ["Why is review mandatory?", "What do statuses mean?", "How do I listen aloud?"]
      };
    }

    if (/status|statuses|under review|in progress|assigned|awaiting|resolved|reopened/i.test(queryLower)) {
      return {
        success: true,
        reply: "**ProofVoice Complaint Statuses:**\n\n• **Submitted:** Grievance recorded and tracking ID assigned.\n• **Under Review:** Administrators have opened your application.\n• **Assigned:** Ticket routed to a specific department or technician.\n• **In Progress:** Work is actively underway.\n• **Awaiting Student:** Admin has requested clarifying information or confirmation.\n• **Resolved:** Repairs completed and verified with closing remark.\n• **Reopened:** Issue recurred or was incomplete.",
        speak_text: "The main statuses are Submitted, Under Review, Assigned, In Progress, Awaiting Student, Resolved, and Reopened.",
        topic: 'statuses',
        suggested_actions: ["What are my active complaints?", "What does 'Under Review' mean?", "Can I reopen a complaint?"]
      };
    }

    if (/profile|save profile|photo|picture|avatar|upload photo|address|student id/i.test(queryLower)) {
      return {
        success: true,
        reply: "**Managing Your Profile & Settings:**\n\n1. Open **Profile & Settings** (`student-profile.html`) from the sidebar or click your avatar.\n2. Update your Legal Name, Student ID, Department, Year/Semester, and Residential Address.\n3. Click **Upload Photo** to update your picture.\n4. Click **\"Save Profile Changes\"** to save to the database.\nYour saved address automatically populates future formal grievance letters.",
        speak_text: "You can update your name, student ID, department, address, and profile photo under Profile and Settings. Click Save Profile Changes to save.",
        topic: 'profile',
        suggested_actions: ["Edit My Profile", "What are my complaints?", "How do I report an issue?"]
      };
    }

    if (/notification|notifications|alert|alerts|bell|unread/i.test(queryLower)) {
      return {
        success: true,
        reply: "**Personalized Notifications:**\n\n• ProofVoice sends real notifications when events occur on your complaints (submission, assignment, admin remark, info request, resolution).\n• Click the **Notification Bell** on the top bar to view recent alerts or mark all as read.\n• You can customize your In-App and Email preferences under Profile & Settings.",
        speak_text: "You receive personalized notifications for submission, status changes, admin remarks, and resolution on your tickets. Check the bell icon on the top bar.",
        topic: 'notifications',
        suggested_actions: ["How do I mark alerts as read?", "Configure notification preferences", "Open Notification Center"]
      };
    }

    return {
      success: true,
      reply: "I don't have specific details on that topic in the ProofVoice support knowledge base. ProofVoice is designed specifically for reporting campus grievances, preparing formal applications, and tracking institutional resolution.\n\nFor institutional academic grading, fee refunds, or policy questions, please contact your university's Dean of Student Welfare or Campus Grievance Redressal Committee directly.",
      speak_text: "I don't have that specific information. For institutional policy questions, please contact your Dean of Student Welfare.",
      topic: 'unrecognized',
      suggested_actions: [
        "How do I record a complaint?",
        "What do complaint statuses mean?",
        "How do I update my profile?",
        "What are my active complaints?"
      ]
    };
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
if (!window.proofVoiceApi.getToken) {
  window.proofVoiceApi.getToken = function() {
    return localStorage.getItem('proofvoice_auth_token');
  };
}
window.formatApiErrorPayload = formatApiErrorPayload;
window.mapBackendRole = mapBackendRole;
window.titleCaseStatus = titleCaseStatus;
