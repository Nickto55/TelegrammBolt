// Types for BOLT Application

export interface User {
  id: string;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  role: 'admin' | 'responder' | 'initiator' | 'user';
  auth_type: 'telegram' | 'qr' | 'admin';
  telegram_linked?: boolean;
}

export interface Permissions {
  dashboard?: boolean;
  view_dse?: boolean;
  create_dse?: boolean;
  edit_dse?: boolean;
  delete_dse?: boolean;
  chat?: boolean;
  admin_panel?: boolean;
  manage_users?: boolean;
  view_users?: boolean;
  manage_invites?: boolean;
  terminal?: boolean;
  export_data?: boolean;
  export_pdf?: boolean;
  export_excel?: boolean;
  approve_dse_requests?: boolean;
  view_dashboard_stats?: boolean;
}

export interface DSE {
  id: string;
  dse: string;
  dse_name?: string;
  problem_type: string;
  description?: string;
  machine_number?: string;
  installer_fio?: string;
  programmer_name?: string;
  datetime?: string;
  created_at?: string;
  user_id?: string;
  status?: string;
  hidden?: boolean;
}

export interface PendingRequest {
  id: string;
  dse: string;
  dse_name?: string;
  problem_type: string;
  user_id?: string;
  created_at?: string;
}

export interface DashboardStats {
  total_dse: number;
  active_users: number;
  recent_dse: number;
  problem_types?: Record<string, number>;
}

export interface NavItem {
  label: string;
  icon: string;
  path: string;
  permission?: keyof Permissions;
  badge?: number;
  children?: NavItem[];
}
