export interface CapabilityActionState {
  allowed: boolean;
  reason?: string | null;
}

export interface CapabilityModuleState {
  available: boolean;
  reason?: string | null;
  actions: Record<string, CapabilityActionState>;
}

export interface CapabilityServiceHealth {
  key: string;
  label: string;
  available: boolean;
  reason?: string | null;
  raw_status?: string | null;
}

export interface CapabilitySnapshot {
  modules: Record<string, CapabilityModuleState>;
  services: Record<string, CapabilityServiceHealth>;
}
