import { UNSAFE_createBrowserHistory as createBrowserHistory } from 'react-router-dom';
import { Modal } from 'antd';

const rawHistory = createBrowserHistory({ v5Compat: true });

type AppHistory = typeof rawHistory;
type HistoryListener = Parameters<AppHistory['listen']>[0];

const listeners = new Set<HistoryListener>();

let currentAction = rawHistory.action;
let currentLocation = rawHistory.location;
let suppressNextPop = false;
let activeGuard: { id: symbol; message: string } | null = null;
let pendingNavigation: Promise<boolean> | null = null;

function shouldAllowNavigationSync() {
  if (!activeGuard) return true;
  return false;
}

function askForNavigationConfirmation() {
  if (!activeGuard) {
    return Promise.resolve(true);
  }
  if (pendingNavigation) {
    return pendingNavigation;
  }

  pendingNavigation = new Promise<boolean>((resolve) => {
    Modal.confirm({
      title: '离开当前页面',
      content: activeGuard?.message,
      okText: '离开',
      cancelText: '继续编辑',
      centered: true,
      width: 460,
      okButtonProps: {
        danger: true,
      },
      styles: {
        body: {
          paddingTop: 8,
          paddingBottom: 4,
        },
      },
      onOk: () => {
        pendingNavigation = null;
        resolve(true);
      },
      onCancel: () => {
        pendingNavigation = null;
        resolve(false);
      },
      afterClose: () => {
        pendingNavigation = null;
      },
    });
  });

  return pendingNavigation;
}

rawHistory.listen((update) => {
  if (suppressNextPop) {
    suppressNextPop = false;
    return;
  }

  if (update.action === 'POP' && activeGuard) {
    const delta = typeof update.delta === 'number' ? update.delta : null;
    askForNavigationConfirmation().then((allowed) => {
      if (!allowed) {
        if (delta && delta !== 0) {
          suppressNextPop = true;
          rawHistory.go(-delta);
        }
        return;
      }
      currentAction = update.action;
      currentLocation = update.location;
      listeners.forEach((listener) => listener(update));
    });
    return;
  }

  currentAction = update.action;
  currentLocation = update.location;
  listeners.forEach((listener) => listener(update));
});

export const appHistory: AppHistory = {
  get action() {
    return currentAction;
  },
  get location() {
    return currentLocation;
  },
  createHref(to) {
    return rawHistory.createHref(to);
  },
  createURL(to) {
    return rawHistory.createURL(to);
  },
  encodeLocation(to) {
    return rawHistory.encodeLocation(to);
  },
  push(to, state) {
    if (!shouldAllowNavigationSync()) {
      void askForNavigationConfirmation().then((allowed) => {
        if (allowed) rawHistory.push(to, state);
      });
      return;
    }
    rawHistory.push(to, state);
  },
  replace(to, state) {
    if (!shouldAllowNavigationSync()) {
      void askForNavigationConfirmation().then((allowed) => {
        if (allowed) rawHistory.replace(to, state);
      });
      return;
    }
    rawHistory.replace(to, state);
  },
  go(delta) {
    if (!shouldAllowNavigationSync()) {
      void askForNavigationConfirmation().then((allowed) => {
        if (allowed) rawHistory.go(delta);
      });
      return;
    }
    rawHistory.go(delta);
  },
  listen(listener) {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },
};

export function setNavigationGuard(id: symbol, message: string) {
  activeGuard = { id, message };
}

export function clearNavigationGuard(id: symbol) {
  if (activeGuard?.id === id) {
    activeGuard = null;
  }
}
