// =============================
// ENUMS
// =============================

export type ScreenStatus = 'loading' | 'loaded' | 'empty' | 'error';

export type ProfileStatus = 'active' | 'pending_verification' | 'blocked';

export type DocumentStatus =
  | 'uploaded'
  | 'checking'
  | 'approved'
  | 'rejected'
  | 'expired'
  | 'expiring_soon';

export type LicenseStatus =
  | 'active'
  | 'expiring_soon'
  | 'expired'
  | 'missing';

export type PayoutStatus = 'connected' | 'pending' | 'disabled';

export type DriverLicenseStatus = 'valid' | 'expiring' | 'expired';

export type ProfileTabId =
  | 'overview'
  | 'taxi_ip'
  | 'documents'
  | 'payouts'
  | 'security';

export type ActionStyle = 'primary' | 'secondary' | 'ghost';

// =============================
// SCREEN META
// =============================

export interface DriverProfileScreenState {
  status: ScreenStatus;
  activeTab: ProfileTabId;
  isEditing: boolean;
  isMobile: boolean;
  error: string | null;
}

export interface DriverProfileScreenMeta {
  id: 'driverProfile';
  title: string;
  role: 'taxi_driver';
  businessType: 'ip';
  taxMode: 'usn_income';
  state: DriverProfileScreenState;
}

// =============================
// USER
// =============================

export interface AvatarData {
  url: string | null;
  placeholder: boolean;
}

export interface DriverProfileUser {
  id: string;
  avatar: AvatarData;
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

// =============================
// PROFESSIONAL (TAXI / IP)
// =============================

export interface TaxiLicense {
  number: string;
  region: string;
  status: LicenseStatus;
  expiresAt: string;
}

export interface DriverLicense {
  number: string;
  status: DriverLicenseStatus;
  expiresAt: string;
  experienceYears: number;
}

export interface VehicleInfo {
  brand: string;
  model: string;
  year: number;
  color: string;
  plateNumber: string;
}

export interface ProfessionalInfo {
  roleLabel: string;
  businessTypeLabel: string;
  taxModeLabel: string;
  taxRatePercent: number;
  inn: string;
  ogrnip: string;
  ipRegisteredAt: string;
  license: TaxiLicense;
  driverLicense: DriverLicense;
  vehicle: VehicleInfo;
}

// =============================
// DOCUMENTS
// =============================

export type DocumentType =
  | 'passport'
  | 'inn'
  | 'ogrnip'
  | 'taxi_license'
  | 'driver_license'
  | 'sts'
  | 'osago'
  | 'diagnostic_card';

export interface DriverDocument {
  id: string;
  type: DocumentType;
  title: string;
  uploadedAt: string;
  expiresAt: string | null;
  status: DocumentStatus;
  fileUrl: string;
}

// =============================
// PAYOUTS
// =============================

export interface PayoutHistoryItem {
  id: string;
  date: string;
  amount: number;
  status: 'completed' | 'pending' | 'failed';
}

export interface PayoutsInfo {
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

// =============================
// SECURITY
// =============================

export interface ActiveDevice {
  id: string;
  name: string;
  lastSeen: string;
  current: boolean;
}

export interface SecurityInfo {
  phoneVerified: boolean;
  emailVerified: boolean;
  twoFactorEnabled: boolean;
  activeDevices: ActiveDevice[];
}

// =============================
// ROOT DATA
// =============================

export interface DriverProfileData {
  user: DriverProfileUser;
  professional: ProfessionalInfo;
  documents: DriverDocument[];
  payouts: PayoutsInfo;
  security: SecurityInfo;
}

// =============================
// UI TYPES (OPTIONAL)
// =============================

export interface TabItem {
  id: ProfileTabId;
  label: string;
}

export interface QuickStatusCard {
  id: string;
  label: string;
  value: string;
  status: 'ok' | 'warning' | 'error';
}

export interface StickyAction {
  id: 'editProfile' | 'uploadDocument' | 'openPayouts' | 'openSecurity';
  label: string;
  style: ActionStyle;
}

// =============================
// COMPONENT PROPS (REACT READY)
// =============================

export interface ProfileHeaderProps {
  user: DriverProfileUser;
  professional: ProfessionalInfo;
  onEditAvatar?: () => void;
}

export interface ProfileTabsProps {
  items: TabItem[];
  activeTab: ProfileTabId;
  onChange: (tab: ProfileTabId) => void;
}

export interface DocumentsTabProps {
  documents: DriverDocument[];
  onUpload: () => void;
  onOpen: (id: string) => void;
  onReplace: (id: string) => void;
  onDelete: (id: string) => void;
}

export interface PayoutsTabProps {
  payouts: PayoutsInfo;
}

export interface SecurityTabProps {
  security: SecurityInfo;
  onToggle2FA: (enabled: boolean) => void;
}

export interface StickyActionBarProps {
  actions: StickyAction[];
  onActionClick: (actionId: StickyAction['id']) => void;
}
