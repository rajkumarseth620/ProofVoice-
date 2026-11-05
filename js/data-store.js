/**
 * ProofVoice - Mock Data Store & State Management (v3)
 * Provides realistic multi-tenant data persistent in localStorage.
 * Compatible with future Django REST & MySQL backends.
 */

const STORAGE_KEY = 'proofvoice_demo_db_v3';

// Seed Initial Multi-Tenant Demo Data
const INITIAL_DEMO_DATA = {
  currentSession: {
    userId: 'usr_student_01',
    role: 'student', // 'student' | 'admin' | 'superadmin'
    institutionId: 'inst_apex_01'
  },
  institutions: [
    {
      id: 'inst_apex_01',
      code: 'AIT',
      name: 'Apex Institute of Technology',
      type: 'Autonomous University',
      officialEmail: 'dean.studentaffairs@apextech.edu',
      country: 'India',
      state: 'Jharkhand',
      city: 'Jamshedpur',
      officialAddress: 'Apex Knowledge Park, Main Ring Road, Jamshedpur, Jharkhand 831014',
      website: 'https://apextech.edu',
      status: 'active',
      contactPerson: 'Dr. Vikram Roy',
      contactDesignation: 'Dean of Student Affairs',
      defaultRecipient: {
        designation: 'The Dean',
        name: 'Dr. Vikram Roy',
        address: 'Office of the Dean, Student Welfare, Apex Tech Campus, Jamshedpur 831014'
      },
      recipientMappings: {
        'Classroom and Laboratory': { designation: 'The In-Charge, Academic Laboratories & IT Facilities', department: 'Information Technology Services' },
        'Electricity and Lighting': { designation: 'The Executive Engineer, Electrical Infrastructure', department: 'Electrical & Energy Management' },
        'Water and Sanitation': { designation: 'The Estate Officer / Sanitation Supervisor', department: 'Water Works & Sanitation' },
        'Internet and IT': { designation: 'The Chief Information Officer / Network Administrator', department: 'Information Technology Services' },
        'Hostel and Accommodation': { designation: 'The Chief Warden, Hostel Administration', department: 'Hostel & Residential Life' },
        'Library': { designation: 'The University Librarian', department: 'Library & Information Services' },
        'Transport': { designation: 'The Transport Coordinator', department: 'Transport & Shuttle Operations' },
        'Infrastructure and Maintenance': { designation: 'The Estate Officer / Campus Maintenance Cell', department: 'Infrastructure & Maintenance' },
        'Safety and Security': { designation: 'The Chief Proctor / Campus Security Officer', department: 'Campus Security Services' },
        'Administrative Services': { designation: 'The Registrar', department: 'General Administration' },
        'Other': { designation: 'The Dean of Student Affairs', department: 'Academic Grievance Redressal' }
      },
      departments: [
        'Infrastructure & Maintenance',
        'Information Technology Services',
        'Hostel & Residential Life',
        'Electrical & Energy Management',
        'Water Works & Sanitation',
        'Academic Grievance Redressal',
        'Library & Information Services',
        'Transport & Shuttle Operations'
      ],
      categories: [
        'Infrastructure and Maintenance',
        'Electricity and Lighting',
        'Water and Sanitation',
        'Internet and IT',
        'Classroom and Laboratory',
        'Library',
        'Hostel and Accommodation',
        'Transport',
        'Administrative Services',
        'Safety and Security',
        'Other'
      ],
      settings: {
        slaHours: 48,
        requireStudentVerification: true,
        notifyOnResolution: true
      }
    },
    {
      id: 'inst_horizon_02',
      code: 'HSU',
      name: 'Horizon State University',
      type: 'Public University',
      officialEmail: 'registrar@horizonstate.edu',
      country: 'India',
      state: 'Karnataka',
      city: 'Bengaluru',
      officialAddress: 'Horizon University Campus, Outer Ring Road, Bengaluru, Karnataka 560012',
      website: 'https://horizonstate.edu',
      status: 'active',
      contactPerson: 'Prof. Ananya Sen',
      contactDesignation: 'Registrar',
      defaultRecipient: {
        designation: 'The Registrar',
        name: 'Prof. Ananya Sen',
        address: 'Administrative Block, Horizon State University, Bengaluru 560012'
      },
      recipientMappings: {
        'Classroom and Laboratory': { designation: 'The Dean of Academic Facilities', department: 'Campus IT' },
        'Hostel and Accommodation': { designation: 'The Chief Hostel Warden', department: 'Student Welfare Cell' },
        'Infrastructure and Maintenance': { designation: 'The Estate Officer', department: 'Estate Office' },
        'Other': { designation: 'The Registrar', department: 'General Administration' }
      },
      departments: ['Estate Office', 'Campus IT', 'Student Welfare Cell', 'General Administration'],
      categories: ['Campus Maintenance', 'IT Support', 'Hostel Facilities', 'Academics', 'Classroom and Laboratory', 'Other'],
      settings: {
        slaHours: 72,
        requireStudentVerification: true,
        notifyOnResolution: true
      }
    },
    {
      id: 'inst_greenfield_03',
      code: 'GPC',
      name: 'Greenfield Polytechnic College',
      type: 'Polytechnic College',
      officialEmail: 'principal@greenfieldpoly.edu',
      country: 'India',
      state: 'Maharashtra',
      city: 'Pune',
      officialAddress: 'Plot 18, Industrial Estate Road, Pune, Maharashtra 411038',
      website: 'https://greenfieldpoly.edu',
      status: 'pending_approval',
      contactPerson: 'Ramesh Kulkarni',
      contactDesignation: 'Head of Administration',
      defaultRecipient: {
        designation: 'The Principal',
        name: 'Ramesh Kulkarni',
        address: 'Principal Office, Greenfield Polytechnic, Pune'
      },
      recipientMappings: {},
      departments: ['Workshop & Labs', 'General Administration'],
      categories: ['Equipment & Machines', 'Cleanliness & Water', 'Other'],
      settings: {
        slaHours: 48,
        requireStudentVerification: false,
        notifyOnResolution: true
      }
    }
  ],
  users: [
    {
      id: 'usr_superadmin_01',
      role: 'superadmin',
      fullName: 'ProofVoice Platform Super Administrator',
      email: 'superadmin@proofvoice.platform',
      passwordHash: btoa('Admin@ProofVoice2026'),
      institutionId: null,
      department: 'Platform Governance & Security',
      phone: '+91 99999 88888',
      avatar: 'SA',
      status: 'active',
      registeredAt: '2024-01-01'
    },
    {
      id: 'usr_admin_rajkr',
      role: 'admin',
      fullName: 'Raj Kumar',
      email: 'rajkr@apex.edu',
      passwordHash: btoa('6203415403raju'),
      institutionId: 'inst_arka_01',
      designation: 'Dean of Student Welfare',
      department: 'Academic Affairs',
      phone: '+91 62034 15403',
      avatar: 'RK',
      status: 'verified',
      is_verified: true,
      isVerified: true,
      profileComplete: true,
      registeredAt: '2024-01-10'
    },
    {
      id: 'usr_student_laxmi',
      role: 'student',
      fullName: 'Laxmi Seth',
      email: 'laxmi.seth@apex.edu',
      passwordHash: btoa('6203415403raju'),
      institutionId: 'inst_apex_01',
      studentIdentifier: 'APEX-CS-2024-001',
      department: 'Computer Science & Engineering',
      yearSemester: '3rd Year, 5th Semester',
      residentialAddress: 'Jamshedpur',
      phone: '+91 62034 15403',
      avatar: 'LS',
      status: 'verified',
      is_verified: true,
      isVerified: true,
      profileComplete: true,
      registeredAt: '2026-10-27'
    },
    {
      id: 'usr_student_01',
      role: 'student',
      fullName: 'Maya Sharma',
      email: 'maya.sharma@apextech.edu',
      institutionId: 'inst_apex_01',
      studentIdentifier: 'AIT-2023-CS-042',
      department: 'Computer Science & Engineering',
      yearSemester: '3rd Year, 5th Semester',
      residentialAddress: 'Room 312, Sarojini Hall of Residence, Apex Tech Campus, Jamshedpur 831014',
      phone: '+91 98765 43210',
      avatar: 'MS',
      status: 'verified',
      is_verified: true,
      isVerified: true,
      profileComplete: true,
      registeredAt: '2025-08-15'
    },
    {
      id: 'usr_student_02',
      role: 'student',
      fullName: 'Rohan Kulkarni',
      email: 'rohan.kulkarni@horizonstate.edu',
      institutionId: 'inst_horizon_02',
      studentIdentifier: 'HSU-2024-ME-019',
      department: 'Mechanical Engineering',
      yearSemester: '2nd Year, 3rd Semester',
      residentialAddress: 'Flat 4B, Kaveri Hostel Block, Horizon State University, Bengaluru 560012',
      phone: '+91 98450 11223',
      avatar: 'RK',
      status: 'verified',
      is_verified: true,
      isVerified: true,
      profileComplete: true,
      registeredAt: '2025-09-01'
    },
    {
      id: 'usr_student_new',
      role: 'student',
      fullName: 'Aditya Verma',
      email: 'aditya.verma@apextech.edu',
      institutionId: 'inst_apex_01',
      studentIdentifier: 'AIT-2026-UG-089',
      department: 'General Campus',
      course: 'Undergraduate',
      yearSemester: '1st Year, Semester 1',
      residentialAddress: '',
      phone: '+91 91234 56789',
      avatar: 'AV',
      status: 'verified',
      is_verified: true,
      isVerified: true,
      profileComplete: true,
      registeredAt: '2026-10-27'
    },
    {
      id: 'usr_admin_01',
      role: 'admin',
      fullName: 'Dr. Vikram Roy',
      email: 'v.roy@apextech.edu',
      institutionId: 'inst_apex_01',
      designation: 'Dean of Student Affairs',
      department: 'Academic Grievance Redressal',
      phone: '+91 98321 00001',
      avatar: 'VR',
      status: 'verified',
      is_verified: true,
      isVerified: true,
      profileComplete: true,
      registeredAt: '2024-01-10'
    },
    {
      id: 'usr_admin_02',
      role: 'admin',
      fullName: 'Prof. Ananya Sen',
      email: 'registrar@horizonstate.edu',
      institutionId: 'inst_horizon_02',
      designation: 'Registrar',
      department: 'General Administration',
      phone: '+91 98450 99999',
      avatar: 'AS',
      status: 'verified',
      is_verified: true,
      isVerified: true,
      profileComplete: true,
      registeredAt: '2024-03-15'
    },
    {
      id: 'usr_superadmin_02',
      role: 'superadmin',
      fullName: 'Chief Systems Administrator',
      email: 'platform.admin@proofvoice.io',
      passwordHash: btoa('Admin@ProofVoice2026'),
      institutionId: null,
      designation: 'Platform Super-Admin',
      phone: '+91 80000 00000',
      avatar: 'PA',
      status: 'active',
      registeredAt: '2023-01-01'
    }
  ],
  adminRequests: [
    {
      id: 'req_adm_01',
      fullName: 'Dr. Rajesh Mishra',
      officialEmail: 'r.mishra@apextech.edu',
      institutionId: 'inst_apex_01',
      institutionName: 'Apex Institute of Technology',
      designation: 'Head of Physics Department',
      department: 'Classroom and Laboratory',
      phone: '+91 98350 22334',
      reason: 'Need administrative access to oversee department-level laboratory equipment repairs and complaints.',
      verificationCode: 'AIT-FACULTY-2026',
      status: 'pending',
      requestedAt: '2026-10-25T11:20:00Z'
    }
  ],
  complaints: [
    {
      id: 'PV-AIT-2026-001',
      institutionId: 'inst_apex_01',
      studentId: 'usr_student_01',
      studentName: 'Maya Sharma',
      studentIdentifier: 'AIT-2023-CS-042',
      title: 'Ceiling projector malfunctioning in Computer Lab 304',
      originalInputMethod: 'voice',
      originalTranscription: 'The ceiling projector in Computer Lab 304 in the Academic Block B has been flickering and shutting down automatically every 10 minutes during our Machine Learning practical sessions. It has been happening since Monday and disrupts the entire class.',
      category: 'Classroom and Laboratory',
      priority: 'High',
      location: 'Academic Block B, 3rd Floor, Computer Lab 304',
      formalApplication: `Maya Sharma
Student ID: AIT-2023-CS-042
Department of Computer Science & Engineering, 3rd Year, 5th Semester
Apex Institute of Technology
Room 312, Sarojini Hall of Residence, Apex Tech Campus, Jamshedpur 831014
October 22, 2026

To,
The In-Charge, Academic Laboratories & IT Facilities
Apex Institute of Technology
Apex Knowledge Park, Main Ring Road, Jamshedpur, Jharkhand 831014

Subject: Formal Grievance Regarding Ceiling Projector Malfunctioning in Computer Lab 304

Respected Sir/Madam,

I am writing this formal application to respectfully bring to your urgent attention a technical malfunction in Computer Lab 304, Academic Block B. The ceiling-mounted projector has been experiencing severe intermittent power cutoffs and display flickering, shutting down every ten minutes during academic laboratory sessions.

This technical fault severely impairs the presentation of instructional code and practical demonstrations for over 60 students in the Machine Learning curriculum.

I kindly request you to look into this matter and take the necessary action to resolve the issue.

Thank you for your time and consideration.

Yours sincerely,

Maya Sharma
Student ID: AIT-2023-CS-042
Department of Computer Science & Engineering
Apex Institute of Technology
Contact: +91 98765 43210`,
      status: 'In Progress',
      assignedDepartment: 'Information Technology Services',
      assignedTo: 'Rajesh Nair (Sr. IT Technician)',
      submittedAt: '2026-10-22T10:30:00Z',
      updatedAt: '2026-10-25T14:15:00Z',
      history: [
        {
          status: 'Submitted',
          timestamp: '2026-10-22T10:30:00Z',
          actor: 'Maya Sharma',
          remarks: 'Complaint formally submitted via ProofVoice Voice Assistant.'
        },
        {
          status: 'Under Review',
          timestamp: '2026-10-23T09:15:00Z',
          actor: 'Dr. Vikram Roy (Dean)',
          remarks: 'Application reviewed. Assigned to Information Technology Services for hardware diagnostics.'
        },
        {
          status: 'In Progress',
          timestamp: '2026-10-25T14:15:00Z',
          actor: 'Rajesh Nair (IT Services)',
          remarks: 'Technician inspected the unit. Replacement HDMI splitter and power module ordered. Expected repair on 28th Oct.'
        }
      ],
      adminNotes: [
        {
          timestamp: '2026-10-23T09:16:00Z',
          author: 'Dr. Vikram Roy',
          text: 'Internal check: Similar issue was reported in Block A last month. Vendor warranty valid until Dec 2026.'
        }
      ]
    },
    {
      id: 'PV-AIT-2026-002',
      institutionId: 'inst_apex_01',
      studentId: 'usr_student_01',
      studentName: 'Maya Sharma',
      studentIdentifier: 'AIT-2023-CS-042',
      title: 'Water dispenser cooling system not functional on 2nd Floor Library',
      originalInputMethod: 'text',
      originalTranscription: 'The RO water purifier and water cooler on the second floor reading wing of the central library has been leaking water on the floor and is not dispensing drinking water properly for the past three days.',
      category: 'Water and Sanitation',
      priority: 'Medium',
      location: 'Central Library, 2nd Floor East Wing reading area',
      formalApplication: `Maya Sharma
Student ID: AIT-2023-CS-042
Department of Computer Science & Engineering, 3rd Year, 5th Semester
Apex Institute of Technology
Room 312, Sarojini Hall of Residence, Apex Tech Campus, Jamshedpur 831014
October 18, 2026

To,
The Estate Officer / Sanitation Supervisor
Apex Institute of Technology
Apex Knowledge Park, Main Ring Road, Jamshedpur, Jharkhand 831014

Subject: Formal Complaint Regarding Malfunctioning Water Cooler in Central Library

Respected Sir/Madam,

I wish to formally report that the drinking water dispenser and filtration unit situated on the second floor (East Wing) of the Central Library is currently non-operational. Water is accumulating on the corridor floor due to a pipe leakage, presenting a slip hazard to students. Furthermore, drinking water is unavailable to reading room patrons.

I kindly request you to look into this matter and take the necessary action to resolve the issue.

Thank you for your time and consideration.

Yours sincerely,

Maya Sharma
Student ID: AIT-2023-CS-042
Department of Computer Science & Engineering
Apex Institute of Technology
Contact: +91 98765 43210`,
      status: 'Resolved',
      assignedDepartment: 'Water Works & Sanitation',
      assignedTo: 'Suresh Verma (Sanitation Supervisor)',
      submittedAt: '2026-10-18T11:00:00Z',
      updatedAt: '2026-10-20T16:45:00Z',
      resolutionSummary: 'Sanitation team replaced the faulty inlet silicone valve and cleaned the drainage line. Water cooler operational and sanitized.',
      history: [
        {
          status: 'Submitted',
          timestamp: '2026-10-18T11:00:00Z',
          actor: 'Maya Sharma',
          remarks: 'Complaint registered.'
        },
        {
          status: 'Under Review',
          timestamp: '2026-10-18T14:20:00Z',
          actor: 'Dr. Vikram Roy',
          remarks: 'Escalated to Water Works & Sanitation.'
        },
        {
          status: 'In Progress',
          timestamp: '2026-10-19T10:00:00Z',
          actor: 'Suresh Verma',
          remarks: 'Work order #SAN-402 issued for pipe replacement.'
        },
        {
          status: 'Resolved',
          timestamp: '2026-10-20T16:45:00Z',
          actor: 'Suresh Verma',
          remarks: 'Valve replaced, water temperature verified at 18°C, area dried and disinfected.'
        }
      ],
      adminNotes: []
    },
    {
      id: 'PV-HSU-2026-001',
      institutionId: 'inst_horizon_02',
      studentId: 'usr_student_02',
      studentName: 'Rohan Kulkarni',
      studentIdentifier: 'HSU-2024-ME-019',
      title: 'Mechanical Workshop Lathe Machine safety shield broken',
      originalInputMethod: 'text',
      originalTranscription: 'The acrylic safety shield on Lathe Machine #4 in the Mechanical Machine Shop has a deep structural crack and is missing the locking pin. Operating it poses a flying metal chip hazard.',
      category: 'Classroom and Laboratory',
      priority: 'Urgent',
      location: 'Department of Mechanical Engineering, Workshop Block A, Bay 3',
      formalApplication: `Rohan Kulkarni
Student ID: HSU-2024-ME-019
Department of Mechanical Engineering, 2nd Year, 3rd Semester
Horizon State University
Flat 4B, Kaveri Hostel Block, Horizon State University, Bengaluru 560012
October 24, 2026

To,
The Dean of Academic Facilities
Horizon State University
Horizon University Campus, Outer Ring Road, Bengaluru, Karnataka 560012

Subject: Formal Safety Redressal Regarding Damaged Lathe Guard in Workshop Bay 3

Respected Sir/Madam,

I am writing this formal application to respectfully report a workplace safety defect in Workshop Block A. The transparent chip guard on heavy-duty Lathe Machine #4 is severely cracked and lacks the proper retention pin, risking physical injury to students during turning operations.

I kindly request you to look into this matter and take the necessary action to resolve the issue.

Thank you for your time and consideration.

Yours sincerely,

Rohan Kulkarni
Student ID: HSU-2024-ME-019
Department of Mechanical Engineering
Horizon State University
Contact: +91 98450 11223`,
      status: 'In Progress',
      assignedDepartment: 'Estate Office',
      assignedTo: 'Anand Kumar (Lab Tech)',
      submittedAt: '2026-10-24T09:00:00Z',
      updatedAt: '2026-10-26T11:30:00Z',
      history: [
        {
          status: 'Submitted',
          timestamp: '2026-10-24T09:00:00Z',
          actor: 'Rohan Kulkarni',
          remarks: 'Safety hazard reported.'
        },
        {
          status: 'In Progress',
          timestamp: '2026-10-26T11:30:00Z',
          actor: 'Prof. Ananya Sen',
          remarks: 'Machine tagged out of service. Replacement polycarbonate visor ordered.'
        }
      ],
      adminNotes: []
    }
  ],
  notifications: [
    {
      id: 'notif_kunal_01',
      recipientId: 'usr_student_kunal',
      recipientEmail: 'kunal@arka.edu',
      institutionId: 'inst_arka_01',
      title: 'Student Status Verified',
      message: 'Your student membership has been officially verified and approved by the campus administration.',
      link: 'student-profile.html',
      type: 'account',
      read: false,
      timestamp: '2026-11-04T20:30:00Z'
    },
    {
      id: 'notif_kunal_02',
      recipientId: 'usr_student_kunal',
      recipientEmail: 'kunal@arka.edu',
      institutionId: 'inst_arka_01',
      title: 'Status Update: PV-2026-7499',
      message: "Your complaint 'Not Working Projector In Lab' status is now Resolved.",
      link: 'complaint-details.html?id=PV-2026-7499',
      complaintId: 'PV-2026-7499',
      type: 'resolution',
      read: false,
      timestamp: '2026-11-04T19:35:00Z'
    },
    {
      id: 'notif_kunal_03',
      recipientId: 'usr_student_kunal',
      recipientEmail: 'kunal@arka.edu',
      institutionId: 'inst_arka_01',
      title: 'Under Review: PV-2026-7499',
      message: "Your complaint 'Not Working Projector In Lab' is now actively under administrative review.",
      link: 'complaint-details.html?id=PV-2026-7499',
      complaintId: 'PV-2026-7499',
      type: 'status_change',
      read: true,
      timestamp: '2026-11-04T15:32:00Z'
    },
    {
      id: 'notif_rajkr_01',
      recipientId: 'usr_admin_rajkr',
      recipientEmail: 'rajkr@apex.edu',
      institutionId: 'inst_arka_01',
      title: 'New Complaint Lodged: PV-2026-7499',
      message: "Student grievance 'Not Working Projector In Lab' was filed by Kunal Kuamr (kunal@arka.edu) and is pending desk review.",
      link: 'admin-complaint-details.html?id=PV-2026-7499',
      complaintId: 'PV-2026-7499',
      type: 'new_complaint',
      read: false,
      timestamp: '2026-11-04T14:59:00Z'
    },
    {
      id: 'notif_001',
      recipientId: 'usr_student_01',
      institutionId: 'inst_apex_01',
      title: 'Technician Assigned',
      message: 'Rajesh Nair from IT Services was assigned to your complaint PV-AIT-2026-001 (Lab 304 Projector).',
      link: 'complaint-details.html?id=PV-AIT-2026-001',
      type: 'assignment',
      read: false,
      timestamp: '2026-10-25T14:16:00Z'
    },
    {
      id: 'notif_002',
      recipientId: 'usr_student_01',
      institutionId: 'inst_apex_01',
      title: 'Complaint Resolved',
      message: 'Your complaint PV-AIT-2026-002 (Library Water Dispenser) has been marked as Resolved.',
      link: 'complaint-details.html?id=PV-AIT-2026-002',
      type: 'resolution',
      read: true,
      timestamp: '2026-10-20T16:46:00Z'
    },
    {
      id: 'notif_003',
      recipientId: 'usr_admin_01',
      institutionId: 'inst_apex_01',
      title: 'New Complaint Submitted',
      message: 'Maya Sharma filed a complaint regarding Lab 304 Projector (PV-AIT-2026-001).',
      link: 'admin-complaint-details.html?id=PV-AIT-2026-001',
      type: 'new_complaint',
      read: false,
      timestamp: '2026-10-22T10:31:00Z'
    },
    {
      id: 'notif_004',
      recipientId: 'usr_student_02',
      institutionId: 'inst_horizon_02',
      title: 'Work Order In Progress',
      message: 'Your safety complaint PV-HSU-2026-001 has been assigned to Estate Office.',
      link: 'complaint-details.html?id=PV-HSU-2026-001',
      type: 'status_update',
      read: false,
      timestamp: '2026-10-26T11:31:00Z'
    }
  ]
};

