/// <reference types="vite/client" />

interface Window {
  __BETALEN_CONFIG__?: {
    supabaseUrl?: string;
    supabasePublishableKey?: string;
  };
}