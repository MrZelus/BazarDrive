/**
 * TypeScript model for `docs/driver_profile_screen.schema.json` and
 * the expanded payload sample shared by product/frontend.
 */

export type ISODate = string;
export type ISODateTime = string;
export type PhoneNumber = string;
export type Email = string;

export type ScreenStatus = 'loading' | 'loaded' | 'empty' | 'error';
export type ProfileStatus = 'active' | 'pending_verification' | 'blocked';
export type DocumentStatus =
  | 'uploaded'
  | 'checking'
  | 'approved'
  | 'rejected'
  | 'expired'
  | 'expiring_soon';
export type LicenseStatus = 'active' | 'expiring_soon' | 'expired' | 'missing';
export type PayoutStatus = 'connected' | 'pending' | 'disabled';

export type DriverRole = 'taxi_driver';
export type BusinessType = 'ip';
export type TaxMode = 'usn_income';

export type LayoutSection = 'header' | 'quickStatuses' | 'tabs' | 'content' | 'stickyActions';
export type PageLayoutType = 'page';

export type TabId = 'overview' | 'taxi_ip' | 'documents' | 'payouts' | 'security';

export type DriverLicenseValidationStatus = 'valid' | 'expiring_soon' | 'expired';
export type InsuranceStatus = 'valid' | 'expiring_soon' | 'expired';
export type QuickStatusState = 'ok' | 'warning' | 'error';

export type DocumentType =
  | 'passport'
  | 'inn'
  | 'ogrnip'
  | 'taxi_license'
  | 'driver_license'
  | 'sts'
  | 'osago'
  | 'diagnostic_card';

export type PayoutHistoryStatus = 'completed' | 'pending' | 'failed';

export type ComponentName =
  | 'ProfileHeader'
  | 'StatusCardsRow'
  | 'ProfileTabs'
  | 'TabContentRouter'
  | 'OverviewTab'
  | 'TaxiIpTab'
  | 'DocumentsTab'
  | 'DocumentItem'
  | 'PayoutsTab'
  | 'PayoutHistoryList'
  | 'SecurityTab'
  | 'SettingsList'
  | 'DevicesList'
  | 'StickyActionBar'
  | 'InfoGrid'
  | 'StatsCards'
  | 'DataCard';

export type ValueFormat = 'currency_rub';

export type ActionId =
  | 'editProfile'
  | 'uploadDocument'
  | 'openPayouts'
  | 'openSecurity'
  | 'changeAvatar'
  | 'toggle2FA'
  | 'deleteDocument';

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
  role: DriverRole;
  businessType: BusinessType;
  taxMode: TaxMode;
  layout: {
    type: PageLayoutType;
    sections: LayoutSection[];
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
  phone: PhoneNumber;
  email: Email;
  city: string;
  workZone: string;
  rating: number;
  tripsCompleted: number;
  profileStatus: ProfileStatus;
  registeredAt: ISODate;
}

