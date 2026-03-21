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

export type BooleanStatusType = 'boolean_status';
export type ToggleType = 'toggle';

export type ProfileTabId =
  | 'overview'
  | 'taxi_ip'
  | 'documents'
  | 'payouts'
  | 'security';

export type ActionStyle = 'primary' | 'secondary' | 'ghost';

export interface DriverProfileScreenState {
  status: ScreenStatus;
  activeTab: ProfileTabId;
  isEditing: boolean;
  isMobile: boolean;
  error: string | null;
}

export interface DriverProfileScreenLayout {
  type: 'page';
  sections: Array<'header' | 'quickStatuses' | 'tabs' | 'content' | 'stickyActions'>;
}

export interface DriverProfileScreenMeta {
  id: 'driverProfile';
  title: string;
  role: 'taxi_driver';
  businessType: 'ip';
  taxMode: 'usn_income';
  layout: DriverProfileScreenLayout;
  state: DriverProfileScreenState;
}

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

export interface InsuranceItem {
  status: 'valid' | 'expiring' | 'expired';
  expiresAt: string;
}

export interface InsuranceInfo {
  osago: InsuranceItem;
  diagnosticCard: InsuranceItem;
}

export interface DriverDocument {
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

export interface DriverProfileData {
  user: DriverProfileUser;
  professional: ProfessionalInfo;
  insurance: InsuranceInfo;
  documents: DriverDocument[];
  payouts: PayoutsInfo;
  security: SecurityInfo;
}

export interface HeaderProps {
  showAvatar: boolean;
  showEditAvatar: boolean;
  titleField: string;
  subtitle: string[];
  statusField: string;
}

export interface QuickStatusCard {
  id: string;
  label: string;
  value: string;
  status: 'ok' | 'warning' | 'error';
}

export interface TabItem {
  id: ProfileTabId;
  label: string;
}

export interface InfoGridItem {
  label: string;
  value?: string | number;
  valueField?: string;
  suffix?: string;
}

export interface StatsCardItem {
  label: string;
  valueField: string;
  format?: 'currency_rub' | 'number' | 'text';
  emphasis?: 'highlight';
}

export interface DataCardBlock {
  component: 'DataCard';
  title: string;
  items: InfoGridItem[];
}

export interface InfoGridBlock {
  component: 'InfoGrid';
  items: InfoGridItem[];
}

export interface StatsCardsBlock {
  component: 'StatsCards';
  items: StatsCardItem[];
}

export interface EmptyStateConfig {
  title: string;
  action: string;
}

export interface OverviewTabView {
  component: 'OverviewTab';
  blocks: Array<InfoGridBlock | StatsCardsBlock>;
}

export interface TaxiIpTabView {
  component: 'TaxiIpTab';
  blocks: DataCardBlock[];
}

export interface DocumentsTabView {
  component: 'DocumentsTab';
  listField: string;
  itemComponent: 'DocumentItem';
  emptyState: EmptyStateConfig;
}

export interface PayoutHistoryListBlock {
  component: 'PayoutHistoryList';
  listField: string;
}

export interface PayoutsTabView {
  component: 'PayoutsTab';
  blocks: Array<DataCardBlock | StatsCardsBlock | PayoutHistoryListBlock>;
}

export interface SettingsListItem {
  id: string;
  label: string;
  valueField: string;
  type: BooleanStatusType | ToggleType;
}

export interface SettingsListBlock {
  component: 'SettingsList';
  items: SettingsListItem[];
}

export interface DevicesListBlock {
  component: 'DevicesList';
  listField: string;
}

export interface SecurityTabView {
  component: 'SecurityTab';
  blocks: Array<SettingsListBlock | DevicesListBlock>;
}

export interface TabContentViews {
  overview: OverviewTabView;
  taxi_ip: TaxiIpTabView;
  documents: DocumentsTabView;
  payouts: PayoutsTabView;
  security: SecurityTabView;
}

export interface TabContentRouter {
  component: 'TabContentRouter';
  views: TabContentViews;
}

export interface StickyAction {
  id: 'editProfile' | 'uploadDocument' | 'openPayouts' | 'openSecurity';
  label: string;
  style: ActionStyle;
}

export interface StickyActionsConfig {
  component: 'StickyActionBar';
  actions: StickyAction[];
}

export interface DriverProfileUI {
  header: {
    component: 'ProfileHeader';
    props: HeaderProps;
  };
  quickStatuses: {
    component: 'StatusCardsRow';
    items: QuickStatusCard[];
  };
  tabs: {
    component: 'ProfileTabs';
    items: TabItem[];
    activeTabField: string;
  };
  content: TabContentRouter;
  stickyActions: StickyActionsConfig;
}

export interface NavigateAction {
  type: 'navigate';
  target: string;
}

export interface ModalAction {
  type: 'modal';
  target: string;
}

export interface SetActiveTabAction {
  type: 'setActiveTab';
  target: ProfileTabId;
}

export interface FileUploadAction {
  type: 'fileUpload';
  target: 'avatar';
}

export interface ApiAction {
  type: 'api';
  method: 'PATCH' | 'POST' | 'GET';
  target: string;
}

export interface ConfirmThenApiAction {
  type: 'confirmThenApi';
  method: 'DELETE' | 'PATCH';
  target: string;
}

export interface DriverProfileActions {
  editProfile: NavigateAction;
  uploadDocument: ModalAction;
  openPayouts: SetActiveTabAction;
  openSecurity: SetActiveTabAction;
  changeAvatar: FileUploadAction;
  toggle2FA: ApiAction;
  deleteDocument: ConfirmThenApiAction;
}

export interface DriverProfileEnums {
  screenStatus: ScreenStatus[];
  profileStatus: ProfileStatus[];
  documentStatus: DocumentStatus[];
  licenseStatus: LicenseStatus[];
  payoutStatus: PayoutStatus[];
}

export interface DriverProfileScreenSchema {
  screen: DriverProfileScreenMeta;
  data: DriverProfileData;
  ui: DriverProfileUI;
  actions: DriverProfileActions;
  enums: DriverProfileEnums;
}

export interface ProfileHeaderProps {
  user: DriverProfileUser;
  professional: ProfessionalInfo;
  onEditAvatar?: () => void;
}

export interface StatusCardsRowProps {
  items: QuickStatusCard[];
}

export interface ProfileTabsProps {
  items: TabItem[];
  activeTab: ProfileTabId;
  onChange: (tab: ProfileTabId) => void;
}

export interface OverviewTabProps {
  user: DriverProfileUser;
  professional: ProfessionalInfo;
  payouts: PayoutsInfo;
}

export interface TaxiIpTabProps {
  professional: ProfessionalInfo;
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
  onChangePassword: () => void;
  onLogoutAll: () => void;
}

export interface StickyActionBarProps {
  actions: StickyAction[];
  onActionClick: (actionId: StickyAction['id']) => void;
}
