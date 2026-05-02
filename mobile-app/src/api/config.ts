import { Platform } from 'react-native';

declare const process: {
  env?: {
    EXPO_PUBLIC_SAFEBITE_API_URL?: string;
  };
};

const localApiUrl = Platform.select({
  android: 'http://10.0.2.2:8000',
  default: 'http://127.0.0.1:8000',
});

export const API_BASE_URL =
  process.env?.EXPO_PUBLIC_SAFEBITE_API_URL?.replace(/\/$/, '') ?? localApiUrl;