export interface Professional {
  roleLabel: string;
  businessTypeLabel: string;
  taxModeLabel: string;
  taxRatePercent: number;
  inn: string;
  ogrnip: string;
  ipRegisteredAt: ISODate;
  license: {
    number: string;
    region: string;
    status: LicenseStatus;
    expiresAt: ISODate;
  };
  driverLicense: {
    number: string;
    status: DriverLicenseValidationStatus;
    expiresAt: ISODate;
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
  status: InsuranceStatus;
  expiresAt: ISODate;
}

export interface Document {
  id: string;
  type: DocumentType;
  title: string;
  uploadedAt: ISODate;
  expiresAt: ISODate | null;
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
  date: ISODate;
  amount: number;
  status: PayoutHistoryStatus;
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
  lastSeen: ISODateTime;
  current: boolean;
}

export interface DriverProfileUI {
  header: HeaderUI;
  quickStatuses: QuickStatusesUI;
  tabs: TabsUI;
  content: ContentUI;
  stickyActions: StickyActionsUI;
}

export interface HeaderUI {
  component: 'ProfileHeader';
  props: {
    showAvatar: boolean;
    showEditAvatar: boolean;
    titleField: 'data.user.fullName';
    subtitle: ['data.professional.roleLabel', 'data.professional.businessTypeLabel', 'data.professional.taxModeLabel'];
    statusField: 'data.user.profileStatus';
  };
}

export interface QuickStatusesUI {
  component: 'StatusCardsRow';
  items: QuickStatus[];
}

export interface QuickStatus {
  id: 'documents_status' | 'taxi_license_status' | 'payouts_status' | 'osago_status' | string;
  label: string;
  value: string;
  status: QuickStatusState;
}

export interface TabsUI {
  component: 'ProfileTabs';
  items: TabItem[];
  activeTabField: 'screen.state.activeTab';
}

export interface TabItem {
  id: TabId;
  label: string;
}

export interface ContentUI {
  component: 'TabContentRouter';
  views: {
    overview: OverviewTabView;
    taxi_ip: TaxiIpTabView;
    documents: DocumentsTabView;
    payouts: PayoutsTabView;
    security: SecurityTabView;
  };
}

export interface OverviewTabView {
  component: 'OverviewTab';
  blocks: [InfoGridBlock, StatsCardsBlock];
}

export interface TaxiIpTabView {
  component: 'TaxiIpTab';
  blocks: [DataCardBlock, DataCardBlock, DataCardBlock];
}

export interface DocumentsTabView {
  component: 'DocumentsTab';
  listField: 'data.documents';
  itemComponent: 'DocumentItem';
  emptyState: {
    title: string;
    action: 'uploadDocument';
  };
}

export interface PayoutsTabView {
  component: 'PayoutsTab';
  blocks: [DataCardBlock, StatsCardsBlock, PayoutHistoryListBlock];
}

export interface SecurityTabView {
  component: 'SecurityTab';
  blocks: [SettingsListBlock, DevicesListBlock];
}

export interface InfoGridBlock {
  component: 'InfoGrid';
  items: Array<
    | { label: string; valueField: string }
    | { label: string; value: string }
  >;
}

export interface StatsCardsBlock {
  component: 'StatsCards';
  items: Array<{
    label: string;
    valueField: string;
    format: ValueFormat;
    emphasis?: 'highlight';
  }>;
}

export interface DataCardBlock {
  component: 'DataCard';
  title: string;
  items: Array<{
    label: string;
    valueField: string;
    suffix?: '%';
  }>;
}

export interface PayoutHistoryListBlock {
  component: 'PayoutHistoryList';
  listField: 'data.payouts.history';
}

export interface SettingsListBlock {
  component: 'SettingsList';
  items: Array<{
    id: 'phoneVerified' | 'emailVerified' | 'twoFactorEnabled';
    label: string;
    valueField: string;
    type: 'boolean_status' | 'toggle';
  }>;
}

export interface DevicesListBlock {
  component: 'DevicesList';
  listField: 'data.security.activeDevices';
}

export interface StickyActionsUI {
  component: 'StickyActionBar';
  actions: StickyAction[];
}

export interface StickyAction {
  id: ActionId;
  label: string;
  style: 'primary' | 'secondary' | 'ghost';
}

export type ActionConfig =
  | NavigateAction
  | ModalAction
  | SetActiveTabAction
  | FileUploadAction
  | ApiAction
  | ConfirmThenApiAction;

export interface NavigateAction {
  type: 'navigate';
  target: '/profile/edit' | string;
}

export interface ModalAction {
  type: 'modal';
  target: 'documentUploader' | string;
}

export interface SetActiveTabAction {
  type: 'setActiveTab';
  target: Extract<TabId, 'payouts' | 'security'> | TabId;
}

export interface FileUploadAction {
  type: 'fileUpload';
  target: 'avatar';
}

export interface ApiAction {
  type: 'api';
  method: 'PATCH';
  target: '/api/profile/security/2fa' | string;
}

export interface ConfirmThenApiAction {
  type: 'confirmThenApi';
  method: 'DELETE';
  target: '/api/profile/documents/:id' | string;
}

export interface DriverProfileEnums {
  screenStatus: ScreenStatus[];
  profileStatus: ProfileStatus[];
  documentStatus: DocumentStatus[];
  licenseStatus: LicenseStatus[];
  payoutStatus: PayoutStatus[];
}
