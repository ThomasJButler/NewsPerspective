"use client";

import { useCallback, useSyncExternalStore } from "react";

const STORAGE_KEY = "newsperspective-api-key";
const STORAGE_EVENT = "newsperspective-api-key-change";

function subscribeToApiKey(onStoreChange: () => void) {
  if (typeof window === "undefined") {
    return () => {};
  }

  const handleStorage = (event: StorageEvent) => {
    if (event.key === null || event.key === STORAGE_KEY) {
      onStoreChange();
    }
  };

  window.addEventListener("storage", handleStorage);
  window.addEventListener(STORAGE_EVENT, onStoreChange);

  return () => {
    window.removeEventListener("storage", handleStorage);
    window.removeEventListener(STORAGE_EVENT, onStoreChange);
  };
}

function subscribeToHydration() {
  return () => {};
}

function getApiKeySnapshot(): string {
  if (typeof window === "undefined") {
    return "";
  }

  return localStorage.getItem(STORAGE_KEY) ?? "";
}

function emitApiKeyChange() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(STORAGE_EVENT));
  }
}

export function useApiKey() {
  const apiKey = useSyncExternalStore(
    subscribeToApiKey,
    getApiKeySnapshot,
    () => ""
  );
  const isLoaded = useSyncExternalStore(
    subscribeToHydration,
    () => true,
    () => false
  );

  const setApiKey = useCallback((key: string) => {
    localStorage.setItem(STORAGE_KEY, key);
    emitApiKeyChange();
  }, []);

  const clearApiKey = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    emitApiKeyChange();
  }, []);

  return {
    apiKey,
    setApiKey,
    clearApiKey,
    hasApiKey: isLoaded && apiKey.trim().length > 0,
    isLoaded,
  };
}
