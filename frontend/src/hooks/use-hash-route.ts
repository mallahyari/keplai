import { useSyncExternalStore } from "react";

function getHash() {
  return window.location.hash.slice(1) || "/";
}

function subscribe(cb: () => void) {
  window.addEventListener("hashchange", cb);
  return () => window.removeEventListener("hashchange", cb);
}

export function useHashRoute() {
  return useSyncExternalStore(subscribe, getHash);
}
