import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { getCapabilitySnapshot } from '../api/system';
import type { CapabilityActionState, CapabilitySnapshot } from '../types';
import { subscribeTaskStream } from '../api/taskStream';

type CapabilityContextValue = {
  snapshot: CapabilitySnapshot | null;
  loading: boolean;
  refresh: () => Promise<void>;
  getActionCapability: (moduleKey: string, actionKey: string) => CapabilityActionState;
};

const defaultActionCapability: CapabilityActionState = {
  allowed: true,
  reason: null,
};

const CapabilityContext = createContext<CapabilityContextValue>({
  snapshot: null,
  loading: false,
  refresh: async () => undefined,
  getActionCapability: () => defaultActionCapability,
});

export const CapabilityProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [snapshot, setSnapshot] = useState<CapabilitySnapshot | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const next = await getCapabilitySnapshot();
      setSnapshot(next);
    } catch {
      setSnapshot(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const stop = subscribeTaskStream({
      onEvent: (payload) => {
        if (payload.event === 'capability_changed') {
          void refresh();
        }
      },
    });

    return () => {
      stop();
    };
  }, [refresh]);

  const getActionCapability = useCallback((moduleKey: string, actionKey: string): CapabilityActionState => {
    return snapshot?.modules?.[moduleKey]?.actions?.[actionKey] || defaultActionCapability;
  }, [snapshot]);

  const value = useMemo<CapabilityContextValue>(() => ({
    snapshot,
    loading,
    refresh,
    getActionCapability,
  }), [getActionCapability, loading, refresh, snapshot]);

  return (
    <CapabilityContext.Provider value={value}>
      {children}
    </CapabilityContext.Provider>
  );
};

export const useCapabilityContext = () => useContext(CapabilityContext);
