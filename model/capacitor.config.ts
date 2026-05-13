import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  
  appId: 'com.laundryhub.app',
  appName: 'LaundryHub',
  webDir: 'dist',
  server: {
    cleartext: true, // Specifically tells Capacitor to allow HTTP
    androidScheme: 'http'
  }
};

export default config;