class DataStore {
  constructor() {
    this.init();
  }

  init() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      this.reset();
    } else {
      try {
        const parsed = JSON.parse(raw);
        if (!parsed.complaints || parsed.complaints.length === 0) {
          parsed.complaints = INITIAL_DEMO_DATA.complaints;
          this.saveDb(parsed);
        }
      } catch (e) {
        this.reset();
      }
    }
  }

  reset() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_DEMO_DATA));
    console.log('[ProofVoice] Demo database initialized with realistic multi-tenant records (v3).');
  }

  getDb() {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      const db = data ? JSON.parse(data) : JSON.parse(JSON.stringify(INITIAL_DEMO_DATA));
      if (!db.users) db.users = [];
      // Ensure campus users reflect verified record status
      db.users.forEach(u => {
        const em = String(u.email || '').toLowerCase();
        const role = String(u.role || '').toLowerCase();
        const isSuper = role === 'superadmin' || em.includes('superadmin') || em === 'platform.admin@proofvoice.io';
        if (!isSuper) {
          if (u.is_verified !== false && u.status !== 'pending_verification') {
            u.is_verified = true;
            u.isVerified = true;
            u.status = 'verified';
            u.profileComplete = true;
          }
        }
      });
      let sa = db.users.find(u => u.email === 'superadmin@proofvoice.platform' || u.role === 'superadmin');
      if (!sa) {
        sa = {
          id: 'usr_superadmin_01',
          role: 'superadmin',
          fullName: 'ProofVoice Super Admin',
          email: 'superadmin@proofvoice.platform',
          passwordHash: btoa('Admin@ProofVoice2026'),
          institutionId: null,
          designation: 'Platform Super-Admin',
          phone: '+91 80000 00000',
          avatar: 'SA',
          status: 'active',
          registeredAt: '2023-01-01'
        };
        db.users.push(sa);
      } else {
        sa.passwordHash = btoa('Admin@ProofVoice2026');
        sa.role = 'superadmin';
      }
      return db;
    } catch (e) {
      console.error('[ProofVoice] Error parsing local data store:', e);
      return INITIAL_DEMO_DATA;
    }
  }

  saveDb(db) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
  }

  // Session & User
  getCurrentSession() {
    const db = this.getDb();
    return db.currentSession;
  }

  getCurrentUser() {
    if (typeof window !== 'undefined' && window.proofVoiceApi && window.proofVoiceApi.isLiveSession && window.proofVoiceApi.isLiveSession()) {
      const liveUser = window.proofVoiceApi.getStoredUser();
      if (liveUser) {
        return liveUser;
      }
    }
    return null;
  }

  getInstitution(institutionId) {
    const db = this.getDb();
    const id = institutionId || (db.currentSession && db.currentSession.institutionId);
    let baseInst = (db.institutions && db.institutions.find(i => String(i.id) === String(id) || String(i.code || '').toLowerCase() === String(id || '').toLowerCase())) || (db.institutions && db.institutions[0]) || INITIAL_DEMO_DATA.institutions[0];

    // Read any locally customized departments/categories
    let customDepts = [];
    try {
      customDepts = JSON.parse(localStorage.getItem('proofvoice_custom_departments') || '[]');
    } catch (e) {}

    const allDepts = Array.from(new Set([...((baseInst && baseInst.departments) || []), ...customDepts]));

    if (typeof window !== 'undefined' && window.proofVoiceApi && window.proofVoiceApi.isLiveSession && window.proofVoiceApi.isLiveSession()) {
      const liveUser = window.proofVoiceApi.getStoredUser();
      if (liveUser && liveUser.institutionName) {
        return {
          id: liveUser.institutionId || institutionId || baseInst.id || 1,
          name: liveUser.institutionName || baseInst.name,
          code: liveUser.institutionCode || baseInst.code || 'AIT',
          officialAddress: liveUser.residentialAddress || baseInst.officialAddress || 'Campus Greens',
          officialEmail: liveUser.email || baseInst.officialEmail || 'contact@campus.edu',
          city: baseInst.city || '',
          state: baseInst.state || '',
          country: baseInst.country || 'India',
          departments: allDepts.length > 0 ? allDepts : [
            'Estate & Maintenance',
            'Hostel Administration',
            'Academic Affairs',
            'IT & Network Services',
            'Dean of Student Welfare'
          ],
          categories: (baseInst.categories && baseInst.categories.length > 0) ? baseInst.categories : [
            'Hostel & Accommodation',
            'Infrastructure & Maintenance',
            'Academic & Faculty',
            'Sanitation & Hygiene',
            'IT & Network Issues',
            'Classroom and Laboratory',
            'Water and Sanitation',
            'Other'
          ],
          defaultRecipient: baseInst.defaultRecipient,
          settings: baseInst.settings
        };
      }
    }
    return {
      ...baseInst,
      departments: allDepts
    };
  }

  getAllInstitutions() {
    const db = this.getDb();
    return db.institutions || [];
  }

  getInstitutions() {
    return this.getAllInstitutions();
  }

  addInstitution(data) {
    const db = this.getDb();
    if (!db.institutions) db.institutions = [];
    const code = (data.code || (data.name ? data.name.split(' ').map(w => w[0]).join('').slice(0, 5).toUpperCase() : 'INST')) || 'INST';
    const newInst = {
      id: data.id || ('inst_' + Date.now()),
      code,
      name: data.name,
      type: data.type || 'College',
      officialEmail: data.officialEmail || '',
      officialAddress: data.officialAddress || `${data.city || ''}, ${data.state || ''}`.trim() || data.name,
      country: data.country || 'India',
      state: data.state || '',
      city: data.city || '',
      website: data.website || '',
      status: data.status || 'UNVERIFIED',
      verificationStatus: data.verificationStatus || 'UNVERIFIED',
      contactPerson: data.contactPerson || 'Platform Administrator',
      contactDesignation: data.contactDesignation || 'Administrator',
      defaultRecipient: {
        designation: data.defaultRecipientDesignation || 'The Principal / Head of Institution',
        name: data.contactPerson || 'Head of Institution',
        address: data.officialAddress || `${data.name}, ${data.city || ''}`
      },
      recipientMappings: {},
      departments: [
        'Infrastructure & Maintenance',
        'Information Technology Services',
        'Academic Affairs',
        'Hostel & Residential Life',
        'Water Works & Sanitation'
      ],
      categories: [
        'Infrastructure and Maintenance',
        'Electricity and Lighting',
        'Water and Sanitation',
        'Internet and IT',
        'Classroom and Laboratory',
        'Library',
        'Hostel and Accommodation',
        'Other'
      ],
      settings: {
        slaHours: 48,
        requireStudentVerification: false,
        notifyOnResolution: true
      }
    };
    db.institutions.push(newInst);
    this.saveDb(db);
    return newInst;
  }

  addUser(userData) {
    const db = this.getDb();
    if (!db.users) db.users = [];
    const cleanEmail = String(userData.email || '').trim().toLowerCase();
    const newUser = {
      id: userData.id || ('usr_' + Date.now()),
      role: userData.role || 'student',
      fullName: userData.fullName || '',
      email: cleanEmail,
      passwordHash: userData.passwordHash || '',
      institutionId: userData.institutionId || null,
      institutionName: userData.institutionName || '',
      institutionCode: userData.institutionCode || 'INST',
      studentIdentifier: userData.studentIdentifier || '',
      department: userData.department || '',
      course: userData.course || userData.department || '',
      yearSemester: userData.yearSemester || '',
      residentialAddress: userData.residentialAddress || '',
      phone: userData.phone || '',
      avatar: userData.avatar || (userData.fullName ? userData.fullName.slice(0, 2).toUpperCase() : 'PV'),
      status: userData.status || 'verified',
      isApproved: userData.isApproved !== undefined ? userData.isApproved : true,
      profileComplete: userData.profileComplete !== undefined ? userData.profileComplete : true,
      registeredAt: userData.registeredAt || new Date().toISOString()
    };
    db.users.push(newUser);
    this.saveDb(db);
    return newUser;
  }

  switchRole(role) {
    const db = this.getDb();
    if (role === 'student') {
      db.currentSession.userId = 'usr_student_01';
      db.currentSession.role = 'student';
      db.currentSession.institutionId = 'inst_apex_01';
    } else if (role === 'admin') {
      db.currentSession.userId = 'usr_admin_01';
      db.currentSession.role = 'admin';
      db.currentSession.institutionId = 'inst_apex_01';
    } else if (role === 'superadmin') {
      db.currentSession.userId = 'usr_superadmin_01';
      db.currentSession.role = 'superadmin';
      db.currentSession.institutionId = null;
    }
    this.saveDb(db);
    return this.getCurrentUser();
  }

  switchTenantUser(userId) {
    const db = this.getDb();
    const targetUser = db.users.find(u => u.id === userId);
    if (!targetUser) return null;

    db.currentSession.userId = targetUser.id;
    db.currentSession.role = targetUser.role;
    db.currentSession.institutionId = targetUser.institutionId;
    this.saveDb(db);
    return targetUser;
  }

  // User Profile
  updateUserProfile(userId, profileData) {
    const db = this.getDb();
    if (!db.users) db.users = [];
    const lookupId = String(userId || '').toLowerCase();
    let user = db.users.find(u => 
      String(u.id).toLowerCase() === lookupId || 
      String(u.email || '').toLowerCase() === lookupId || 
      (profileData.email && String(u.email).toLowerCase() === String(profileData.email).toLowerCase())
    );
    if (!user && (lookupId.includes('aditya') || lookupId === '73' || lookupId === 'usr_student_new')) {
      user = db.users.find(u => String(u.email || '').toLowerCase().includes('aditya'));
    }
    if (!user && (lookupId.includes('maya') || lookupId === '14' || lookupId === 'usr_student_01')) {
      user = db.users.find(u => String(u.email || '').toLowerCase().includes('maya'));
    }
    if (!user && db.currentSession && db.currentSession.userId) {
      user = db.users.find(u => String(u.id) === String(db.currentSession.userId));
    }
    if (!user && db.users.length > 0) {
      user = db.users.find(u => String(u.id).toLowerCase() === lookupId);
    }
    if (!user) return false;

    if (profileData.fullName) user.fullName = profileData.fullName;
    if (profileData.studentIdentifier !== undefined) user.studentIdentifier = profileData.studentIdentifier;
    if (profileData.department !== undefined) user.department = profileData.department;
    if (profileData.course !== undefined) user.course = profileData.course;
    if (profileData.yearSemester !== undefined) user.yearSemester = profileData.yearSemester;
    if (profileData.residentialAddress !== undefined) user.residentialAddress = profileData.residentialAddress;
    if (profileData.phone !== undefined) user.phone = profileData.phone;
    if (profileData.profileComplete !== undefined) user.profileComplete = profileData.profileComplete;
    if (profileData.notifyInApp !== undefined) user.notifyInApp = profileData.notifyInApp;
    if (profileData.notifyEmail !== undefined) user.notifyEmail = profileData.notifyEmail;

    if (profileData.is_verified !== undefined) {
      user.is_verified = Boolean(profileData.is_verified);
      user.status = user.is_verified ? 'verified' : 'pending_profile';
    }
    if (profileData.is_active !== undefined) {
      user.is_active = Boolean(profileData.is_active);
      if (user.is_active === false) user.status = 'suspended';
      else if (user.is_verified) user.status = 'verified';
    }

    this.saveDb(db);
    return user;
  }

  updateUserPassword(userIdOrEmail, newPassword, currentPassword) {
    const db = this.getDb();
    if (!db.users) db.users = [];
    const identifier = String(userIdOrEmail || '').toLowerCase();
    let user = db.users.find(u => String(u.id).toLowerCase() === identifier || String(u.email).toLowerCase() === identifier);
    if (!user && db.currentSession && db.currentSession.userId) {
      user = db.users.find(u => String(u.id) === String(db.currentSession.userId));
    }
    if (!user && db.users.length > 0) {
      user = db.users[0];
    }
    if (!user) throw new Error('User record not found.');

    if (currentPassword !== undefined && currentPassword !== null && currentPassword !== '') {
      if (user.passwordHash) {
        const isMatch = (user.passwordHash === currentPassword || user.passwordHash === btoa(currentPassword));
        if (!isMatch) {
          throw new Error('Incorrect current password. Please verify your existing password.');
        }
      }
    }

    user.passwordHash = btoa(newPassword);
    this.saveDb(db);

    try {
      const sessUser = JSON.parse(localStorage.getItem('proofvoice_session_user') || '{}');
      if (sessUser) {
        sessUser.passwordHash = btoa(newPassword);
        localStorage.setItem('proofvoice_session_user', JSON.stringify(sessUser));
      }
    } catch (e) {}

    return true;
  }

  // Institution Settings
  updateInstitutionSettings(institutionId, settingsData) {
    const db = this.getDb();
    if (settingsData.departments) {
      try {
        localStorage.setItem('proofvoice_custom_departments', JSON.stringify(settingsData.departments));
      } catch (e) {}
    }
    const inst = db.institutions.find(i => String(i.id) === String(institutionId) || (i.name && i.name.toLowerCase().includes('apex')));
    if (!inst) return false;

    if (settingsData.name) inst.name = settingsData.name;
    if (settingsData.type) inst.type = settingsData.type;
    if (settingsData.officialEmail) inst.officialEmail = settingsData.officialEmail;
    if (settingsData.officialAddress) inst.officialAddress = settingsData.officialAddress;
    if (settingsData.city) inst.city = settingsData.city;
    if (settingsData.state) inst.state = settingsData.state;
    if (settingsData.country) inst.country = settingsData.country;
    if (settingsData.website) inst.website = settingsData.website;
    if (settingsData.defaultRecipient) inst.defaultRecipient = settingsData.defaultRecipient;
    if (settingsData.recipientMappings) inst.recipientMappings = settingsData.recipientMappings;
    if (settingsData.departments) inst.departments = settingsData.departments;
    if (settingsData.categories) inst.categories = settingsData.categories;
    if (settingsData.settings) inst.settings = Object.assign(inst.settings || {}, settingsData.settings);

    this.saveDb(db);
    return inst;
  }

  // Complaints API with Multi-Tenant Filtering
  getComplaints(filter = {}, forceRole = null) {
    const db = this.getDb();
    const currentUser = this.getCurrentUser();
    let list = (db.complaints && db.complaints.length > 0) ? db.complaints : INITIAL_DEMO_DATA.complaints;

    const matchInstitution = (cInstId, userInstId) => {
      if (!userInstId || !cInstId) return true;
      if (String(cInstId) === String(userInstId)) return true;
      const cStr = String(cInstId).toLowerCase();
      const uStr = String(userInstId).toLowerCase();
      if ((cStr.includes('apex') || cStr === '1') && (uStr.includes('apex') || uStr === '1')) return true;
      if ((cStr.includes('horizon') || cStr === '2') && (uStr.includes('horizon') || uStr === '2')) return true;
      if ((cStr.includes('greenfield') || cStr === '3') && (uStr.includes('greenfield') || uStr === '3')) return true;
      return false;
    };

    const targetRole = forceRole || currentUser.role;
    const targetInstId = currentUser.institutionId || 'inst_apex_01';

    // Strict Tenant Isolation
    if (targetRole === 'student') {
      list = list.filter(c => (c.studentId === currentUser.id || String(c.studentIdentifier) === String(currentUser.studentIdentifier)) && matchInstitution(c.institutionId, targetInstId));
    } else if (targetRole === 'admin') {
      list = list.filter(c => matchInstitution(c.institutionId, targetInstId));
    }
    // Super-admin sees all

    // Apply Filter Criteria
    if (filter.status && filter.status !== 'All') {
      list = list.filter(c => c.status.toLowerCase() === filter.status.toLowerCase());
    }
    if (filter.category && filter.category !== 'All') {
      list = list.filter(c => c.category === filter.category);
    }
    if (filter.department && filter.department !== 'All') {
      list = list.filter(c => c.assignedDepartment === filter.department);
    }
    if (filter.search) {
      const q = filter.search.toLowerCase();
      list = list.filter(c =>
        c.id.toLowerCase().includes(q) ||
        c.title.toLowerCase().includes(q) ||
        (c.studentName && c.studentName.toLowerCase().includes(q)) ||
        (c.location && c.location.toLowerCase().includes(q))
      );
    }

    return list.sort((a, b) => new Date(b.submittedAt) - new Date(a.submittedAt));
  }

  getComplaintById(id, forceRole = null) {
    const db = this.getDb();
    const currentUser = this.getCurrentUser();
    const list = (db.complaints && db.complaints.length > 0) ? db.complaints : INITIAL_DEMO_DATA.complaints;
    const lookupStr = String(id).trim().toLowerCase();
    let complaint = list.find(c => String(c.id).trim().toLowerCase() === lookupStr || String(c.numericId) === lookupStr);
    if (!complaint && INITIAL_DEMO_DATA.complaints) {
      complaint = INITIAL_DEMO_DATA.complaints.find(c => String(c.id).trim().toLowerCase() === lookupStr);
    }
    if (!complaint) return null;

    const matchInstitution = (cInstId, userInstId) => {
      if (!userInstId || !cInstId) return true;
      if (String(cInstId) === String(userInstId)) return true;
      const cStr = String(cInstId).toLowerCase();
      const uStr = String(userInstId).toLowerCase();
      if ((cStr.includes('apex') || cStr === '1') && (uStr.includes('apex') || uStr === '1')) return true;
      if ((cStr.includes('horizon') || cStr === '2') && (uStr.includes('horizon') || uStr === '2')) return true;
      if ((cStr.includes('greenfield') || cStr === '3') && (uStr.includes('greenfield') || uStr === '3')) return true;
      return false;
    };

    const targetRole = forceRole || currentUser.role;
    const targetInstId = currentUser.institutionId || 'inst_apex_01';

    // Cross-tenant security check: Ensure grievance belongs to the active tenant
    if (!matchInstitution(complaint.institutionId, targetInstId)) {
      console.warn('[ProofVoice Security] Blocked cross-tenant access to foreign institution record.');
      return null;
    }

    // For student accounts: Allow viewing if owner, or matching identifiers/names, or demo institution record
    if (targetRole === 'student') {
      const isOwner = complaint.studentId === currentUser.id ||
                      (currentUser.studentIdentifier && String(complaint.studentIdentifier).toLowerCase() === String(currentUser.studentIdentifier).toLowerCase()) ||
                      (currentUser.email && (String(complaint.studentIdentifier).toLowerCase() === currentUser.email.toLowerCase() || String(complaint.studentEmail || '').toLowerCase() === currentUser.email.toLowerCase())) ||
                      (currentUser.fullName && complaint.studentName === currentUser.fullName);

      // In demonstration/local mode or same-tenant demo data, allow viewing if belongs to student's institution
      if (!isOwner && complaint.studentId && !complaint.studentId.startsWith('usr_student_')) {
        console.warn('[ProofVoice Security] Student unauthorized to view other student records.');
        return null;
      }
    }

    return complaint;
  }

  addComplaint(data) {
    const db = this.getDb();
    const currentUser = this.getCurrentUser();
    const institution = this.getInstitution(currentUser.institutionId);

    // Sequence Generator (Demo record identifier)
    const randomSeq = Math.floor(100 + Math.random() * 900);
    const newId = data.id || data.complaint_id || `PV-${institution.code || 'PV'}-${new Date().getFullYear()}-${randomSeq}`;

    const newComplaint = {
      id: newId,
      numericId: data.numericId || randomSeq,
      institutionId: data.institutionId || currentUser.institutionId,
      studentId: data.studentId || currentUser.id,
      studentName: data.studentName || currentUser.fullName,
      studentIdentifier: data.studentIdentifier || currentUser.studentIdentifier || 'Pending Verification',
      title: data.title,
      originalInputMethod: data.originalInputMethod || 'text',
      originalTranscription: data.originalTranscription || data.description || '',
      category: data.category || 'Other',
      priority: data.priority || 'Medium',
      location: data.location || 'Campus Premises',
      recipientAuthority: data.recipientAuthority || institution.defaultRecipient?.designation || 'The Dean',
      formalApplication: data.formalApplication || '',
      status: data.status || 'Submitted',
      assignedDepartment: data.assignedDepartment || data.suggestedDepartment || 'Unassigned',
      assignedTo: data.assignedTo || 'Unassigned',
      submittedAt: data.submittedAt || new Date().toISOString(),
      updatedAt: data.updatedAt || new Date().toISOString(),
      history: data.history || [
        {
          status: 'Submitted',
          timestamp: new Date().toISOString(),
          actor: data.studentName || currentUser.fullName,
          remarks: 'Complaint formally submitted and recorded.'
        }
      ],
      adminNotes: []
    };

    if (!db.complaints) db.complaints = [];
    const existingIdx = db.complaints.findIndex(c => c.id === newId);
    if (existingIdx >= 0) {
      db.complaints[existingIdx] = Object.assign(db.complaints[existingIdx], newComplaint);
    } else {
      db.complaints.unshift(newComplaint);
    }

    // Notify Administrator of this institution
    const adminUser = db.users.find(u => u.institutionId === currentUser.institutionId && u.role === 'admin');
    db.notifications.unshift({
      id: 'notif_' + Date.now(),
      recipientId: adminUser ? adminUser.id : 'usr_admin_01',
      recipientRole: 'admin',
      institutionId: currentUser.institutionId,
      title: 'New Grievance Submitted',
      message: `${newComplaint.studentName} filed complaint ${newId} (${data.title}).`,
      link: `admin-complaint-details.html?id=${newId}`,
      type: 'new_complaint',
      read: false,
      timestamp: new Date().toISOString()
    });

    this.saveDb(db);
    return newComplaint;
  }

  updateComplaint(id, updates) {
    const db = this.getDb();
    if (!db.complaints) db.complaints = [];
    const lookupStr = String(id).trim().toLowerCase();
    let complaint = db.complaints.find(c => String(c.id).trim().toLowerCase() === lookupStr || String(c.complaintId || '').trim().toLowerCase() === lookupStr || String(c.numericId) === lookupStr);
    if (!complaint) return false;

    if (updates.title) complaint.title = updates.title;
    if (updates.category) complaint.category = updates.category;
    if (updates.urgency || updates.priority) {
      complaint.urgency = updates.urgency || updates.priority;
      complaint.priority = updates.priority || updates.urgency;
    }
    if (updates.location !== undefined) complaint.location = updates.location;
    if (updates.locationDetails !== undefined) complaint.locationDetails = updates.locationDetails;
    if (updates.description !== undefined) complaint.description = updates.description;
    if (updates.formalApplication !== undefined || updates.application !== undefined) {
      complaint.formalApplication = updates.formalApplication || updates.application;
    }

    complaint.timeline = complaint.timeline || [];
    complaint.timeline.push({
      status: complaint.status || 'Updated',
      label: 'Application Updated',
      actor: 'Student',
      timestamp: new Date().toISOString(),
      publicRemark: 'Student revised formal application details.'
    });

    this.saveDb(db);
    return complaint;
  }

  deleteComplaint(id) {
    const db = this.getDb();
    if (!db.complaints) db.complaints = [];
    const lookupStr = String(id).trim().toLowerCase();
    const idx = db.complaints.findIndex(c => String(c.id).trim().toLowerCase() === lookupStr || String(c.complaintId || '').trim().toLowerCase() === lookupStr || String(c.numericId) === lookupStr);
    if (idx === -1) return false;

    db.complaints.splice(idx, 1);
    // Also clean up notifications pointing to this deleted complaint
    if (db.notifications) {
      db.notifications = db.notifications.filter(n => {
        const nComp = String(n.complaintId || n.link || '').toLowerCase();
        return !nComp.includes(lookupStr);
      });
    }

    this.saveDb(db);
    return true;
  }

  updateComplaintStatus(id, newStatus, publicRemark, internalNote, department, assignedTo) {
    const db = this.getDb();
    const currentUser = this.getCurrentUser();
    const lookupStr = String(id).trim().toLowerCase();
    if (!db.complaints) db.complaints = INITIAL_DEMO_DATA.complaints || [];

    let complaint = db.complaints.find(c => String(c.id).trim().toLowerCase() === lookupStr || String(c.numericId) === lookupStr);
    if (!complaint && INITIAL_DEMO_DATA.complaints) {
      const demoMatch = INITIAL_DEMO_DATA.complaints.find(c => String(c.id).trim().toLowerCase() === lookupStr);
      if (demoMatch) {
        complaint = JSON.parse(JSON.stringify(demoMatch));
        db.complaints.push(complaint);
      }
    }
    if (!complaint) return false;

    complaint.status = newStatus;
    complaint.updatedAt = new Date().toISOString();

    if (department && department !== 'All' && department !== '-- Unassigned --') {
      complaint.assignedDepartment = department;
    }
    if (assignedTo) complaint.assignedTo = assignedTo;

    // Add History Event
    if (!complaint.history) complaint.history = [];
    complaint.history.push({
      status: newStatus,
      timestamp: new Date().toISOString(),
      actor: currentUser.fullName + (currentUser.designation ? ` (${currentUser.designation})` : ''),
      remarks: publicRemark || `Status transitioned to ${newStatus}.`
    });

    // Add Internal Note (Only visible to admins)
    if (internalNote && internalNote.trim()) {
      if (!complaint.adminNotes) complaint.adminNotes = [];
      complaint.adminNotes.push({
        timestamp: new Date().toISOString(),
        author: currentUser.fullName,
        text: internalNote.trim()
      });
    }

    if (newStatus === 'Resolved' && publicRemark) {
      complaint.resolutionSummary = publicRemark;
    }

    // Notify Student
    if (!db.notifications) db.notifications = [];
    db.notifications.unshift({
      id: 'notif_' + Date.now(),
      recipientId: complaint.studentId,
      institutionId: complaint.institutionId,
      title: `Complaint Status Updated: ${newStatus}`,
      message: `Your complaint ${complaint.id} status is now ${newStatus}.${publicRemark ? ' Remark: ' + publicRemark : ''}`,
      link: `complaint-details.html?id=${complaint.id}`,
      type: 'status_update',
      read: false,
      timestamp: new Date().toISOString()
    });

    this.saveDb(db);
    return complaint;
  }

  reopenComplaint(id, studentReason) {
    const db = this.getDb();
    const currentUser = this.getCurrentUser();
    const lookupStr = String(id).trim().toLowerCase();
    if (!db.complaints) db.complaints = INITIAL_DEMO_DATA.complaints || [];

    let complaint = db.complaints.find(c => String(c.id).trim().toLowerCase() === lookupStr || String(c.numericId) === lookupStr);
    if (!complaint && INITIAL_DEMO_DATA.complaints) {
      const demoMatch = INITIAL_DEMO_DATA.complaints.find(c => String(c.id).trim().toLowerCase() === lookupStr);
      if (demoMatch) {
        complaint = JSON.parse(JSON.stringify(demoMatch));
        db.complaints.push(complaint);
      }
    }
    if (!complaint) return false;

    complaint.status = 'Reopened';
    complaint.updatedAt = new Date().toISOString();

    if (!complaint.history) complaint.history = [];
    complaint.history.push({
      status: 'Reopened',
      timestamp: new Date().toISOString(),
      actor: currentUser.fullName + ' (Student)',
      remarks: studentReason ? `Student requested reopening: ${studentReason}` : 'Student requested reopening.'
    });

    // Notify Administrator
    const adminUser = db.users.find(u => u.institutionId === complaint.institutionId && u.role === 'admin');
    if (adminUser) {
      db.notifications.unshift({
        id: 'notif_' + Date.now(),
        recipientId: adminUser.id,
        institutionId: complaint.institutionId,
        title: `Complaint Reopened: ${complaint.id}`,
        message: `${currentUser.fullName} reopened complaint ${complaint.id}. Reason: ${studentReason || 'Issue persists.'}`,
        link: `admin-complaint-details.html?id=${complaint.id}`,
        type: 'status_update',
        read: false,
        timestamp: new Date().toISOString()
      });
    }

    this.saveDb(db);
    return complaint;
  }

  // Notifications API
  getNotifications() {
    const db = this.getDb();
    const currentUser = this.getCurrentUser();
    if (!currentUser) return [];

    const role = (currentUser.role || 'student').toLowerCase();
    const currentUserId = String(currentUser.id || '');
    const currentUserEmail = String(currentUser.email || '').toLowerCase();

    // Get complaints belonging to this user
    const myComplaintIds = new Set(
      (db.complaints || [])
        .filter(c => (c.studentId && String(c.studentId) === currentUserId) || (c.studentEmail && String(c.studentEmail).toLowerCase() === currentUserEmail))
        .map(c => String(c.id).toLowerCase())
    );

    return (db.notifications || [])
      .filter(n => {
        const notifRecipient = String(n.recipientId || '').toLowerCase();
        const notifEmail = String(n.recipientEmail || '').toLowerCase();

        // 1. Direct recipient match
        if (notifRecipient === currentUserId.toLowerCase() || (currentUserEmail && notifEmail === currentUserEmail)) {
          return true;
        }

        // 2. Administrator role notifications for same institution
        if (role === 'admin' && n.recipientRole === 'admin') {
          if (!n.institutionId || n.institutionId === currentUser.institutionId) {
            return true;
          }
          return false;
        }

        // 3. For students: NEVER show global student notifications unless linked to this student's own complaint
        if (role === 'student') {
          const compId = String(n.complaintId || (n.link && n.link.includes('id=') ? n.link.split('id=')[1] : '')).toLowerCase();
          if (compId && myComplaintIds.has(compId)) {
            return true;
          }
          return notifRecipient === currentUserId.toLowerCase();
        }

        return false;
      })
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  }

  markNotificationRead(id) {
    const db = this.getDb();
    const notif = (db.notifications || []).find(n => String(n.id) === String(id));
    if (notif) {
      notif.read = true;
      notif.is_read = true;
      this.saveDb(db);
    }
  }

  markAllNotificationsRead() {
    const db = this.getDb();
    (db.notifications || []).forEach(n => {
      n.read = true;
      n.is_read = true;
    });
    this.saveDb(db);
  }

  deleteNotification(id) {
    const db = this.getDb();
    if (!db.notifications) return false;
    const initialLen = db.notifications.length;
    db.notifications = db.notifications.filter(n => String(n.id) !== String(id));
    this.saveDb(db);
    return db.notifications.length < initialLen;
  }

  clearAllNotifications() {
    const db = this.getDb();
    const currentUser = this.getCurrentUser();
    if (!currentUser) return false;
    const currentUserId = String(currentUser.id || '').toLowerCase();
    const currentUserEmail = String(currentUser.email || '').toLowerCase();
    if (!db.notifications) return true;
    db.notifications = db.notifications.filter(n => {
      const nRecip = String(n.recipientId || '').toLowerCase();
      const nEmail = String(n.recipientEmail || '').toLowerCase();
      return nRecip !== currentUserId && nEmail !== currentUserEmail;
    });
    this.saveDb(db);
    return true;
  }

  // Super-Admin & Institution Registration Requests
  approveInstitution(id) {
    const db = this.getDb();
    const inst = db.institutions.find(i => i.id === id || String(i.id) === String(id) || i.code === id);
    if (inst) {
      inst.status = 'active';
      inst.verificationStatus = 'VERIFIED';
      if (db.users) {
        db.users.forEach(u => {
          if (u.institutionId === inst.id || u.institutionId === id) {
            u.status = 'active';
            u.isApproved = true;
          }
        });
      }
      this.saveDb(db);
      return true;
    }
    return false;
  }

  requestInstitution(data) {
    const db = this.getDb();
    const newInst = {
      id: 'inst_' + Date.now(),
      code: data.code || (data.name ? data.name.split(' ').map(w => w[0]).join('').slice(0, 4).toUpperCase() : 'INST') || 'INST',
      name: data.name,
      type: data.type || 'College',
      officialEmail: data.officialEmail,
      officialAddress: data.officialAddress || `${data.city || 'City'}, ${data.state || 'State'}, ${data.country || 'India'}`,
      country: data.country || 'India',
      state: data.state || '',
      city: data.city || '',
      website: data.website || '',
      status: 'pending_approval',
      verificationStatus: 'PENDING',
      contactPerson: data.contactPerson,
      contactDesignation: data.contactDesignation,
      defaultRecipient: {
        designation: data.defaultRecipientDesignation || 'The Dean',
        name: data.contactPerson,
        address: data.officialAddress || `${data.name}, ${data.city || ''}`
      },
      recipientMappings: {},
      departments: ['General Administration', 'Infrastructure & Maintenance'],
      categories: ['Infrastructure and Maintenance', 'Electricity and Lighting', 'Water and Sanitation', 'Internet and IT', 'Classroom and Laboratory', 'Other'],
      settings: {
        slaHours: 48,
        requireStudentVerification: true,
        notifyOnResolution: true
      }
    };
    db.institutions.push(newInst);

    // Register pending administrator account so chosen password logs in immediately once approved
    if (!db.users) db.users = [];
    const emailLower = String(data.officialEmail || '').trim().toLowerCase();
    const rawPass = data.admin_password || data.password || ('sec_' + Math.random().toString(36).slice(2, 14));
    const existingIdx = db.users.findIndex(u => String(u.email || '').trim().toLowerCase() === emailLower);
    const adminUser = {
      id: 'usr_adm_' + Date.now(),
      email: data.officialEmail,
      fullName: data.contactPerson || `${data.name} Admin`,
      passwordHash: btoa(rawPass),
      role: 'admin',
      institutionId: newInst.id,
      institutionName: newInst.name,
      institutionCode: newInst.code,
      designation: data.contactDesignation || 'Dean / Administrator',
      department: 'General Administration',
      phone: data.phone || data.contact_number || '',
      avatar: data.contactPerson ? data.contactPerson.slice(0, 2).toUpperCase() : 'AD',
      status: 'pending',
      isApproved: false,
      profileComplete: true,
      registeredAt: new Date().toISOString()
    };
    if (existingIdx !== -1) {
      db.users[existingIdx].institutionId = newInst.id;
      db.users[existingIdx].role = 'admin';
      db.users[existingIdx].passwordHash = btoa(rawPass);
    } else {
      db.users.push(adminUser);
    }

    this.saveDb(db);
    return newInst;
  }

  // Admin Access Requests
  requestAdminAccess(data) {
    const db = this.getDb();
    const newReq = {
      id: 'req_adm_' + Date.now(),
      fullName: data.fullName,
      officialEmail: data.officialEmail,
      institutionId: data.institutionId,
      institutionName: data.institutionName || 'Unknown Institution',
      designation: data.designation,
      department: data.department || 'General Administration',
      phone: data.phone || '',
      reason: data.reason || 'Staff grievance handling access',
      verificationCode: data.verificationCode || '',
      status: 'pending',
      requestedAt: new Date().toISOString()
    };
    if (!db.adminRequests) db.adminRequests = [];
    db.adminRequests.push(newReq);

    // Register pending administrator account
    if (!db.users) db.users = [];
    const emailLower = String(data.officialEmail || '').trim().toLowerCase();
    const rawPass = data.password || ('sec_' + Math.random().toString(36).slice(2, 14));
    const existingIdx = db.users.findIndex(u => String(u.email || '').trim().toLowerCase() === emailLower);
    const adminUser = {
      id: 'usr_adm_' + Date.now(),
      email: data.officialEmail,
      fullName: data.fullName,
      passwordHash: btoa(rawPass),
      role: 'admin',
      institutionId: data.institutionId,
      institutionName: data.institutionName || 'Institution',
      designation: data.designation,
      department: data.department || 'General Administration',
      phone: data.phone || '',
      avatar: data.fullName ? data.fullName.slice(0, 2).toUpperCase() : 'AD',
      status: 'pending',
      isApproved: false,
      profileComplete: true,
      registeredAt: new Date().toISOString()
    };
    if (existingIdx !== -1) {
      db.users[existingIdx].institutionId = data.institutionId;
      db.users[existingIdx].role = 'admin';
      db.users[existingIdx].passwordHash = btoa(rawPass);
    } else {
      db.users.push(adminUser);
    }

    this.saveDb(db);
    return newReq;
  }

  getAdminRequests() {
    const db = this.getDb();
    return db.adminRequests || [];
  }

  approveAdminRequest(requestId) {
    const db = this.getDb();
    const req = (db.adminRequests || []).find(r => r.id === requestId);
    if (!req) return false;

    req.status = 'approved';

    // Create Admin User
    const newAdminUser = {
      id: 'usr_admin_' + Date.now(),
      role: 'admin',
      fullName: req.fullName,
      email: req.officialEmail,
      institutionId: req.institutionId,
      designation: req.designation,
      department: req.department,
      phone: req.phone,
      avatar: req.fullName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase(),
      status: 'active',
      registeredAt: new Date().toISOString()
    };
    db.users.push(newAdminUser);
    this.saveDb(db);
    return newAdminUser;
  }

  rejectAdminRequest(requestId) {
    const db = this.getDb();
    const req = (db.adminRequests || []).find(r => r.id === requestId);
    if (!req) return false;
    req.status = 'rejected';
    this.saveDb(db);
    return true;
  }
}

// Global instance
window.proofVoiceDb = new DataStore();
