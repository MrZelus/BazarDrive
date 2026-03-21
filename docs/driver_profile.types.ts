export type ScreenStatus = 'loading' | 'loaded' | 'empty' | 'error';
export type ProfileStatus = 'active' | 'pending_verification' | 'blocked';
export type DocumentStatus = 'uploaded' | 'checking' | 'approved' | 'rejected' | 'expired' | 'expiring_soon';
export type LicenseStatus = 'active' | 'expiring_soon' | 'expired' | 'missing';
export type PayoutStatus = 'connected' | 'pending' | 'disabled';

export type TabId = 'overview' | 'taxi_ip' | 'documents' | 'payouts' | 'security';

export interface DriverProfilePayload {
  screen: Screen;
  data: DriverProfileData;
  ui: DriverProfileUI;
  actions: Record<ActionId, ActionConfig>;
  enums: DriverProfileEnums;
}

export interface Screen {
  id: 'driverProfile';
  title: string;
  role: 'taxi_driver';
  businessType: 'ip';
  taxMode: 'usn_income';
  layout: {
    type: 'page';
    sections: Array<'header' | 'quickStatuses' | 'tabs' | 'content' | 'stickyActions'>;
  };
  state: {
    status: ScreenStatus;
    activeTab: TabId;
    isEditing: boolean;
    isMobile: boolean;
    error: string | null;
  };
}

export interface DriverProfileData {
  user: User;
  professional: Professional;
  insurance: Insurance;
  documents: Document[];
  payouts: Payouts;
  security: Security;
}

export interface User {
  id: string;
  avatar: {
    url: string;
    placeholder: boolean;
  };
  fullName: string;
  phone: string;
  email: string;
  city: string;
  workZone: string;
  rating: number;
  tripsCompleted: number;
  profileStatus: ProfileStatus;
  registeredAt: string;
}

export interface Professional {
  roleLabel: string;
  businessTypeLabel: string;
  taxModeLabel: string;
  taxRatePercent: number;
  inn: string;
  ogrnip: string;
  ipRegisteredAt: string;
  license: {
    number: string;
    region: string;
    status: LicenseStatus;
    expiresAt: string;
  };
  driverLicense: {
    number: string;
    status: 'valid' | 'expiring_soon' | 'expired';
    expiresAt: string;
    experienceYears: number;
  };
  vehicle: {
    brand: string;
    model: string;
    year: number;
    color: string;
    plateNumber: string;
  };
}

export interface Insurance {
  osago: InsuranceItem;
  diagnosticCard: InsuranceItem;
}

export interface InsuranceItem {
  status: 'valid' | 'expiring_soon' | 'expired';
  expiresAt: string;
}

export interface Document {
  id: string;
  type:
    | 'passport'
    | 'inn'
    | 'ogrnip'
    | 'taxi_license'
    | 'driver_license'
    | 'sts'
    | 'osago'
    | 'diagnostic_card';
  title: string;
  uploadedAt: string;
  expiresAt: string | null;
  status: DocumentStatus;
  fileUrl: string;
}

export interface Payouts {
  status: PayoutStatus;
  bankName: string;
  bik: string;
  accountNumber: string;
  recipient: string;
  dayIncome: number;
  weekIncome: number;
  monthIncome: number;
  taxReserve: number;
  history: PayoutHistoryItem[];
}

export interface PayoutHistoryItem {
  id: string;
  date: string;
  amount: number;
  status: 'completed' | 'pending' | 'failed';
}

export interface Security {
  phoneVerified: boolean;
  emailVerified: boolean;
  twoFactorEnabled: boolean;
  activeDevices: ActiveDevice[];
}

export interface ActiveDevice {
  id: string;
  name: string;
  lastSeen: string;
  current: boolean;
}

export interface DriverProfileUI {
  header: {
    component: 'ProfileHeader';
    props: {
      showAvatar: boolean;
      showEditAvatar: boolean;
      titleField: string;
      subtitle: string[];
      statusField: string;
    };
  };
  quickStatuses: {
    component: 'StatusCardsRow';
    items: QuickStatus[];
  };
  tabs: {
    component: 'ProfileTabs';
    items: TabItem[];
    activeTabField: string;
  };
  content: {
    component: 'TabContentRouter';
    views: Record<TabId, TabView>;
  };
  stickyActions: {
    component: 'StickyActionBar';
    actions: StickyAction[];
  };
}

export interface QuickStatus {
  id: string;
  label: string;
  value: string;
  status: 'ok' | 'warning' | 'error';
}

export interface TabItem {
  id: TabId;
  label: string;
}

export interface TabView {
  component: string;
  blocks?: unknown[];
  listField?: string;
  itemComponent?: string;
  emptyState?: {
    title: string;
    action: ActionId;
  };
}

export type ActionId =
  | 'editProfile'
  | 'uploadDocument'
  | 'openPayouts'
  | 'openSecurity'
  | 'changeAvatar'
  | 'toggle2FA'
  | 'deleteDocument';

export type ActionConfig =
  | { type: 'navigate'; target: string }
  | { type: 'modal'; target: string }
  | { type: 'setActiveTab'; target: TabId }
  | { type: 'fileUpload'; target: 'avatar' }
  | { type: 'api'; method: 'PATCH'; target: string }
  | { type: 'confirmThenApi'; method: 'DELETE'; target: string };

export interface StickyAction {
  id: ActionId;
  label: string;
  style: 'primary' | 'secondary' | 'ghost';
}

export interface DriverProfileEnums {
  screenStatus: ScreenStatus[];
  profileStatus: ProfileStatus[];
  documentStatus: DocumentStatus[];
  licenseStatus: LicenseStatus[];
  payoutStatus: PayoutStatus[];
}
